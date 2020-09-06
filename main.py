import os
import cbpro
import finnhub
import tweepy
from datetime import datetime, timedelta
from decimal import Decimal
from dotenv import load_dotenv
from pathlib import Path  # Python 3.6+ only
from jinja2 import Template
from db import initialize_database, Asset, PriceHistory, Tweet


def compose_tweet(tweet_data: dict):
    placeholder = (
        Path(__file__).parent.absolute() / Path('tweet_template.txt')
    ).read_text()
    template = Template(placeholder)
    return template.render(**tweet_data)


def get_percent_change(new_price, old_price):
    percent_change = abs((new_price - old_price) / old_price) * 100
    return "{:.2f}".format(percent_change)


# Load environment variables into the system - api keys
# Setting override to True in case we get generated api keys
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path, override=True)

# get api keys from environment variables
finnhub_api_key = os.getenv('finnhub_api_key')
twitter_key = os.getenv('twitter_api_key')
twitter_secret = os.getenv('twitter_api_secret')
consumer_key = os.getenv('twitter_consumer_key')
consumer_secret = os.getenv('twitter_consumer_secret')

# Set the product tickers -> Bitcoin vs SPY
btc_product_ticker = 'BTC-USD'  # coinbase product ticker
spy_product_ticker = 'SPY'  # finnhub

# Create Data Clients - Coinbase Pro and FinnHub
public_client = cbpro.PublicClient()
finnhub_client = finnhub.Client(api_key=finnhub_api_key)

# Get BTC Price
btc_ticker = public_client.get_product_ticker(product_id=btc_product_ticker)
current_btc_in_dollars = btc_ticker.get('price', None)  # string

# Get Quote of SPY
spy_quote = finnhub_client.quote(spy_product_ticker)
current_spy_in_dollars = spy_quote.get('c', None)  # float, c is current price

# Convert BTC Price & SPY price to Satoshis
sats_in_btc = 100000000 # 100,000,000 sats in a bitcoin
sats_per_dollar = sats_in_btc // float(current_btc_in_dollars)
spy_in_sats = int(current_spy_in_dollars * sats_per_dollar)

# Create Database connection
Session = initialize_database()
session = Session()

# Get stored Assets (Bitcoin and SPY)
btc = session.query(Asset).filter_by(ticker='BTC').first()
spy = session.query(Asset).filter_by(ticker='SPY').first()

# New PriceHistory written every hour, pull the previous entry
spy_price_last_hour = (
    session.query(PriceHistory)
    .filter(PriceHistory.asset_id==spy.id)
    .order_by(PriceHistory.timestamp.desc())
    .first()
)

# In case the cronjob is delayed or early (not sure if early is possible)
# Query in between a 10 minute timespan for an entry
yesterday_datetime_early = datetime.now() - timedelta(days=1, minutes=5)
yesterday_datetime_late = datetime.now() - timedelta(days=1) + timedelta(minutes=5)

spy_price_yesterday = (
    session.query(PriceHistory)
    .filter(
        PriceHistory.timestamp>=yesterday_datetime_early,
        PriceHistory.timestamp<=yesterday_datetime_late,
        PriceHistory.asset_id==spy.id
    ).first()
)

# Convert values to percentages
if spy_price_last_hour is None:
    hourly_change = None
    hourly_symbol = None
    sats_hourly_difference = None
else:
    spy_in_sats_previous = spy_price_last_hour.price_sats
    sats_hourly_difference = spy_in_sats - spy_in_sats_previous
    hourly_change = get_percent_change(spy_in_sats_previous, spy_in_sats)
    if sats_hourly_difference >= 0:
        hourly_symbol = '+'
    else:
        hourly_symbol = '-'
    sats_hourly_difference = abs(sats_hourly_difference)  # remove symbol

if spy_price_yesterday is None:
    daily_change = None
    daily_symbol = None
    sats_daily_difference = None
else:
    spy_in_sats_previous_day = spy_price_yesterday.price_sats
    sats_daily_difference = spy_in_sats - spy_in_sats_previous_day
    daily_change = get_percent_change(spy_in_sats_previous_day, spy_in_sats)
    if sats_daily_difference >= 0:
        daily_symbol = '+'
    else:
        daily_symbol = '-'
    sats_daily_difference = abs(sats_daily_difference)

# Data package to build the tweet
tweet_data = {
    'spy_in_sats': spy_in_sats,
    'hourly_change': hourly_change,
    'hourly_symbol': hourly_symbol,
    'hourly_difference': sats_hourly_difference,
    'daily_change': daily_change,
    'daily_symbol': daily_symbol,
    'daily_difference': sats_daily_difference,
    'btc_price': current_btc_in_dollars,
    'spy_price': current_spy_in_dollars
}

# Authorize twitter client
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(twitter_key, twitter_secret)
api = tweepy.API(auth)

# Compose tweet
tweet_content = compose_tweet(tweet_data)

# Post tweet
try:
    response = api.update_status(tweet_content)
except tweepy.error.TweepError as e:
    print(e)
    response = False

# Write data to database
if response:
    tweet_id = response.id_str
    tweet = Tweet(
        tweet_id=tweet_id,
        content=tweet_content,
        tweet_data=tweet_data
    )
    spy_price_history = PriceHistory(
        asset_id=spy.id,
        price=current_spy_in_dollars,
        price_sats=spy_in_sats,
    )
    btc_price_history = PriceHistory(
        asset_id=btc.id,
        price=current_btc_in_dollars,
        price_sats=sats_in_btc
    )
    session.add(tweet)
    session.add(spy_price_history)
    session.add(btc_price_history)
    session.commit()

# Close database connection
session.close()