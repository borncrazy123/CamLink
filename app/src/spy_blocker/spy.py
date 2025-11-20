import json
import re
from pathlib import Path
from typing import List, Dict, Any
import sys


def _load_mac_json(json_path: Path = None) -> Dict[str, Any]:
    """Load mac.json and normalize keys to 8-hex-digit prefix (4 bytes).

    Returns a map: canonical_prefix (8 hex chars, uppercase) -> value
    """
    if json_path is None:
        json_path = Path(__file__).parent / 'mac.json'

    if not json_path.exists():
        return {}

    try:
        with json_path.open('r', encoding='utf-8') as f:
            raw = json.load(f)
            # print("raw:", raw)
    except Exception:
        print("Failed to load mac.json")
        return {}

    out = {}
    for item in raw:
        out.update(item) 

    return out


# load mac.json once into memory (prefix -> value)
MAC_PREFIX_MAP: Dict[str, Any] = _load_mac_json()


def lookup_macs_from_string(mac_list_string: str) -> List[Dict[str, Any]]:
    """Given a comma-separated MAC string, lookup each MAC's 4-byte prefix in mac.json.

    Args:
        mac_list_string: 'F4-E1-FC-01-02-09,F4-EA-B5-F1-21-C2'

    Returns:
        A list of dicts: [{ 'mac': original_mac, 'prefix': 'F4E1FC01', 'value': matched_value }, ...]
        If no match for a mac, it will be omitted from the result.
    """
    if not mac_list_string:
        return []

    mapping = MAC_PREFIX_MAP
    if not mapping:
        return []

    parts = [p.strip() for p in mac_list_string.split(',') if p.strip()]
    results: List[Dict[str, Any]] = []

    for mac in parts:
        if len(mac) < 8:
            results.append({'mac': mac, 'prefix': mac, 'value': "MAC length too short"})
            continue
        prefix = mac[:8]
        if prefix in mapping:
            results.append({'mac': mac, 'prefix': prefix, 'value': mapping[prefix]})
        else:
            results.append({'mac': mac, 'prefix': prefix, 'value': "Unknown MAC"})

    return results

sys.argv = ["spy.py", "B8-7C-F2-AB-12-09,28-6F-B9-F1-21-C2,00-7C-F2-AB-12-09,00-7C"]
if __name__ == '__main__':
    # simple CLI for manual testing
    import sys

    if len(sys.argv) > 1:
        inp = sys.argv[1]
    else:
        inp = input('输入逗号分隔的 MAC 列表: ').strip()

    matches = lookup_macs_from_string(inp)
    print(json.dumps(matches, ensure_ascii=False, indent=2))

