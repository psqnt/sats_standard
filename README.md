# Sats Standard Tweet Bot

A Twitter bot which pulls $SPY price and Bitcoin price and denominates the price of 1 share of $SPY in satoshis (bitcoin base unit), then it publishes the tweet.

[Follow the bot here](https://twitter.com/SatsStandard)

## Purpose

This project had two purposes:
1. Provide an easily accessible way to see $SPY priced in Bitcoin (easily accessible meaning following this bot)
2. Provide a simple example to others attempting to build twitter bots

## Tools

List of other technologies used in this project and the purpose they serve:

* [Python](https://github.com/python/cpython)
* [SqlAlchemy](https://github.com/sqlalchemy/sqlalchemy) and [SQLite](https://github.com/mackyle/sqlite) for Database Object Relation Mapping and the actual Database (file)
* [Tweepy](https://github.com/tweepy/tweepy) a Python Twitter Client used to post tweets
* [Coinbase Client](https://github.com/danpaquin/coinbasepro-python) to pull Bitcoin price data
* [Finnhub Client](https://github.com/Finnhub-Stock-API/finnhub-python) to pull Stock price data
* [Jinja](https://github.com/pallets/jinja) a template engine used to compose tweets


## Usage

Note this will not work for you right off the bat. You will need to:
1. Make a twitter account and go through the process of applying for a bot (hobby)
2. Get an API Key from FinnHubb
3. Create a .env folder, add your API keys from twitter and finnhub in and then source those as environment variables so they can be read into this python program.

Then you can:

clone this repo (and edit), create virtualenv, install dependencies from `requirements.txt`

```bash
git clone https://github.com/psqnt/sats_standard.git
cd sats_standard
python -m venv venv
. venv/bin/activate
pip install -r requirements.txt
```

Once the project is setup, you should run this in a crontab on a computer / server that is always on.

## Example Crontab

On a computer running 24/7 (Always On) - create a crontab and add this to it (make sure it is the correct path to your project)

Open crontab edit
```
$ crontab -e
```

Add this to the crontab file. It sources the environment variables needed for API keys and executes the python program using the virtualenvs python (which means it has the dependencies installed)
```
# Run the twitter bot once every 1 at the beginning of every hour
0 * * * * . /path/to/project/.env; /path/to/project/venv/bin/python3 /path/to/project/main.py
```

## Query Saved Data

In the root project directory an sqlite database file `app.db` will be created and appended to by this program.

You can query the data by using `sqlite3` in the command line directly

```
$ sqlite3 app.db
```

or in the python interpreter (virtualenv python so it has dependencies):
```python
(venv) $ python
Python 3.8.5 (default, Jul 21 2020, 10:48:26)
[Clang 11.0.3 (clang-1103.0.32.62)] on darwin
Type "help", "copyright", "credits" or "license" for more information.
>>> from db import initialize_database, Asset, PriceHistory, Tweet
>>> Session = initialize_database()
>>> session = Session()
>>> tweets = session.query(Tweet).all()
>>> for t in tweets:
...     print(t.tweet_id, t.tweet_data)
...
1302615226446237698 {'spy_in_sats': 3357871, 'percent_change': None, 'btc_price': '10201.01', 'spy_price': 342.57}
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](https://github.com/psqnt/sats_standard/blob/master/LICENSE)