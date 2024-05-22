# Twitter Bot

This project is a Twitter bot built using Python. It generates and posts tweets automatically every hour using the Twitter API and Google's Generative AI (Gemini).

## How It Works

1. **Theme Selection**: The `theme_selection` function randomly selects a topic from a predefined list of themes. Additionally, it may include an optional emotion to add depth and variety to the generated tweets.

2. **Tweet Generation**: The `create_and_publish_tweet` function generates tweets based on the selected theme and optional emotion. It uses Google's Gemini 1.0 Pro language generation capabilities to create engaging and diverse content.

3. **Tweet Publishing**: After generating a tweet, the application uses the Twitter API to publish the tweet on a Twitter account. Users must authenticate with Twitter to authorize the application to access their account and publish tweets.

4. **Real-time Display**: The generated tweets are displayed in real-time using Streamlit, allowing users to see the tweets as they are generated. The Streamlit app provides a user-friendly interface for interacting with the application.

5. **Persistent Storage**: OAuth tokens are stored persistently to avoid re-authentication across sessions.

**Note**: Tweets are generated every hour, providing a continuous stream of content on the selected topics.

## Dependencies

The following dependencies are required for this project:

- `requests_oauthlib`: For handling OAuth authentication with the Twitter API.
- `os`: For accessing environment variables.
- `json`: For handling JSON data.
- `google.generativeai`: For using Gemini API.
- `random`: For selecting random themes and emotions.
- `datetime`: For handling date and time.
- `pandas`: For managing data.
- `streamlit`: For creating a user interface.
- `dotenv`: For loading environment variables from a `.env` file.
- `time`: For handling sleep intervals.
- `threading`: For running periodic tasks in a separate thread.
- `pickle`: For persistent storage

### Core Functions

- **Environment Setup**: Load environment variables from `.env` file.
- **OAuth Authentication**: Handle the Twitter OAuth process.
- **Theme Selection**: Randomly select a theme and emotion for tweet generation.
- **Tweet Creation and Posting**: Generate a tweet using Generative AI and post it to Twitter.
- **Periodic Execution**: Run the tweet creation and posting process every hour.

## Setup

1. Clone the repository:

    ```bash
    git clone https://github.com/your-username/twitter-bot.git
    ```

2. Install the required dependencies:

    ```bash
    pip install -r requirements.txt
    ```

3. Set up your Twitter API credentials and Google AI key by creating a `.env` file and adding the following:

    ```plaintext
    CONSUMER_KEY=your_twitter_consumer_key
    CONSUMER_SECRET=your_twitter_consumer_secret
    ACCESS_TOKEN=your_twitter_access_token
    ACCESS_SECRET=your_twitter_access_secret
    CLIENT_ID=your_twitter_client_id
    CLIENT_SECRET=your_twitter_client_secret
    GOOGLE_AI_KEY=your_google_gemini_ai_key
    ```

4. Run the application:

    ```bash
    streamlit run twitter_bot.py
    ```

## Customization

- You can customize the list of themes and emotions in the `theme_selection` function to tailor the generated tweets to your preferences or specific use case.

## Limitations

- The quality and coherence of the generated tweets may vary based on the complexity of the selected theme and the capabilities of the language model used.
- The Twitter API has rate limits and other restrictions that may affect the frequency and volume of tweets that can be published.

## Application interface
![Aplication Screenshot](screenshots/app_interface.png)

## Example of generated tweets
![Example tweet](screenshots/Example1.png)
![Example tweet](screenshots/Example2.png)
![Example tweet](screenshots/Example3.png)
![Example tweet](screenshots/Example4.png)