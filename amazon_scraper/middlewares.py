"""Downloader middleware for rotating authenticated HTTP proxies."""

from __future__ import annotations

import itertools
import logging
from pathlib import Path
from urllib.parse import urlsplit

from scrapy import Request
from scrapy.crawler import Crawler
from scrapy.downloadermiddlewares.retry import get_retry_request
from scrapy.http import Response, TextResponse

logger = logging.getLogger(__name__)


def _redact_proxy(proxy_url: str) -> str:
    """Return a log-safe proxy description without username/password."""
    parsed = urlsplit(proxy_url)
    host = parsed.hostname or "unknown"
    port = f":{parsed.port}" if parsed.port else ""
    return f"{parsed.scheme}://{host}{port}"


def _load_proxy_file(filename: str) -> list[str]:
    if not filename:
        return []

    path = Path(filename).expanduser()
    if not path.is_file():
        raise FileNotFoundError(f"Proxy file does not exist: {path}")

    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def _validate_proxy_urls(proxy_urls: list[str]) -> list[str]:
    validated: list[str] = []
    for proxy_url in proxy_urls:
        parsed = urlsplit(proxy_url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError(
                "Invalid proxy URL. Expected http://[user:pass@]host:port"
            )
        validated.append(proxy_url)
    return list(dict.fromkeys(validated))


class RotatingProxyMiddleware:
    """Assign proxies round-robin and change proxy between retry attempts."""

    challenge_markers = (
        b"enter the characters you see below",
        b"api-services-support@amazon.com",
        b"sorry, we just need to make sure you're not a robot",
    )

    def __init__(self, proxies: list[str], challenge_retry_times: int) -> None:
        self.proxies = proxies
        self._proxy_cycle = itertools.cycle(proxies)
        self.challenge_retry_times = challenge_retry_times

    @classmethod
    def from_crawler(cls, crawler: Crawler) -> "RotatingProxyMiddleware":
        inline = crawler.settings.get("AMAZON_PROXY_URLS", "")
        proxies = [part.strip() for part in inline.replace("\n", ",").split(",")]
        proxies = [proxy for proxy in proxies if proxy]
        proxies.extend(_load_proxy_file(crawler.settings.get("AMAZON_PROXY_FILE", "")))
        proxies = _validate_proxy_urls(proxies)

        if not proxies:
            raise RuntimeError(
                "No proxies configured. Set AMAZON_PROXY_URLS or AMAZON_PROXY_FILE."
            )

        logger.info("Loaded %d proxy endpoint(s)", len(proxies))
        return cls(
            proxies=proxies,
            challenge_retry_times=crawler.settings.getint(
                "AMAZON_CHALLENGE_RETRY_TIMES", 2
            ),
        )

    def _next_proxy(self, previous: str | None = None) -> str:
        candidate = next(self._proxy_cycle)
        if len(self.proxies) > 1 and candidate == previous:
            candidate = next(self._proxy_cycle)
        return candidate

    def process_request(self, request: Request, spider: object) -> None:
        previous = request.meta.get("_rotating_proxy")
        proxy_url = self._next_proxy(previous)
        request.meta["proxy"] = proxy_url
        request.meta["_rotating_proxy"] = proxy_url
        logger.debug("Using proxy %s for %s", _redact_proxy(proxy_url), request.url)

    def process_response(
        self, request: Request, response: Response, spider: object
    ) -> Response | Request:
        if not isinstance(response, TextResponse):
            return response

        body = response.body.lower()
        if not any(marker in body for marker in self.challenge_markers):
            return response

        logger.warning(
            "Amazon challenge page detected for %s via %s",
            request.url,
            _redact_proxy(request.meta["_rotating_proxy"]),
        )
        retry = get_retry_request(
            request,
            spider=spider,
            reason="amazon_challenge_page",
            max_retry_times=self.challenge_retry_times,
        )
        return retry or response
