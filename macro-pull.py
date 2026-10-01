#!/usr/bin/env python3
"""Fetch macro market data (SPX, CSI 1000, US 10Y) and write JSON.
Designed for no_agent cron — stdout is delivered verbatim."""
import json, os, urllib.request, ssl
from datetime import datetime, timezone

YQL = 'https://query1.finance.yahoo.com/v8/finance/chart/'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) deltav-macro-puller/1.0'}
OUT = os.environ.get("DATA_DIR", os.path.join(os.getcwd(), "data")) + os.sep + "macro-market.json"

os.makedirs(os.path.dirname(OUT), exist_ok=True)
ctx = ssl.create_default_context()  # MITM guard: full cert verification; no opt-out in OSS edition

macro = {'spx': None, 'csi1000': None, 'us10y': None, 'updatedAt': ''}
targets = {
    'spx': YQL + '%5EGSPC?interval=1d&range=2d',
    'csi1000': YQL + '000852.SS?interval=1d&range=2d',
    'us10y': YQL + '%5ETNX?interval=1d&range=2d',
}

for key, url in targets.items():
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
            data = json.loads(r.read().decode())
        meta = data['chart']['result'][0]['meta']
        price = meta['regularMarketPrice']
        prev = meta.get('previousClose') or meta.get('chartPreviousClose', price)
        chg = round((price - prev) / prev * 100, 2) if prev and prev != 0 else None
        macro[key] = {
            'price': price,
            'prevClose': prev,
            'changePct': chg,
            'currency': meta.get('currency', 'USD'),
            'name': meta.get('shortName', key)
        }
        print(f'  {key}: {price} ({chg}%)')
    except Exception as e:
        print(f'  {key}: ERROR — {e}')

macro['updatedAt'] = datetime.now(timezone.utc).isoformat()
with open(OUT, 'w') as f:
    json.dump(macro, f)
print(f'Wrote {OUT} ({os.path.getsize(OUT)} bytes)')
