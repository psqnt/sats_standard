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
    placeholder = Path('tweet_template.txt').read_text()
    template = Template(placeholder)
    return template.render(**tweet_data)


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

# Check if we have any price history
yesterday_datetime_early = datetime.now() - timedelta(days=1, hours=1)
yesterday_datetime_late = datetime.now() - timedelta(days=1) + timedelta(hours=1)
spy = session.query(Asset).filter_by(ticker='SPY').first()
btc = session.query(Asset).filter_by(ticker='BTC').first()
spy_price_yesterday = session.query(PriceHistory).filter(
    PriceHistory.timestamp >= yesterday_datetime_early,
    PriceHistory.timestamp <= yesterday_datetime_late,
    PriceHistory.asset_id == spy.id
).first()

if spy_price_yesterday is None:
    percent_change = None
else:
    percent_change = (spy_price_yesterday.price_sats - spy_in_sats) / spy_in_sats

# Data package to build the tweet
tweet_data = {
    'spy_in_sats': spy_in_sats,
    'percent_change': percent_change,
    'btc_price': current_btc_in_dollars,
    'spy_price': current_spy_in_dollars
}


# Authorize twitter client
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(twitter_key, twitter_secret)
api = tweepy.API(auth)

# Compose tweet, write data to database
tweet_content = compose_tweet(tweet_data)
tweet = Tweet(
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

# Post tweet and close database connection
api.update_status(tweet_content)
session.close()