import time
import yfinance as yf

from . import config


def fetch_analyst_data(ticker: str, retries: int = 2) -> dict:
    """
    Returns {'upgrades_downgrades': DataFrame or None, 'price_targets': dict
    or None, 'errored': bool} for a single ticker. 'errored' distinguishes
    a genuine fetch failure (Yahoo's endpoint erroring) from a clean "no
    analyst coverage" result (most NSE stocks have none -- expected, not
    an error) -- this matters for diagnosing whether failures mean "no
    coverage" or "the endpoint itself is broken."

    Retries with a fresh Ticker object on failure: Yahoo's quoteSummary
    endpoint (which backs this data) uses a cookie/crumb handshake that
    can intermittently fail and then succeed on a subsequent attempt.
    """
    result = {"upgrades_downgrades": None, "price_targets": None, "errored": False}

    for attempt in range(retries + 1):
        t = yf.Ticker(ticker)
        ud_failed = pt_failed = False

        try:
            ud = t.upgrades_downgrades
            if ud is not None and not ud.empty:
                result["upgrades_downgrades"] = ud
        except Exception:
            ud_failed = True

        try:
            pt = t.analyst_price_targets
            if pt:
                result["price_targets"] = pt
        except Exception:
            pt_failed = True

        if not (ud_failed and pt_failed):
            result["errored"] = False
            break
        result["errored"] = True
        if attempt < retries:
            time.sleep(config.REQUEST_DELAY_SECONDS * (attempt + 2))

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
    error_count = 0

    for i, ticker in enumerate(tickers, 1):
        try:
            data = fetch_analyst_data(ticker)
            if data["errored"]:
                error_count += 1
            if data["upgrades_downgrades"] is not None or data["price_targets"] is not None:
                out[ticker] = data
        except Exception as e:
            error_count += 1
            print(f"[warn] {ticker}: analyst data fetch failed ({e})")

        if i % 100 == 0:
            print(f"  ...processed {i}/{total} tickers ({error_count} errors so far)")

        time.sleep(config.REQUEST_DELAY_SECONDS)

    error_rate = error_count / total if total else 0
    print(f"Finished: {error_count}/{total} tickers errored ({error_rate:.0%})")
    if error_rate > 0.5:
        print(
            "[warn] Over half of all tickers errored -- this points to Yahoo's "
            "analyst-data endpoint failing broadly, not most stocks genuinely "
            "lacking coverage. See the README's troubleshooting section."
        )

    return out
