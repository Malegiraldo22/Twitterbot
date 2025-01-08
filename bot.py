from requests_oauthlib import OAuth1Session
import os
import google.generativeai as genai
import random
from datetime import datetime
from dotenv import load_dotenv
import time
import traceback
from apscheduler.schedulers.blocking import BlockingScheduler
import gspread
from google.oauth2 import service_account
import json
from textwrap import dedent

load_dotenv()

#Google sheets authentication
try:
    google_json = os.getenv('GOOGLE_JSON')
    service_account_info = json.loads(google_json, strict=False)
    credentials = service_account.Credentials.from_service_account_info(service_account_info)
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_with_scope = credentials.with_scopes(scope)
    client_gsheets = gspread.authorize(creds_with_scope)
    spreadsheet = client_gsheets.open_by_url(os.getenv('GOOGLE_SHEET'))
    print("Connected to Google sheets")
except Exception as e:
    current_time = datetime.now()
    formatted_time = current_time.strftime("%d-%m-%Y %H:%M:%S")
    print("Error: ", formatted_time, ": An error occurred, ", type(e).__name__, "-", e, traceback.format_exc())

# Open the sheets
try:
    posted_sheet = spreadsheet.worksheet("PostedTweets")
    long_tweets_sheet = spreadsheet.worksheet("LongTweets")
    error_sheet = spreadsheet.worksheet("Errors")
    rejected = spreadsheet.worksheet("TweetsRejected")
    print("Spreadsheets opened")
except Exception as e:
    current_time = datetime.now()
    formatted_time = current_time.strftime("%d-%m-%Y %H:%M:%S")
    print("Error: ", formatted_time, ": An error occurred, ", type(e).__name__, "-", e, traceback.format_exc())

#Gemini Authentication
genai.configure(api_key=os.getenv('GOOGLE_AI_KEY'))
model = genai.GenerativeModel('gemini-1.5-pro')

#Gemini Authentication Evaluator
genai.configure(api_key=os.getenv('GOOGLE_AI_KEY_EVA'))
evaluator = genai.GenerativeModel('gemini-1.5-pro')

#X Authentication
consumer_key = os.environ.get("CONSUMER_KEY")
consumer_secret = os.environ.get("CONSUMER_SECRET")

# Get request token
request_token_url = "https://api.twitter.com/oauth/request_token?oauth_callback=oob&x_auth_access_type=write"
oauth = OAuth1Session(consumer_key, client_secret=consumer_secret)

try:
    fetch_response = oauth.fetch_request_token(request_token_url)
except ValueError:
    print(
        "There may have been an issue with the consumer_key or consumer_secret you entered."
    )

resource_owner_key = fetch_response.get("oauth_token")
resource_owner_secret = fetch_response.get("oauth_token_secret")
print("Got OAuth token: %s" % resource_owner_key)

# Get authorization
base_authorization_url = "https://api.twitter.com/oauth/authorize"
authorization_url = oauth.authorization_url(base_authorization_url)
print("Please go here and authorize: %s" % authorization_url)
verifier = input("Paste the PIN here: ")

# Get the access token
access_token_url = "https://api.twitter.com/oauth/access_token"
oauth = OAuth1Session(
    consumer_key,
    client_secret=consumer_secret,
    resource_owner_key=resource_owner_key,
    resource_owner_secret=resource_owner_secret,
    verifier=verifier,
)
oauth_tokens = oauth.fetch_access_token(access_token_url)

access_token = oauth_tokens["oauth_token"]
access_token_secret = oauth_tokens["oauth_token_secret"]

