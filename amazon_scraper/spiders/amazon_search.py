"""Extract product summaries from permitted Amazon search-result pages."""

from __future__ import annotations

import os
from urllib.parse import urlencode

import scrapy


class AmazonSearchSpider(scrapy.Spider):
    name = "amazon_search"

    def __init__(
        self,
        query: str | None = None,
        pages: int | str = 1,
        domain: str | None = None,
        *args: object,
        **kwargs: object,
    ) -> None:
        super().__init__(*args, **kwargs)
        if not query:
            raise ValueError("Pass a search term with -a query='your search'")

        self.query = query
        self.max_pages = max(1, int(pages))
        configured_domain = os.getenv("AMAZON_DOMAIN", "amazon.in")
        self.domain = (domain or configured_domain).lower().strip()
        if self.domain.startswith(("http://", "https://")):
            raise ValueError("domain must look like amazon.in, without http://")
        self.allowed_domains = [self.domain]

    def start_requests(self):
        params = urlencode({"k": self.query, "page": 1})
        yield scrapy.Request(
            f"https://www.{self.domain}/s?{params}",
            callback=self.parse,
            cb_kwargs={"page": 1},
        )

    def parse(self, response: scrapy.http.Response, page: int):
        products = response.css('div[data-component-type="s-search-result"]')
        if not products:
            self.logger.warning("No product cards found on %s", response.url)

        for product in products:
            asin = product.attrib.get("data-asin", "").strip()
            title = product.css("h2 span::text").get()
            product_url = product.css("h2 a::attr(href)").get()
            whole = product.css("span.a-price-whole::text").get()
            fraction = product.css("span.a-price-fraction::text").get()

            if not asin or not title or not product_url:
                continue

            price = None
            if whole:
                price = whole.strip().rstrip(".,")
                if fraction:
                    price = f"{price}.{fraction.strip()}"

            yield {
                "asin": asin,
                "title": title.strip(),
                "price": price,
                "currency_text": product.css("span.a-price-symbol::text").get(),
                "rating": product.css("span.a-icon-alt::text").get(),
                "review_count": product.css(
                    "span.a-size-base.s-underline-text::text"
                ).get(),
                "url": response.urljoin(product_url),
                "image_url": product.css("img.s-image::attr(src)").get(),
                "search_query": self.query,
                "search_page": page,
            }

        if page >= self.max_pages:
            return

        next_page = response.css("a.s-pagination-next::attr(href)").get()
        if next_page:
            yield response.follow(
                next_page,
                callback=self.parse,
                cb_kwargs={"page": page + 1},
            )
