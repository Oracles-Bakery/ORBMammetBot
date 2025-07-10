from pathlib import Path
import json

# Central place to update if your structure changes
SELECTOR_ROOT = Path(__file__).parent / "selectors"

DEFAULT_FILES = {
    "profile": "character",
    "freecompany": "freecompany",
    "pvpteam": "pvpteam",
    "search": "character",
    # Add more as needed
}

def load_selectors(category: str, filename: str) -> dict:
    """
    Loads the selector dict for a given category/folder and filename.
    """
    file_path = SELECTOR_ROOT / category / f"{filename}.json"
    if not file_path.exists():
        raise FileNotFoundError(f"Selector file not found: {file_path}")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Selector file {file_path} is not valid JSON: {e}")

def list_categories() -> list:
    """
    Lists all categories (subfolders) in selectors/.
    """
    return [p.name for p in SELECTOR_ROOT.iterdir() if p.is_dir()]

def list_files(category: str) -> list:
    """
    Lists all .json files in a given category.
    """
    folder = SELECTOR_ROOT / category
    if not folder.exists():
        raise FileNotFoundError(f"Category folder not found: {category}")
    return [f.stem for f in folder.glob("*.json")]

def list_keys(category: str, filename: str) -> list:
    """
    Lists all top-level keys in the specified selector file.
    """
    sel = load_selectors(category, filename)
    return list(sel.keys())