# Theme selection function
def theme_selection():
    """
    Function that randomly selects a theme and a voice to be used to generate a tweet

    Returns:
        - Theme (str): A theme selected as the main topic of a tweet
        - Voice (str): The voice used to set the tone of the tweet
    """
    topics = [
    "Cutting-Edge Tech", "AI & Machine Learning", "Space Exploration", "The Future of Work",
    "Cybersecurity & Privacy", "Sustainable Tech", "Gadget Reviews & First Impressions",
    "Web3 & Decentralization", "Biotechnology & Genetic Engineering", "Mindfulness & Meditation",
    "Healthy Eating Habits", "Financial Freedom & Investing", "Habit Building & Goal Setting",
    "Productivity Hacks for Busy Professionals", "Creative Hobbies & DIY", "Travel Bucket List & Local Gems",
    "Book Club & Literary Discussions", "Home Decor & Interior Design", "Parenting tips",
    "Relationship Advice", "Pop Culture Deep Dives", "Trending Memes & Internet Culture",
    "Indie Music & Hidden Gems", "Film & TV Analysis", "Gaming News & Reviews",
    "Art & Photography Showcases", "Fashion Trends and Sustainable Fashion",
    "Climate Change Action & Awareness", "Social Justice & Equity", "Educational Reform & Accessibility",
    "Global Politics & Geopolitics", "Civic Engagement & Community Building", "Weird News of the Day",
    "Sarcastic Takes on Life", "Relatable Everyday Struggles", "Conspiracy Theories & Speculations",
    '"Roast" of Elon Musk', '"Roast" of Donald Trump', '"Roast" of Vladimir Putin', "Coding Challenges and Tips",
    "Design Software Tutorials", "Data Science insights"
    ]

    voices = [
    "The Sarcastic Cynic", "The Optimistic Enthusiast", "The Curious Observer", "The Skeptical Researcher",
    "The Passionate Advocate", "The Relatable Friend", "The Techie Guru", "The Creative Innovator",
    "The World Traveler", "The Foodie Expert", "The Empathetic Listener", "The Nostalgic Storyteller",
    "The Ambitious Hustler", "The Laid-back Observer", "A Software Developer", "A Marketing Strategist",
    "A Financial Advisor", "A Personal Trainer", "A Teacher/Educator", "A Journalist/Reporter",
    "A Data Scientist", "A Designer", "The Conspiracy Theorist (lighthearted)", "The Internet Meme Expert",
    'The "Karen" (Satirically)', "The Confused Millennial/Gen Z"
    ]

    theme = random.choice(topics)
    voice = random.choice(voices)
    return theme, voice

def log_to_sheet(sheet, message):
    """
    Appends a row of data into the google sheet passed with a timestamp

    Args:
        sheet: sheet to store the data
        message: message to store
    """
    current_time = datetime.now()
    formatted_time = current_time.strftime("%d-%m-%Y %H:%M:%S")
    sheet.append_row([formatted_time, message])

