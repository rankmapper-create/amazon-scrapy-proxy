# Amazon Scrapy spider with rotating proxies

This project scrapes product summaries from Amazon search-result pages and
assigns a proxy endpoint to every download. Retried requests are assigned a
different endpoint when the pool contains more than one proxy.

Use it only for pages you are permitted to crawl. The project respects
`robots.txt`, uses a low request rate, and does not attempt to solve or bypass
CAPTCHAs. A detected challenge page is retried a limited number of times.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
cp proxies.txt.example proxies.txt
```

Edit `proxies.txt` and add one proxy URL per line:

```text
http://username:password@host:port
```

Keep `proxies.txt` private. It is intentionally not committed. A rotating
gateway from a proxy provider also works; in that case a single URL is enough
because the provider rotates the exit IP behind the gateway.

## Run

```bash
scrapy crawl amazon_search \
  -a query="wireless keyboard" \
  -a pages=2 \
  -O output/products.jsonl
```

The default marketplace is `amazon.in`. Override it per run:

```bash
scrapy crawl amazon_search -a query="coffee grinder" -a domain=amazon.com \
  -O output/products.jsonl
```

You can configure proxies without a file by setting a comma-separated value:

```bash
export AMAZON_PROXY_URLS='http://user:pass@host1:8000,http://user:pass@host2:8000'
```

Proxy credentials are not printed in logs. HTTP 403/429 and transient server
errors are retried up to `AMAZON_RETRY_TIMES` times, with a new proxy selected
for each attempt.
