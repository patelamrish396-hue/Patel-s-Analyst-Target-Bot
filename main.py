from scanner import config, symbols, analyst_data, state as state_store, notifier
from scanner import signals as signal_engine

ICONS = {
    "ANALYST_RATING_ACTION": "🧑‍💼",
    "PRICE_TARGET_CHANGE": "🎯",
}


def format_alert(ticker: str, sig: dict) -> str:
    clean_symbol = ticker.replace(".NS", "")
    icon = ICONS.get(sig["type"], "🔔")
    label = sig["type"].replace("_", " ").title()
    return f"{icon} <b>{clean_symbol}</b> — {label}\n{sig['detail']}"


def main():
    # Unlike the price-based bots, analyst reports can be published any
    # time of day (including after market close), so there's no
    # market-hours gate here -- this bot just runs whenever it's triggered.
    print("Fetching stock symbol list...")
    tickers = symbols.get_nse_symbols()
    print(f"Tracking {len(tickers)} symbols")

    print("Fetching analyst data (this is per-ticker, so it's slower than "
          "the price-based bots -- expect this to take a while)...")
    data_by_ticker = analyst_data.fetch_all(tickers)
    print(f"Found analyst data for {len(data_by_ticker)}/{len(tickers)} symbols "
          f"(most NSE stocks have no analyst coverage at all -- this is expected)")

    state = state_store.load_state()
    alerts = []

    for ticker, data in data_by_ticker.items():
        for sig in signal_engine.analyze(ticker, data, state):
            alerts.append((ticker, sig))

    print(f"{len(alerts)} alert(s) to send")

    batch = []
    for ticker, sig in alerts:
        batch.append(format_alert(ticker, sig))
        if len(batch) == 15:
            notifier.send_message("\n\n".join(batch))
            batch = []
    if batch:
        notifier.send_message("\n\n".join(batch))

    state_store.save_state(state)


if __name__ == "__main__":
    main()
