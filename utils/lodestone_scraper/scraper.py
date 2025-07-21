# utils/lodestone_scraper/scraper.py
import aiohttp
from bs4 import BeautifulSoup
from .uris import applicable_uris
from .selectors import load_selectors, DEFAULT_FILES  # centralize default logic here
from .extract import extract_element

class SelectorNotFound(Exception):
    pass

class URIBuilderError(Exception):
    pass

class LodestoneScraper:
    def __init__(self, region="eu", session=None, timeout=15):
        self.region = region
        self.timeout = timeout
        self.session = session  # allows passing an existing aiohttp session for reuse

    @staticmethod
    def list_available_selectors():
        # You can expand this to dynamically read files if you want
        from pathlib import Path
        selector_root = Path(__file__).parent / "selectors"
        selectors = []
        for folder in selector_root.iterdir():
            if folder.is_dir():
                for jsonfile in folder.glob("*.json"):
                    with open(jsonfile, encoding="utf-8") as f:
                        d = json.load(f)
                    for key in d:
                        selectors.append(f"{folder.name}.{jsonfile.stem}.{key}")
        return selectors

    def _parse_selector_string(self, selector: str):
        parts = selector.split(".")
        if len(parts) == 1:
            category = parts[0]
            file = DEFAULT_FILES.get(category, category)
            keys = []
        elif len(parts) == 2:
            category, file = parts
            keys = []
        else:
            category, file, *keys = parts
        return category, file, keys

    async def scrape(self, selector_string, lodestone_id, *extra_ids):
        # Parse selector string
        category, file, keys = self._parse_selector_string(selector_string)

        # Build selector path and URI key
        selector_dict = load_selectors(category, file)
        uri_key = f"{category}/{file}.json"

        # Build the URI
        if uri_key not in applicable_uris:
            raise URIBuilderError(f"No URI template for {uri_key}")

        # Prepare URL
        ids = (str(lodestone_id),) + tuple(str(i) for i in extra_ids)
        url = applicable_uris[uri_key] % ((self.region,) + ids)

        # Download HTML
        session = self.session or aiohttp.ClientSession()
        try:
            async with session.get(url, timeout=self.timeout, headers={"User-Agent": "LodestoneScraper/1.0"}) as resp:
                if resp.status != 200:
                    raise Exception(f"HTTP {resp.status}: Failed to fetch page.")
                html = await resp.text()
        finally:
            if not self.session:
                await session.close()

        # Parse HTML and extract fields
        soup = BeautifulSoup(html, "lxml")
        target = selector_dict
        for key in keys:
            if key not in target:
                raise SelectorNotFound(f"Key '{key}' not found in selector JSON.")
            target = target[key]

        # If you want a specific field, extract just that
        if keys:
            # Only that one entry
            if isinstance(target, dict) and "selector" in target:
                return extract_element(soup, target)
            else:
                # Nested composite
                return {keys[-1]: extract_element(soup, target)}
        else:
            # Extract all top-level entries
            return {field: extract_element(soup, entry) for field, entry in target.items()}
