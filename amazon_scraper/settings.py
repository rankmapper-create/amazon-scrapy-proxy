"""Scrapy settings for the Amazon product search spider."""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

BOT_NAME = "amazon_scraper"

SPIDER_MODULES = ["amazon_scraper.spiders"]
NEWSPIDER_MODULE = "amazon_scraper.spiders"

# Respect the site's published crawling policy. Only crawl pages that you are
# permitted to access and comply with Amazon's terms and applicable law.
ROBOTSTXT_OBEY = True

CONCURRENT_REQUESTS = int(os.getenv("AMAZON_CONCURRENT_REQUESTS", "2"))
CONCURRENT_REQUESTS_PER_DOMAIN = CONCURRENT_REQUESTS
DOWNLOAD_DELAY = float(os.getenv("AMAZON_DOWNLOAD_DELAY", "2.0"))
RANDOMIZE_DOWNLOAD_DELAY = True
DOWNLOAD_TIMEOUT = 30

COOKIES_ENABLED = False
TELNETCONSOLE_ENABLED = False

USER_AGENT = os.getenv(
    "AMAZON_USER_AGENT",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0 Safari/537.36",
)

DOWNLOADER_MIDDLEWARES = {
    "amazon_scraper.middlewares.RotatingProxyMiddleware": 610,
    "scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware": 750,
}

# Scrapy's retry middleware will recreate blocked/failed requests. The proxy
# middleware assigns a different proxy whenever that request is downloaded.
RETRY_ENABLED = True
RETRY_TIMES = int(os.getenv("AMAZON_RETRY_TIMES", "3"))
RETRY_HTTP_CODES = [403, 408, 429, 500, 502, 503, 504, 522, 524]

# The middleware reads these values and filters credentials from log output.
AMAZON_PROXY_URLS = os.getenv("AMAZON_PROXY_URLS", "")
AMAZON_PROXY_FILE = os.getenv("AMAZON_PROXY_FILE", "")
AMAZON_DOMAIN = os.getenv("AMAZON_DOMAIN", "amazon.in")
AMAZON_CHALLENGE_RETRY_TIMES = int(
    os.getenv("AMAZON_CHALLENGE_RETRY_TIMES", "2")
)

FEED_EXPORT_ENCODING = "utf-8"
FEED_EXPORT_INDENT = 2
LOG_LEVEL = os.getenv("SCRAPY_LOG_LEVEL", "INFO")

REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
