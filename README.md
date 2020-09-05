# Sats Standard Tweet Bot

A Twitter bot which pulls $SPY price and Bitcoin price and denominates the price of 1 share of $SPY in satoshis (bitcoin base unit), then it publishes the tweet.

## Usage

Note this will not work for you right off the bat. You will need to:
1. Make a twitter account and go through the process of applying for a bot (hobby)
2. Get an API Key from FinnHubb
3. Create a .env folder, add your API keys from twitter and finnhub in and then source those as environment variables so they can be read into this python program.

Then you can:

clone this repo (and edit), create virtualenv, install dependencies from `requirements.txt`

```
git clone https://github.com/psqnt/sats_standard.git
cd sats_standard
python -m venv venv
. venv/bin/activate
pip install -r requirements.txt
```

Once the project is setup, you should run this in a crontab on a computer / server that is always on.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License
[MIT](https://github.com/psqnt/sats_standard/blob/master/LICENSE)