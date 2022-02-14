from urllib.parse import urlparse

from pb_design_parsers import (browser, creative, designcuts, envanto, schemas,
                               yellowimgs, youworkforthem)


def collect_name_and_cat(items: list[schemas.item]) -> list[schemas.item]:
    brwsr = browser.get()
    for item in items:
        market_domain = urlparse(item.url).netloc
        market_domain = market_domain[4:] if market_domain[:4] == 'www.' else market_domain
        if market_domain == 'creativemarket.com':
            try:
                item.name, item.cattegories = creative.parse_product_info(brwsr, item.url)
            except Exception:
                raise ValueError(f"Can't parse {item.url}")
        elif market_domain == 'elements.envato.com':
            try:
                item.name, item.cattegories = envanto.parse_product_info(brwsr, item.url)
            except Exception:
                raise ValueError(f"Can't parse {item.url}")
        elif market_domain == 'youworkforthem.com':
            try:
                item.name, item.cattegories = youworkforthem.parse_product_info(brwsr, item.url)
            except Exception:
                raise ValueError(f"Can't parse {item.url}")
        elif market_domain == 'yellowimages.com':
            try:
                item.name, item.cattegories = yellowimgs.parse_product_info(brwsr, item.url)
            except Exception:
                raise ValueError(f"Can't parse {item.url}")
        elif market_domain == 'designcuts.com':
            try:
                item.name, item.cattegories = designcuts.parse_product_info(brwsr, item.url)
            except Exception:
                raise ValueError(f"Can't parse {item.url}")
    return items
