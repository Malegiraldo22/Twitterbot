from requests_oauthlib import OAuth1Session
import os
import json
import google.generativeai as genai
import random
from datetime import datetime
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
import time
import threading
import pickle  # For persistent storage

# Load environment variables from .env file
load_dotenv()

# Check if environment variables are loaded correctly
consumer_key = os.getenv("CONSUMER_KEY")
consumer_secret = os.getenv("CONSUMER_SECRET")
google_ai_key = os.getenv("GOOGLE_AI_KEY")

if not consumer_key or not consumer_secret or not google_ai_key:
    st.error("One or more environment variables are missing. Please check your .env file.")
    st.stop()

# Streamlit page configuration
st.set_page_config(
    page_title='Twitter Bot Control Page',
    layout='wide'
)

# Title
st.title("Twitter Bot Control Page")

# Path to store OAuth tokens persistently
token_file_path = "twitter_oauth_tokens.pkl"

# Function to save tokens to a file
def save_tokens(tokens):
    with open(token_file_path, 'wb') as f:
        pickle.dump(tokens, f)

# Function to load tokens from a file
def load_tokens():
    if os.path.exists(token_file_path):
        with open(token_file_path, 'rb') as f:
            return pickle.load(f)
    return None

# Load tokens if they exist
oauth_tokens = load_tokens()

if oauth_tokens:
    st.session_state.oauth_tokens = oauth_tokens

if "oauth_tokens" not in st.session_state:
    st.session_state.oauth_tokens = None

# Get request token
request_token_url = "https://api.twitter.com/oauth/request_token?oauth_callback=oob&x_auth_access_type=write"
oauth = OAuth1Session(consumer_key, client_secret=consumer_secret)

if st.session_state.oauth_tokens is None:
    try:
        fetch_response = oauth.fetch_request_token(request_token_url)
        st.session_state.oauth_tokens = fetch_response
        save_tokens(fetch_response)  # Save tokens persistently
    except Exception as e:
        st.error(f"Error fetching request token: {e}")
        st.stop()

resource_owner_key = st.session_state.oauth_tokens.get("oauth_token")
resource_owner_secret = st.session_state.oauth_tokens.get("oauth_token_secret")

# Authorization URL
base_authorization_url = "https://api.twitter.com/oauth/authorize"
authorization_url = oauth.authorization_url(base_authorization_url)

# Create placeholders for authorization URL and PIN input
auth_url_placeholder = st.empty()
pin_input_placeholder = st.empty()

# Display authorization URL
auth_url_placeholder.write("Please go to the following URL and authorize the app:")
auth_url_placeholder.write(authorization_url)

# Input PIN
pin = pin_input_placeholder.text_input("Enter the PIN provided by Twitter:", "")

if pin:
    try:
        # Get access token
        access_token_url = "https://api.twitter.com/oauth/access_token"
        oauth = OAuth1Session(
            consumer_key,
            client_secret=consumer_secret,
            resource_owner_key=resource_owner_key,
            resource_owner_secret=resource_owner_secret,
            verifier=pin,
        )
        oauth_tokens = oauth.fetch_access_token(access_token_url)
        st.session_state.oauth_tokens = oauth_tokens
        save_tokens(oauth_tokens)  # Save tokens persistently

        # Clear placeholders
        auth_url_placeholder.empty()
        pin_input_placeholder.empty()

        # Inform user about successful authentication
        st.write("Authentication successful!")
        st.write("You can now use the Twitter API.")
    except Exception as e:
        st.error(f"Error fetching access token: {e}")
        st.stop()

# Gemini authentication
genai.configure(api_key=google_ai_key)
model = genai.GenerativeModel('gemini-1.5-pro-latest')

# Theme selection function
def theme_selection():
    """
    Function that randomly chooses a topic from a list and an emotion

    Returns:
        Theme (str): Theme to be used in the AI prompt to generate a tweet
    """
    topics = [
        "Technology and Innovation",
        "Productivity Tips",
        "Health and Wellness",
        "Personal Finance",
        "Personal Development",
        "Entrepreneurship",
        "Industry News",
        "Pop Culture and Entertainment",
        "Travel and Adventures",
        "Cooking and Recipes",
        "Sports and Fitness",
        "Inspirational Quotes",
        "Memes and Humorous Content",
        "Ecology and Sustainability",
        "Education and Learning",
        "Books and Reading Recommendations",
        "Science and Discoveries",
        "Photography and Art",
        "Opinions and Debates",
        "Technology in Everyday Life",
        "Digital Marketing and Social Media",
        "Personal Stories and Anecdotes",
        "Psychology and Mental Health",
        "Fashion and Style",
        "Global News and Events",
        "Technical Skills Development (coding, design, etc.)",
        "DIY Projects and Crafts",
        "Gaming and E-sports",
        "Music and Music Recommendations",
        "Product Reviews"
    ]

    emotions = [
        "happy",
        "sad",
        "excited",
        "angry",
        "surprised",
        "curious",
        "inspired",
        "nostalgic",
        "motivated",
        "amused"
    ]

    theme = random.choice(topics)
    emotion = random.choice(emotions)
    return theme, emotion

def create_and_publish_tweet(theme, emotion):
    """
    Function that creates a tweet from a list of themes using gemini-pro API and uses Twitter API to publish it

    Raises:
        Exception: returns an error message with status code and error type

    Returns:
        response_code (int): Status code number
        response_print(json): json containing tweet info
    """
    response = model.generate_content(f'Write a 280 character tweet about {theme} with a {emotion} tone including 4 hashtags')
    payload = {"text": response.text}
    # Making the request
    response = oauth.post(
        "https://api.twitter.com/2/tweets",
        json=payload,
    )

    if response.status_code != 201:
        raise Exception(
            "Request returned an error: {} {}".format(response.status_code, response.text)
        )

    response_code = "Response code: {}".format(response.status_code)

    # Saving the response as JSON
    json_response = response.json()
    response_print = json.dumps(json_response, indent=4, sort_keys=True)

    return response_code, response_print

# Function to generate and display the initial tweet
def display_initial_tweet():
    theme = theme_selection()
    response_code, response_print = create_and_publish_tweet(theme)
    current_time = datetime.now()
    formatted_time = current_time.strftime("%d-%m-%Y %H:%M:%S")
    parsed_data = json.loads(response_print)
    tweet = parsed_data['data']['text']
    st.write("---")
    st.write(f"Time posted: {formatted_time}")
    st.write(f"Tweet posted: {tweet}")
    st.write("---")  # Adding a separator for readability

# Call the function to display the initial tweet
display_initial_tweet()

# Function to run periodically every hour
def run_periodically():
    while True:
        # Call your functions here
        theme = theme_selection()
        response_code, response_print = create_and_publish_tweet(theme)

        #Saving tweets in the DataFrame
        current_time = datetime.now()
        formatted_time = current_time.strftime("%d-%m-%Y %H:%M:%S")
        parsed_data = json.loads(response_print)
        tweet = parsed_data['data']['text']

        # Display the tweet and its timestamp in the Streamlit app
        st.write(f"Time posted: {formatted_time}")
        st.write(f"Tweet posted: {tweet}")
        st.write("---")  # Adding a separator for readability

        # Sleep for 1 hour
        time.sleep(3600)

# Start a thread to run the periodic function
periodic_thread = threading.Thread(target=run_periodically)
periodic_thread.daemon = True  # Daemonize the thread so it automatically dies when the main thread dies
periodic_thread.start()