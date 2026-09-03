import os

# --- Universe ---
# Same verified NSE index sources as the other bots. Defaults to the
# Nifty Total Market Index (~750 stocks) since that's the real index
# closest to "Nifty 750" -- there's no official index by that exact name.
# Analyst coverage is naturally sparse outside large/mid-caps regardless,
# so most alerts will come from the larger names within this universe.
NIFTY_TOTAL_MARKET_URL = "https://niftyindices.com/IndexConstituent/ind_niftytotalmarket_list.csv"
NIFTY500_URL = "https://niftyindices.com/IndexConstituent/ind_nifty500list.csv"
NSE_EQUITY_LIST_URL = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
UNIVERSE = os.environ.get("UNIVERSE", "total_market")

# --- What to alert on ---
ALERT_ON_RATING_ACTIONS = os.environ.get("ALERT_ON_RATING_ACTIONS", "true").lower() == "true"
ALERT_ON_PRICE_TARGET_CHANGES = os.environ.get("ALERT_ON_PRICE_TARGET_CHANGES", "true").lower() == "true"

# Minimum consensus price target move (%) to bother alerting on.
PRICE_TARGET_CHANGE_THRESHOLD_PCT = float(os.environ.get("PRICE_TARGET_CHANGE_THRESHOLD_PCT", 5.0))

# How far back (in days) a rating action needs to be to still count as
# "new" the first time a ticker is ever processed. Prevents a flood of
# alerts for old rating history on the very first run.
RATING_ACTION_FRESHNESS_DAYS = int(os.environ.get("RATING_ACTION_FRESHNESS_DAYS", 3))

# --- Rate-limiting: analyst data is fetched per-ticker (not batchable
# the way price bars are), so a small delay between requests helps avoid
# tripping Yahoo's rate limits across a run of hundreds of tickers. ---
REQUEST_DELAY_SECONDS = float(os.environ.get("REQUEST_DELAY_SECONDS", 0.4))

STATE_FILE = "state.json"

# --- Telegram (a third, separate bot/chat from the other two) ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
