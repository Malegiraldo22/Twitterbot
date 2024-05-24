# import libraries
import json
import os
import google.generativeai as genai
import random
from datetime import datetime
import streamlit as st
from dotenv import load_dotenv
import time
import tweepy
import traceback
from apscheduler.schedulers.background import BackgroundScheduler
import gspread
from google.oauth2 import service_account
import pandas as pd

# Load environment variables
load_dotenv()

# Streamlit page configuration
st.set_page_config(
    page_title='Twitter Bot Control Page',
    layout='wide'
)

# Title
st.title("Twitter Bot Control Page")
st.write("---")
logs = st.empty()


# Authenticating with Tweepy
try:
    client = tweepy.Client(
        consumer_key=os.getenv('CONSUMER_KEY'),
        consumer_secret=os.getenv('CONSUMER_SECRET'),
        access_token=os.getenv('ACCESS_TOKEN'),
        access_token_secret=os.getenv('ACCESS_SECRET')
    )
    print("Authenticated")
    logs.write("Authenticated correctly to Twitter")
except Exception as e:
    current_time = datetime.now()
    formatted_time = current_time.strftime("%d-%m-%Y %H:%M:%S")
    print("Error: ", formatted_time, ": An error occurred, ", type(e).__name__, "-", e, traceback.format_exc())

# Google Sheets authentication
try:
    google_json = os.getenv('GOOGLE_JSON')
    service_account_info = json.loads(google_json, strict=False)
    credentials = service_account.Credentials.from_service_account_info(service_account_info)
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_with_scope = credentials.with_scopes(scope)
    client_gsheets = gspread.authorize(creds_with_scope)
    spreadsheet = client_gsheets.open_by_url(os.getenv('GOOGLE_SHEET'))
    print("Connected to Google sheets")
    logs.write("Connected to Google Sheets")
except Exception as e:
    current_time = datetime.now()
    formatted_time = current_time.strftime("%d-%m-%Y %H:%M:%S")
    print("Error: ", formatted_time, ": An error occurred, ", type(e).__name__, "-", e, traceback.format_exc())


# Open the sheets
try:
    posted_sheet = spreadsheet.worksheet("PostedTweets")
    long_tweets_sheet = spreadsheet.worksheet("LongTweets")
    error_sheet = spreadsheet.worksheet("Errors")
    print("Spreadsheets opened")
    logs.write("Spreadsheets opened")
except Exception as e:
    current_time = datetime.now()
    formatted_time = current_time.strftime("%d-%m-%Y %H:%M:%S")
    print("Error: ", formatted_time, ": An error occurred, ", type(e).__name__, "-", e, traceback.format_exc())


# Function to check Google Sheets for updates
def check_sheet_updates():
    """
    Checks if the sheets have been updated

    Returns:
        sheets with all its values
    """
    posted_rows = posted_sheet.get_all_values()
    long_tweets_rows = long_tweets_sheet.get_all_values()
    error_rows = error_sheet.get_all_values()
    return posted_rows, long_tweets_rows, error_rows

# Create a placeholder to update content
next_tweet_area = st.empty()
next_tweet_area_msg = st.empty()
ui_update_schedule = st.empty()
ui_update_schedule_msg = st.empty()
posted_tweets_area = st.empty()
long_tweets_area = st.empty()
errors_area = st.empty()

# Fetch updated data from sheets and update UI
posted_rows, long_tweets_rows, error_rows = check_sheet_updates()
posted_df = pd.DataFrame(posted_rows, columns=['Timestamp', 'Tweet'])
long_tweets_df = pd.DataFrame(long_tweets_rows, columns=['Timestamp', 'Tweet'])
error_df = pd.DataFrame(error_rows, columns=['Timestamp', 'Error'])

with next_tweet_area.container():
    st.write("## Next tweet shedule")

with ui_update_schedule.container():
    st.write("## Next UI update schedule")

with posted_tweets_area.container():
    st.write("## Tweets Generated")
    st.dataframe(posted_df)

with long_tweets_area.container():
    st.write("## Long Tweets Generated")
    st.dataframe(long_tweets_df)
        
with errors_area.container():
    st.write("## Errors")
    st.dataframe(error_df)

# Gemini authentication
genai.configure(api_key=os.getenv('GOOGLE_AI_KEY'))
model = genai.GenerativeModel('gemini-pro')

# Theme selection function
def theme_selection():
    """
    Function that randomly selects a theme and a emotion to be used to generate a tweet

    Returns:
        - Theme (str): A theme selected as the main topic of a tweet
        - Emotion (str): The emotion to set the tone of the tweet
    """
    topics = [
        "Technology and Innovation", "Productivity Tips", "Health and Wellness", "Personal Finance",
        "Personal Development", "Entrepreneurship", "Industry News", "Pop Culture and Entertainment",
        "Travel and Adventures", "Cooking and Recipes", "Sports and Fitness", "Inspirational Quotes",
        "Memes and Humorous Content", "Ecology and Sustainability", "Education and Learning",
        "Books and Reading Recommendations", "Science and Discoveries", "Photography and Art",
        "Opinions and Debates", "Technology in Everyday Life", "Digital Marketing and Social Media",
        "Personal Stories and Anecdotes", "Psychology and Mental Health", "Fashion and Style",
        "Global News and Events", "Technical Skills Development (coding, design, etc.)",
        "DIY Projects and Crafts", "Gaming and E-sports", "Music and Music Recommendations", "Product Reviews"
    ]

    emotions = [
        "happy", "sad", "excited", "angry", "surprised", "curious", "inspired", "nostalgic", "motivated", "amused"
    ]

    theme = random.choice(topics)
    emotion = random.choice(emotions)
    return theme, emotion

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

