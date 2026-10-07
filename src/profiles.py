"""Profile response data derived from local assets and emulator policy."""

import datetime
import json
import re
import time
from functools import lru_cache


def noble_dates():
    # Refresh on every response so every account remains subscribed.
    return 946684800, int(time.time()) + 10 * 365 * 24 * 60 * 60


def utc_date(timestamp):
    return datetime.datetime.fromtimestamp(timestamp, datetime.UTC).isoformat().replace("+00:00", "Z")


def all_emblems(manifest_path):
    """Use the installed manifest; never guess asset IDs or download assets."""
    if not manifest_path.is_file():
        return ()
    stat = manifest_path.stat()
    return _emblems(manifest_path, stat.st_mtime_ns, stat.st_size)


@lru_cache(maxsize=2)
def _emblems(manifest_path, modified, size):
    with manifest_path.open(encoding="utf-8") as stream:
        entries = json.load(stream).get("m_Entries", [])
    prefix = "uiexternal/ui/common/textures/icon/emblem/icon_"
    return tuple(sorted({entry["Name"][len(prefix):] for entry in entries
                         if isinstance(entry, dict)
                         and isinstance(entry.get("Name"), str)
                         and re.fullmatch(re.escape(prefix) + r"emblem_[a-z]+\d+_\d+", entry["Name"])}))


def add_all_emblems(top_data, manifest_path):
    emblems = all_emblems(manifest_path)
    if not emblems:
        return
    factions = {entry.get("CharacterId"): entry.get("Faction")
                for entry in top_data.get("characterMaster", [])}
    # Preserve unrelated stamps and deck data. Category 2 is Wappen/emblems.
    emblem_ids = set(emblems)
    for field in ("stampBadgeMaster", "stampBadge"):
        top_data[field] = [entry for entry in top_data.get(field, [])
                           if entry.get("Id") not in emblem_ids]
    for order, emblem_id in enumerate(emblems):
        character = re.fullmatch(r"emblem_(pl\d+)_\d+", emblem_id)
        faction = factions.get(character.group(1)) if character else None
        # The client filters tabs by SubCategory. Its fallback is Other (4).
        subcategory = faction if faction in (1, 2, 3) else 4
        top_data["stampBadgeMaster"].append({
            "Id": emblem_id, "Category": 2, "Number": order,
            "Type": 0, "SubCategory": subcategory})
        top_data["stampBadge"].append({
            "Id": emblem_id, "Category": 2, "Type": 0,
            "SourceId": "uiexternal/ui/common/textures/icon/emblem/icon_" + emblem_id,
            "SortOrder": order, "SubCategory": subcategory, "IsUse": True})