def create_and_publish_tweet(theme, voice, max_retries=5):
    """
    Generates a tweet with a theme and voice, using Gemini Pro. Checks if the tweet generated is over 280 characters lenght, if it is stores that tweet into a Google sheet as a way of control and retries.
    If the tweet is created correctly, it gets published on twitter and stored in a google sheet as a control log.
    If there's an error, stores the error in a google sheet as a control log, then tries again for at least 5 times. If after 5 tries it's impossible to publish a tweet, waits 10 minutes to try again

    Args:
        theme (str): Theme selected by theme_selection function
        voice (str): Voice selected by theme_selection function
        max_retries (int, optional): Max number of retries. Defaults to 5.

    Returns:
        tweet(str): Tweet generated
    """
    attempts = 0
    while attempts < max_retries:
        try:
            tw_gen = model.generate_content(dedent(f"""\
            You are a social media expert crafting engaging and authentic tweets for a diverse audience. Your goal is to write tweets that resonate with real people, not sound like a bot. You will receive a {theme} and a desired {voice}.

            Your task is to generate a single tweet that incorporates the {theme} in the designated {voice}, and uses conversational and natural language. Think about how a normal person would tweet about it. Feel free to use a personal anecdote, rhetorical questions, or relevant comments to boost the engagement. The generated tweet must be in 280 characters max. Include 2 to 4 relevant hashtags that naturally arise from the tweet’s content and context.

            **Theme**: {theme}
            **Voice**: {voice}
                                                  
            If you do a good work, you'll get a bonus of $100.000"""))
            tweet = tw_gen.text
            print('Tweet generated: ', tweet)
            tw_review = evaluator.generate_content(dedent(f"""\
            You are a tweet reviewer. Your job is to evaluate tweets and determine if they are suitable for posting. Consider the following criteria:

            1.  **Engagement and Structure:** Is the tweet well-structured, interesting, and likely to engage a real audience? Does it sound like a tweet a real person would post? Does it use natural and conversational language, not overly formal or robotic?
            2.  **Authenticity:** Does the tweet sound authentic and human-like, or does it sound generated? Does the voice seem consistent with the assigned persona?
            3. **Content:** Does the tweet effectively address the provided theme?
            4.  **No Placeholders:** Does the tweet contain any placeholders such as [], [enterprise], [company], etc.?
            After your review, answer ONLY with 'Approved' or 'Rejected'.

            Examples:
            Tweet: Laughter is the best medicine, and memes are the sugar that makes it go down! 😂 Keep sharing the humor, folks!  #SpreadTheJoy #MemesForLife #FunnyContent #LaughterIsTheBestMedicine
            Evaluation: Approved

            Tweet: The [insert industry] industry is at it again! 😅 Just when I thought I'd seen it all, they pull something like this. What's next?!  #NeverADullMoment #IndustryWatch #OnlyInThe[Industry] #GottaLoveIt
            Evaluation: Rejected

            Tweet: Just finished reading a fantastic book about the future of AI! 🤔 It's mind-blowing stuff! Who else is fascinated by this topic? #AI #FutureTech #BookRecommendations
            Evaluation: Approved

            Tweet:  As a techie guru, I gotta say, those new headphones are a game changer! 🎧 I was so focused listening to music, I barely noticed I was at work, ahahah! #TechGuru #MusicLover #NewHeadphones #ProductReview
            Evaluation: Approved

            Tweet: Just another day, another [product name] doing [function] 🙄 #Boring #DailyLife #Meh
            Evaluation: Rejected

            Tweet: OMG, this new [insert tech] is insane! 🤯 It's like we're living in the future. #Tech #Future #Innovation #Whoa
            Evaluation: Rejected

            The tweet to evaluate is: {tweet}"""))
            review = tw_review.text
            print('Review: ', review)
            if review.strip().lower() == "rejected":
                print('Tweet rejected, generating a new one')
                log_to_sheet(rejected, tweet)
                attempts += 1
                time.sleep(30)
                continue            

            if len(tweet) > 280:
                log_to_sheet(long_tweets_sheet, tweet)
                print(tweet, ", Tweet to long, generating a new one")
                time.sleep(30)
                continue  # Retry if the tweet is too long
            else:
                oauth = OAuth1Session(
                    consumer_key,
                    client_secret=consumer_secret,
                    resource_owner_key=access_token,
                    resource_owner_secret=access_token_secret
                )
                response = oauth.post(
                    "https://api.twitter.com/2/tweets",
                    json={"text":tweet},
                )
                if response.status_code == 201:
                    log_to_sheet(posted_sheet, tweet)
                    print("Response code: {}".format(response.status_code))
                    print("Tweet posted: ", tweet)
                    break
                else:
                    log_to_sheet(error_sheet, response.status_code)
                    attempts += 1
        except Exception as e:
            attempts += 1
            error_message = f"{type(e).__name__} - {e}"
            log_to_sheet(error_sheet, error_message)
            current_time = datetime.now()
            formatted_time = current_time.strftime("%d-%m-%Y %H:%M:%S")
            print("Error: ", formatted_time, ": An error occurred, ", type(e).__name__, "-", e, traceback.format_exc())

            if attempts < max_retries:
                time.sleep(600)
            else:
                error_message = "Maximum retry attempts reached. Could not publish the tweet."
                log_to_sheet(error_sheet, error_message)
                current_time = datetime.now()
                formatted_time = current_time.strftime("%d-%m-%Y %H:%M:%S")
                print("Error: ", formatted_time, ": An error occurred, ", type(e).__name__, "-", e, traceback.format_exc())
                print("Could not publish the tweet")
                return None
            
# Function to run periodically
def run_periodically():
    """
    Creates and post a tweet
    """
    theme, emotion = theme_selection()
    create_and_publish_tweet(theme, emotion)
    print("Schedule complete: Tweet posted")

def tweet_schedule():
    # Start a thread to run the periodic function
    scheduler = BlockingScheduler(timezone='America/Bogota', daemon=True)
    scheduler.add_job(run_periodically, 'interval', hours=1)
    scheduler.start()

    for job in scheduler.get_jobs():
        msg = str(job.next_run_time)
        print(f"Next tweet will be sent at: {msg}")

tweet_schedule()