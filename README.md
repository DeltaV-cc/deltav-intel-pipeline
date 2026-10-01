# Delta V Intel Pipeline — Layer-0 Market Data Fetchers

Public, no-LLM Python fetchers that power [deltav.cc](https://deltav.cc)'s
IntelHub market intelligence. Pure `urllib`/`feedparser`: no agents, no LLM
calls, no telemetry. Written for deterministic cron execution on a private box.

## Philosophy

- **No LLM in the data path.** Market data must be verifiable, reproducible, and live. LLMs sit only in analysis layers.
- **Secrets env-first.** Keys are read from the environment (or a `*_KEY_FILE` path), never committed.
- **Fail loudly, degrade gracefully.** Each fetcher falls back to a previous output if a source skips a beat.

## Fetchers

| Script | Source | Output | Key |
|---|---|---|---|
| `fetch-chain-movers.py` | CoinGecko | `chain-movers.json` | none |
| `fetch-etf-flows.py` | Farside Investors | `etf-flows.json` | none |
| `fetch-bold-yields.py` | Bold / internal payload | `bold-yields.json` | none |
| `fetch-dune-dex-matrix.py` | Dune Analytics | `dex-matrix.json` | `DUNE_API_KEY` |
| `fetch-infosec.py` | InfoSec RSS feeds | `infosec.json` | none |
| `fetch-ai-personas.py` | AI sim personas | `ai-personas.json` | none |
| `fetch-ai-labs.py` | AI labs RSS / X | `ai-labs.json` | none |
| `macro-pull.py` | Yahoo Finance | `macro-market.json` | none |

## Usage

```bash
# every script writes JSON next to itself or ./data/
DUNE_API_KEY=ex… python3 fetch-dune-dex-matrix.py
python3 fetch-chain-movers.py
```

## Output contract

Each JSON carries `last_updated` and a `sources` block describing where the
data came from. Nothing is anonymized — the site renders whatever is upstream.

## License — MIT
