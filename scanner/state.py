import json
import os

from . import config


def load_state() -> dict:
    if os.path.exists(config.STATE_FILE):
        try:
            with open(config.STATE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_state(state: dict) -> None:
    with open(config.STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, default=str)


def get_ticker_state(state: dict, ticker: str) -> dict:
    return state.setdefault(ticker, {"seen_rating_keys": [], "prev_target_mean": None})


def mark_rating_seen(state: dict, ticker: str, key: str) -> None:
    t_state = get_ticker_state(state, ticker)
    if key not in t_state["seen_rating_keys"]:
        t_state["seen_rating_keys"].append(key)
        # Keep this list bounded -- no need to remember rating actions forever.
        t_state["seen_rating_keys"] = t_state["seen_rating_keys"][-50:]


def set_prev_target_mean(state: dict, ticker: str, mean: float) -> None:
    get_ticker_state(state, ticker)["prev_target_mean"] = mean
