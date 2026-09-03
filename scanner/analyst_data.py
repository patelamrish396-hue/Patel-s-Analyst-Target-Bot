import time
import yfinance as yf

from . import config


def fetch_analyst_data(ticker: str) -> dict:
    """
    Returns {'upgrades_downgrades': DataFrame or None, 'price_targets': dict
    or None} for a single ticker. Failures on either piece are swallowed
    (returned as None) rather than raised, since most NSE stocks simply
    have no analyst coverage at all -- that's an expected, common case,
    not an error worth logging per-ticker across a universe this size.
    """
    result = {"upgrades_downgrades": None, "price_targets": None}
    t = yf.Ticker(ticker)

    try:
        ud = t.upgrades_downgrades
        if ud is not None and not ud.empty:
            result["upgrades_downgrades"] = ud
    except Exception:
        pass

    try:
        pt = t.analyst_price_targets
        if pt:
            result["price_targets"] = pt
    except Exception:
        pass

    return result


def fetch_all(tickers: list) -> dict:
    """
    Sequentially fetches analyst data for every ticker, with a small delay
    between requests. This can't be batched the way price bars can --
    analyst/recommendation data is fetched per-ticker under the hood --
    so a full run over a few hundred tickers will take noticeably longer
    than the price-based bots' bulk downloads.
    """
    out = {}
    total = len(tickers)
    for i, ticker in enumerate(tickers, 1):
        try:
            data = fetch_analyst_data(ticker)
            if data["upgrades_downgrades"] is not None or data["price_targets"] is not None:
                out[ticker] = data
        except Exception as e:
            print(f"[warn] {ticker}: analyst data fetch failed ({e})")

        if i % 100 == 0:
            print(f"  ...processed {i}/{total} tickers")

        time.sleep(config.REQUEST_DELAY_SECONDS)

    return out
