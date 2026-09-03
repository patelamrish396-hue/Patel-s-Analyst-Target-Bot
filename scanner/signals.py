from datetime import datetime, timedelta, timezone

import pandas as pd

from . import config
from . import state as state_store


def _rating_key(date_str: str, firm: str, to_grade: str) -> str:
    return f"{date_str}|{firm}|{to_grade}"


def analyze_rating_actions(ticker: str, ud, state: dict) -> list:
    """
    Detects new analyst rating actions (upgrade/downgrade/initiate/
    reiterate) not seen in a previous run. On a ticker's very first-ever
    run, existing history is recorded as a baseline without alerting --
    otherwise the first run would dump months of old rating history as
    if it all just happened today.
    """
    if ud is None or ud.empty:
        return []

    t_state = state_store.get_ticker_state(state, ticker)
    is_first_run = len(t_state["seen_rating_keys"]) == 0
    freshness_cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=config.RATING_ACTION_FRESHNESS_DAYS)

    signals = []
    for date, row in ud.iterrows():
        try:
            date_str = pd.Timestamp(date).strftime("%Y-%m-%d")
            date_ts = pd.Timestamp(date).to_pydatetime().replace(tzinfo=None)
        except Exception:
            continue

        firm = str(row.get("Firm", "Unknown"))
        to_grade = str(row.get("ToGrade", ""))
        from_grade = str(row.get("FromGrade", ""))
        action = str(row.get("Action", ""))
        key = _rating_key(date_str, firm, to_grade)

        already_seen = key in t_state["seen_rating_keys"]
        state_store.mark_rating_seen(state, ticker, key)

        if already_seen:
            continue
        if is_first_run:
            continue  # establishing baseline only, don't alert on backlog
        if date_ts < freshness_cutoff:
            continue  # not recent enough to be worth surfacing now

        detail = f"{firm}: {action or 'rated'} {to_grade}".strip()
        if from_grade and from_grade.lower() not in ("", "nan", "none"):
            detail += f" (from {from_grade})"

        signals.append({
            "type": "ANALYST_RATING_ACTION",
            "detail": detail,
            "strength": 1.0,
        })

    return signals


def analyze_price_target(ticker: str, price_targets: dict, state: dict) -> list:
    """
    Detects a material change in the consensus (mean) analyst price
    target vs. the last time this ticker was checked. First-ever check
    for a ticker just records the baseline -- nothing to compare against yet.
    """
    if not price_targets:
        return []

    cur_mean = price_targets.get("mean")
    if cur_mean is None:
        return []

    t_state = state_store.get_ticker_state(state, ticker)
    prev_mean = t_state["prev_target_mean"]
    state_store.set_prev_target_mean(state, ticker, cur_mean)

    if prev_mean is None or prev_mean <= 0:
        return []  # baseline run, nothing to compare against yet

    pct_change = (cur_mean - prev_mean) / prev_mean * 100
    if abs(pct_change) < config.PRICE_TARGET_CHANGE_THRESHOLD_PCT:
        return []

    direction = "raised" if pct_change > 0 else "cut"
    return [{
        "type": "PRICE_TARGET_CHANGE",
        "detail": (
            f"Consensus target {direction} from {prev_mean:.2f} to "
            f"{cur_mean:.2f} ({pct_change:+.1f}%)"
        ),
        "strength": abs(pct_change),
    }]


def analyze(ticker: str, analyst_data: dict, state: dict) -> list:
    signals = []
    if config.ALERT_ON_RATING_ACTIONS:
        signals.extend(analyze_rating_actions(ticker, analyst_data.get("upgrades_downgrades"), state))
    if config.ALERT_ON_PRICE_TARGET_CHANGES:
        signals.extend(analyze_price_target(ticker, analyst_data.get("price_targets"), state))
    return signals
