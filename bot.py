# import libraries
import os
import google.generativeai as genai
import random
from datetime import datetime, timedelta
import streamlit as st
from dotenv import load_dotenv
import time
import tweepy
import traceback
from apscheduler.schedulers.background import BackgroundScheduler
import pytz

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

# Authenticating with Tweepy using a bearer token
def authenticate():
    try:
        client = tweepy.Client(
            consumer_key=os.getenv('CONSUMER_KEY'),
            consumer_secret=os.getenv('CONSUMER_SECRET'),
            access_token=os.getenv('ACCESS_TOKEN'),
            access_token_secret=os.getenv('ACCESS_SECRET')
        )
    except Exception as e:
        current_time = datetime.now()
        formated_time = current_time.strftime("%d-%m-%Y %H:%M:%S")
        print("Error: ", formated_time, ": An error occurred, ", type(e).__name__, "-", e, traceback.format_exc())
    return client

# Gemini authentication
genai.configure(api_key=os.getenv('GOOGLE_AI_KEY'))
model = genai.GenerativeModel('gemini-pro')

# Theme selection function
def theme_selection():
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

def create_and_publish_tweet(theme, emotion, max_retries=5):
    attempts = 0
    while attempts < max_retries:
        try:
            response = model.generate_content(f'Write a 280 character tweet about {theme} with a {emotion} tone including 4 hashtags')
            tweet = response.text
            current_time = datetime.now()
            formatted_time = current_time.strftime("%d-%m-%Y %H:%M:%S")
            user.create_tweet(text=tweet)
            return tweet
        except Exception as e:
            attempts += 1
            current_time = datetime.now()
            formatted_time = current_time.strftime("%d-%m-%Y %H:%M:%S")
            st.write(f"{formatted_time}: An error occurred: {type(e).__name__} - {e}, {traceback.format_exc()}")
            print(f"{formatted_time}: An error occurred: {type(e).__name__} - {e}, {traceback.format_exc()}")
            st.write("---")
            print("---")
            if attempts < max_retries:
                time.sleep(120)
            else:
                st.write(f"{formatted_time}: Maximum retry attempts reached. Could not publish the tweet.")
                print(f"{formatted_time}: Maximum retry attempts reached. Could not publish the tweet.")
                return None

def display_initial_tweet():
    theme, emotion = theme_selection()
    tweet = create_and_publish_tweet(theme, emotion)
    current_time = datetime.now()
    formated_time = current_time.strftime("%d-%m-%Y %H:%M:%S")

    if tweet:
        st.write(f"Time posted: {formated_time}")
        st.write(f"Tweet posted: {tweet}")
        st.write("---")
        print(f"{formated_time}: Tweet posted correcty")
        print("----")
    else:
        st.write(f"Time: {formated_time}")
        st.write("Tweet not posted due to errors.")
        st.write("---")  # Adding a separator for readability
        print(f"{formated_time}: Tweet not posted due to errors")
        print("----")

#Call authenticate function
user = authenticate()
# Call the function to display the initial tweet
display_initial_tweet()

# Create a placeholder to update content
display_area = st.empty()

# List to store the history of messages
message_history = []

# Function to run periodically every hour
def run_periodically():
    while True:
        theme, emotion = theme_selection()
        tweet = create_and_publish_tweet(theme, emotion)

        current_time = datetime.now()
        formatted_time = current_time.strftime("%d-%m-%Y %H:%M:%S")

        if tweet:
            message = f"Time posted: {formatted_time}\nTweet posted: {tweet}\n---"
        else:
            message = f"Time: {formatted_time}\nTweet not posted due to errors.\n---"

        message_history.append(message)
        display_area.markdown("\n\n".join(message_history))

        # Displaying the next tweet schedule time
        next_run_time = datetime.now() + timedelta(hours=1)
        next_run_time_formatted = next_run_time.strftime("%d-%m-%Y %H:%M:%S")
        message_history.append(f"Next tweet will be sent at: {next_run_time_formatted}\n---")

        # Sleep for 1 hour
        time.sleep(3600)

# Start a thread to run the periodic function
scheduler = BackgroundScheduler(timezone='America/Bogota', daemon=True)
scheduler.add_job(run_periodically, 'interval', minutes=60)
scheduler.start()
for job in scheduler.get_jobs():
    st.write("Next tweet will be sent at: ", job.next_run_time)
    print("Next tweet will be sent at: ", job.next_run_time)