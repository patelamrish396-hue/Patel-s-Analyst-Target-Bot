# NSE Analyst Ratings & Price Target Telegram Bot

A third, separate bot — this one tracks **analyst/brokerage activity**
rather than price action:

- 🧑‍💼 **New analyst rating actions** — upgrades, downgrades, initiations,
  and reiterations from brokerages (Motilal Oswal, ICICI Securities,
  Kotak, etc.), sourced via Yahoo Finance's analyst data for each stock
- 🎯 **Consensus price target changes** — alerts when the average analyst
  price target moves by more than a threshold (default 5%) since the last
  check

## ⚠️ Read this first — this bot is structurally different from the others

- **This data comes from Yahoo Finance, not NSE.** Brokerages publish
  their own research independently; there's no single official exchange
  feed for this. Yahoo aggregates it, and `yfinance` exposes that
  aggregation, but coverage and freshness depend entirely on Yahoo's data.
- **Most NSE stocks have zero analyst coverage.** Only large and
  mid-caps typically get brokerage attention. Don't be surprised if the
  vast majority of the ~750-stock universe returns nothing — that's
  expected, not a bug.
- **This can't be batch-fetched like price data.** Unlike the other bots
  (which download thousands of tickers' prices in one call), analyst
  data is fetched **one ticker at a time**. A full run over ~750 stocks
  will take noticeably longer and is more exposed to rate-limiting than
  the price-based bots — there's a small delay between requests
  (`REQUEST_DELAY_SECONDS`) to be gentler about this, but it's a
  structural limitation of the data, not something that can be fully
  engineered away.
- **The first run for any stock only establishes a baseline — it won't
  alert.** Otherwise, the very first run would dump months of old rating
  history and an arbitrary starting price target as if they all just
  happened. You'll start seeing real alerts from the second time a given
  stock is checked onward.
- **Not investment advice.** An analyst rating or price target is one
  firm's opinion, not a guarantee — and price targets in particular are
  frequently wrong. Treat these as "worth knowing," not signals to act
  on blindly.

## Setup

### 1. Create a *third* separate Telegram bot
Same process as before via [@BotFather](https://t.me/BotFather) — a
distinct bot so this alert stream doesn't mix with your other two.

### 2. Push this project to a new GitHub repo
```bash
cd nse-analyst-bot
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/<you>/<repo>.git
git push -u origin main
```

### 3. Add secrets
**Settings → Secrets and variables → Actions → New repository secret**
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

### 4. Enable Actions
Runs automatically 3x/day on weekdays (~9:47 AM, ~1:03 PM, ~4:07 PM IST —
nudged off round times to avoid GitHub's peak-load scheduling window, per
the same lesson from the other two bots). Use **Run workflow** for a
manual test, but expect it to take several minutes given the per-ticker
fetching — don't assume it's stuck.

## Tuning

| Variable | Default | Meaning |
|---|---|---|
| `UNIVERSE` | total_market | `"total_market"` (~750), `"nifty500"` (~500), or `"all"` (~2000+, not recommended given the per-ticker cost) |
| `ALERT_ON_RATING_ACTIONS` | true | Toggle the rating-action signal on/off |
| `ALERT_ON_PRICE_TARGET_CHANGES` | true | Toggle the price-target signal on/off |
| `PRICE_TARGET_CHANGE_THRESHOLD_PCT` | 5.0 | Minimum consensus target move (%) to alert on |
| `RATING_ACTION_FRESHNESS_DAYS` | 3 | How recent a newly-discovered rating action must be to alert (older backlog entries are ignored) |
| `REQUEST_DELAY_SECONDS` | 0.4 | Delay between each ticker's request, to go easier on rate limits |

## Local testing

```bash
pip install -r requirements.txt
export TELEGRAM_BOT_TOKEN=xxx
export TELEGRAM_CHAT_ID=xxx
python main.py
```

Expect this to run much slower locally than the other bots too, for the
same per-ticker reason.

## Troubleshooting: scheduled runs missing entirely

Same known GitHub Actions limitation as the other two bots — see their
READMEs for the full explanation. The three check times here are already
nudged off round numbers for this reason.

## Troubleshooting: yfinance attribute errors

This bot leans on `Ticker.upgrades_downgrades` and
`Ticker.analyst_price_targets`, which are real, documented yfinance
features — but yfinance's exact data shape has changed across versions
before. If the very first live run throws an `AttributeError` or
`KeyError` inside `scanner/analyst_data.py`, paste the traceback back and
it can be patched — this is the one part of the project family that
couldn't be tested against live data before shipping, since there's no
network access available in the environment this was built in.

## Project structure

```
main.py                  # entry point, orchestration
scanner/
  config.py               # thresholds & settings
  symbols.py              # fetches stock universe (Nifty 500/Total Market/all NSE)
  analyst_data.py          # per-ticker fetch of ratings + price targets
  signals.py               # new-rating-action / price-target-change detection
  state.py                 # tracks seen ratings + previous price targets
  notifier.py               # Telegram sending
.github/workflows/scan.yml # the cron schedule
state.json                 # committed automatically to remember past state
```
