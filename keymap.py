# keymap.py
import json
import os
import pygame

_DEFAULTS = {
    "player1": {"left":"a","right":"d","up":"w","down":"s","throw":"f","sling":"r","jump":"c"},
    "player2": {"left":"j","right":"l","up":"i","down":"k","throw":"h","sling":"u","jump":"n"},
}
_KEYFILE = "keys.json"

def _to_keycode(name: str) -> int:
    if not isinstance(name, str) or not name:
        raise ValueError("Empty key name")
    s = name.strip().lower()
    # pygame converts common strings like 'a', 'space', 'left', 'f1', etc.
    return pygame.key.key_code(s)

def _normalize_controls(raw: dict) -> dict:
    """Convert a dict of {action: 'keyname'} into {action: pygame.K_*}."""
    out = {}
    for action, keyname in raw.items():
        out[action] = _to_keycode(str(keyname))
    return out

def load_controls() -> tuple[dict, dict]:
    """Return (p1_controls, p2_controls) mapping actions → pygame keycodes.
       Falls back to defaults if file is missing/invalid.
    """
    data = None
    if os.path.exists(_KEYFILE):
        try:
            with open(_KEYFILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = None

    if not isinstance(data, dict):
        data = _DEFAULTS

    p1_raw = data.get("player1", _DEFAULTS["player1"])
    p2_raw = data.get("player2", _DEFAULTS["player2"])

    try:
        p1 = _normalize_controls(p1_raw)
        p2 = _normalize_controls(p2_raw)
    except Exception:
        p1 = _normalize_controls(_DEFAULTS["player1"])
        p2 = _normalize_controls(_DEFAULTS["player2"])

    return p1, p2