def create_and_publish_tweet(theme, emotion, max_retries=5):
    """
    Generates a tweet with a theme and emotion, using Gemini 1.0 Pro. Checks if the tweet generated is over 280 characters lenght, if it is stores that tweet into a Google sheet as a way of control and retries.
    If the tweet is created correctly, it gets published on twitter and stored in a google sheet as a control log.
    If there's an error, stores the error in a google sheet as a control log, then tries again for at least 5 times. If after 5 tries it's impossible to publish a tweet, waits 10 minutes to try again

    Args:
        theme (str): Theme selected by theme_selection function
        emotion (str): Emotion selected by theme_selection function
        max_retries (int, optional): Max number of retries. Defaults to 5.

    Returns:
        tweet(str): Tweet generated
    """
    attempts = 0
    while attempts < max_retries:
        try:
            response = model.generate_content(f'Write a 280 character tweet about {theme} with a {emotion} tone including 4 hashtags')
            tweet = response.text
            logs.write("Tweet created")
            print("Tweet created")
            if len(tweet) > 280:
                log_to_sheet(long_tweets_sheet, tweet)
                logs.write("Tweet to long, generating a new one")
                print("Tweet to long, generating a new one")
                time.sleep(30)
                continue  # Retry if the tweet is too long
            
            client.create_tweet(text=tweet)
            logs.write("Tweet posted")
            print("Tweet posted")
            
            # Log to Google Sheets
            log_to_sheet(posted_sheet, tweet)
            
            return tweet
        except Exception as e:
            attempts += 1
            error_message = f"{type(e).__name__} - {e}"
            log_to_sheet(error_sheet, error_message)
            logs.write("Found an error, please check error logs")
            print("Found an error, please check error logs")

            if attempts < max_retries:
                time.sleep(600)
            else:
                error_message = "Maximum retry attempts reached. Could not publish the tweet."
                log_to_sheet(error_sheet, error_message)
                logs.write("Could not publish the tweet, check Error logs")
                print("Could not publish the tweet, check Error logs")
                return None


# Function to run periodically
def run_periodically():
    """
    Creates and post a tweet periodically every hour. Updates the logs and shows them
    """
    while True:
        theme, emotion = theme_selection()
        create_and_publish_tweet(theme, emotion)
        logs.write("Schedule complete: Tweet posted")
        print("Schedule complete: Tweet posted")

        with posted_tweets_area.container():
            st.write("## Tweets Generated")
            st.dataframe(posted_df)

        with long_tweets_area.container():
            st.write("## Long Tweets Generated")
            st.dataframe(long_tweets_df)
        
        with errors_area.container():
            st.write("## Errors")
            st.dataframe(error_df)

        # Sleep for 1 hour
        time.sleep(3600)

def tweet_schedule():
    # Start a thread to run the periodic function
    scheduler = BackgroundScheduler(timezone='America/Bogota', daemon=True)
    scheduler.add_job(run_periodically, 'interval', hours=1)
    scheduler.start()

    for job in scheduler.get_jobs():
        msg = str(job.next_run_time)
        next_tweet_area_msg.write(f"Next tweet will be sent at: {msg}")
        print(f"Next tweet will be sent at: {msg}")
        with next_tweet_area_msg.container():
            st.write(f"Next tweet will be sent at: {job.next_run_time}")

# Periodically check Google Sheets for updates and refresh UI
def refresh_ui():
    """
    Refresh the UI to show the updated data
    """
    posted_rows, long_tweets_rows, error_rows = check_sheet_updates()
    posted_df = pd.DataFrame(posted_rows)
    long_tweets_df = pd.DataFrame(long_tweets_rows)
    error_df = pd.DataFrame(error_rows)

    with posted_tweets_area.container():
        st.dataframe(posted_df)

    with long_tweets_area.container():
        st.dataframe(long_tweets_df)
        
    with errors_area.container():
        st.dataframe(error_df)
    
    logs.write('UI updated')
    st.experimental_rerun()
    

def ui_schedule():
    # Set a scheduler to refresh the UI every minute to check for updates
    ui_scheduler = BackgroundScheduler(timezone='America/Bogota', daemon=True)
    ui_scheduler.add_job(refresh_ui, 'interval', minutes=60)
    ui_scheduler.start()
    for job in ui_scheduler.get_jobs():
        msg = str(job.next_run_time)
        ui_update_schedule_msg.write(f"UI will update at: {msg}")
        print(f"UI will update at: {msg}")
        with ui_update_schedule_msg.container():
            st.write(f"UI will update at: {job.next_run_time}")

# Calling publish initial tweet
tweet_schedule()
ui_schedule()