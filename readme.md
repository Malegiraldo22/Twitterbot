# Twitter Automation Bot

This project is a Python-based bot that automates the creation and posting of tweets on Twitter. The bot uses Google Sheets to log posted tweets, errors, and long tweets that exceed Twitter's character limit. The tweets are generated using Google's Gemini 1.5 Pro language model, and OAuth1.0 is used for authentication with Twitter.

## Table of Contents

- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [Usage](#usage)
- [Functions](#functions)
- [Error Handling](#error-handling)
- [Scheduler](#scheduler)
- [Contributing](#contributing)
- [License](#License)

## Installation

1. Clone the repository to your local machine:

    ```bash
    git clone https://github.com/Malegiraldo22/Twitterbot.git
    cd Twitterbot
    ```

2. Install the required dependencies:

    ```bash
    pip install -r requirements.txt
    ```

3. Set up your Google Sheets API credentials and Twitter API credentials as described in the [Environment Variables](#environment-variables) section.

4. Create a `.env` file in the root directory and populate it with the required environment variables.

## Environment Variables

This project requires several environment variables to be set for authentication and configuration. These variables should be defined in a `.env` file in the root directory of the project.

### Required Variables

- **Google Sheets API:**
    - `GOOGLE_JSON`: JSON string of the Google service account credentials.
    - `GOOGLE_SHEET`: URL of the Google Sheet to use for logging data.

- **Twitter API:**
    - `CONSUMER_KEY`: Twitter API consumer key.
    - `CONSUMER_SECRET`: Twitter API consumer secret.

- **Google Gemini API:**
    - `GOOGLE_AI_KEY`: API key for Google's Gemini model.

Example `.env` file:

```plaintext
GOOGLE_JSON='{"type":"service_account",...}'
GOOGLE_SHEET='https://docs.google.com/spreadsheets/d/your-sheet-id'
CONSUMER_KEY='your-consumer-key'
CONSUMER_SECRET='your-consumer-secret'
GOOGLE_AI_KEY='your-google-ai-key'
```
## Usage
To start the bot, simply run the following command:
```python
python bot.py
```
The bot will authenticate with Google Sheets, Gemini and Twitter, then start generating and posting tweets at regular intervals (every hour by default)

### Customizing Tweet Themes and Emotions
The `theme_selection()` function randomly selects a theme and an emotion to generate tweets. You can customize the list of themes and emotions in the function.

## Functions
### `theme_selection()`
Randomly selects a theme and an emotion to be used for tweet generation.
* Returns
    * `theme (str)`: Selected theme for the tweet
    * `voice (str)`: selected voice to set the tone of the tweet

###`internet_search()`
Searches for the most recent news using DuckDuckGo
*Returns
    * `news (list)`: List that contains the most recent news about the theme selected

### `log_to_sheet(sheet, message)`
Logs a message with a timestamp to a specified Google Sheet
* Parameters
    * `sheet`: The Google Sheet to log data to
    * `message (str)`: The message to log

### `create_and_publish_tweet(theme, emotion, max_retires=5)`
Generates a tweet with a specified theme and emotion, then attempts to post it on twitter. If the tweet exceeds 280 characters, it is logged in a "Long Tweets" sheet, and a new tweet is generated. If an error occurs, it is logged in an "Errors" sheet, and the function retries up to `max_retries` times.
* Parameters
    * `theme (str): Theme selected by `theme_selection()` function
    * `voice (str): Voice selected by `theme_selection()` function
    * `max_retries (int, optional): Maximum number of retries for posting the tweet. Defaults to 5.
* Returns
    * `tweet (str)`: The generated tweet text, or `None` if the tweet could not be published

### `run_periodically()`
Periodically generates and post tweets

### `tweet_schedule()`
Schedules the bot to post tweets at regular intervals (every hour by default) using the `APScheduler` library

## Error Handling
The bot includes error handling. If an error occurs during the authentication or tweet posting process, it is logged in the "Errors" sheet with a timestamp. If the tweet exceeds X's 280 character limit, it is logged in the "Long Tweets" sheet

## Scheduler
The bot uses the `APScheduler` library to schedule the tweet posting function (`run_periodically()`) at regular intervals. The schedule can be customized by modifying the `tweet_schedule()` function.

## Contributing
Contributions are welcome! Please fork the repository and submit a pull request with your changes.

## Example of generated tweets
![Example tweet](screenshots/Example1.png)
![Example tweet](screenshots/Example2.png)
![Example tweet](screenshots/Example3.png)
![Example tweet](screenshots/Example4.png)

## License

This project is licensed under the MIT License. See `LICENSE` for more information.