# utils/lodestone_scraper/extract.py
import re

def extract_element(soup, selector_dict):
    """
    Recursively extract data from soup using selector_dict rules.
    Supports generic selectors and field ops custom logic.
    """
    # Field Ops Special Case (header-based and none of that nth child nonsense)
    if selector_dict.get("_field_ops_header"):
        return extract_nonstatic_detail(
            soup,
            selector_dict["_field_ops_header"],
            selector_dict.get("_data_index", 0)
        )
    
    # Normal Extraction
    if "selector" in selector_dict:
        css_selector = selector_dict["selector"]
        elements = soup.select(css_selector)

        if not elements:
            return [] if selector_dict.get("multiple") else None

        # Multiple
        if selector_dict.get("multiple"):
            results = []
            for el in elements:
                val = _extract_from_element(el, selector_dict)
                if "regex" in selector_dict and val is not None:
                    match = re.search(selector_dict["regex"], val)
                    results.append(match.groupdict() if match else None)
                else:
                    results.append(val)
            return results

        # Single value
        val = _extract_from_element(elements[0], selector_dict)
        if "regex" in selector_dict and val is not None:
            match = re.search(selector_dict["regex"], val)
            return match.groupdict() if match else None
        return val

    # Nested dict helper, recursive innit (FC crest layers etc)
    result = {}
    for key, subdict in selector_dict.items():
        result[key] = extract_element(soup, subdict)
    return result

def _extract_from_element(element, selector_dict):
    """
    Helper: extracts attribute or text from a single BeautifulSoup element.
    """
    if "attribute" in selector_dict:
        return element.get(selector_dict["attribute"])
    return element.get_text(strip=True)

def extract_nonstatic_detail(soup, header_name: str, data_index: int):
    """
    Finds a field ops section by heading text and returns the Nth div's text from its data block.
    - header_name: e.g. "Bozjan Southern Front", "The Forbidden Land, Eureka", "Occult Crescent"
    - data_index: 0 for Level, 1 for Current, 2 for To Next, etc (per block structure)
    """
    for heading in soup.select("h3.heading-md"):
        if header_name.lower() in heading.get_text(strip=True).lower():
            block = heading.find_next_sibling("div", class_="character__job__list")
            if block:
                values = [div.get_text(strip=True) for div in block.find_all("div", recursive=False)]
                if 0 <= data_index < len(values):
                    return values[data_index]
                else:
                    return None  # Index out of range
    return None  # Not found
