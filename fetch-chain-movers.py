#!/usr/bin/env python3
"""
fetch-chain-movers.py — Fetch top chains and compute 24h TVL changes from DeFiLlama.
Outputs: public/data/chain-movers.json

Uses DeFiLlama /v2/historicalChainTvl/{name} per chain (last 2 data points = 24h delta).
Runs as a cron job every 30 min (DeFiLlama updates daily, but we cache for freshness).
"""
import json, os, sys, time, urllib.request, urllib.parse, ssl
from pathlib import Path

PUBLIC_DIR = Path(os.environ.get("DATA_DIR", 
    os.environ.get("DATA_DIR", "./data")))
TOP_N = 20  # fetch top N chains for movers
GAINERS_COUNT = 5
LOSERS_COUNT = 5

os.makedirs(PUBLIC_DIR, exist_ok=True)

ctx = ssl.create_default_context()  # MITM guard: full cert verification; no opt-out in OSS edition
UA = "Mozilla/5.0 (compatible; deltav-chain-movers-fetcher/1.0)"

def fetch_json(url, timeout=12):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print(f"  ⚠ {url[:70]} -> {e}", file=sys.stderr)
        return None

def main():
    # 1. Get top chains by TVL
    print("[ChainMovers] Fetching top chains...")
    chains = fetch_json("https://api.llama.fi/v2/chains")
    if not chains:
        print("[ChainMovers] FAIL: cannot fetch chains", file=sys.stderr)
        return 1
    
    top = sorted(chains, key=lambda x: x.get("tvl", 0) or 0, reverse=True)[:TOP_N]
    print(f"[ChainMovers] Top {len(top)} chains, fetching 24h history...")
    
    results = []
    for c in top:
        name = c["name"]
        current_tvl = c.get("tvl", 0) or 0
        try:
            encoded = urllib.parse.quote(name, safe="")
            url = f"https://api.llama.fi/v2/historicalChainTvl/{encoded}"
            hist = fetch_json(url)
            if isinstance(hist, list) and len(hist) >= 2:
                yesterday_tvl = hist[-2].get("tvl", 0)
                if yesterday_tvl and yesterday_tvl > 0:
                    change_pct = ((current_tvl - yesterday_tvl) / yesterday_tvl) * 100
                    results.append({
                        "name": name,
                        "tvl": current_tvl,
                        "change_24h": round(change_pct, 2),
                    })
                    print(f"  {name:25s} ${current_tvl/1e9:.2f}B  {change_pct:+.2f}%")
                else:
                    print(f"  {name:25s} ⚠ zero yesterday TVL")
            else:
                print(f"  {name:25s} ⚠ no historical data ({len(hist) if isinstance(hist,list) else type(hist).__name__})")
        except Exception as e:
            print(f"  {name:25s} ⚠ error: {e}")
        time.sleep(0.2)  # rate limit
    
    if not results:
        print("[ChainMovers] FAIL: no chain change data computed", file=sys.stderr)
        return 1
    
    # 2. Compute gainers and losers
    gainers = sorted([r for r in results if r["change_24h"] > 0], 
                     key=lambda x: -x["change_24h"])[:GAINERS_COUNT]
    losers = sorted([r for r in results if r["change_24h"] < 0], 
                    key=lambda x: x["change_24h"])[:LOSERS_COUNT]
    
    # 3. Write output
    output = {
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": "DeFiLlama (per-chain historical TVL)",
        "gainers": gainers,
        "losers": losers,
        "all": results,  # all N chains for reference
    }
    
    out_path = PUBLIC_DIR / "chain-movers.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\n[ChainMovers] ✓ {out_path}")
    g_str = ", ".join(f'{g["name"]} {g["change_24h"]:+.1f}%' for g in gainers)
    l_str = ", ".join(f'{l["name"]} {l["change_24h"]:+.1f}%' for l in losers)
    print(f"  ▲ Gainers: {g_str}")
    print(f"  ▼ Losers:  {l_str}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
