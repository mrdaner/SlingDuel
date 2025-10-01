"""Helpers for loading, normalising, and persisting configurable key bindings."""
import json
import os
import pygame

DEFAULT_KEY_NAMES = {
    "player1": {
        "left": "a",
        "right": "d",
        "up": "w",
        "down": "s",
        "throw": "left shift",
        "sling": "v",
        "jump": "space",
    },
    "player2": {
        "left": "l",
        "right": "'",
        "up": "p",
        "down": ";",
        "throw": "k",
        "sling": "return",
        "jump": "right shift",
    },
}
_KEYFILE = "keys.json"

def _to_keycode(name: str) -> int:
    if not isinstance(name, str) or not name:
        raise ValueError("Empty key name")
    s = name.strip().lower()
    # pygame converts common strings like 'a', 'space', 'left', 'f1', etc.
    return pygame.key.key_code(s)

def _normalize_controls(raw: dict) -> dict:
    """Convert a ``{action: keyname}`` mapping into pygame keycodes."""
    out = {}
    for action, keyname in raw.items():
        out[action] = _to_keycode(str(keyname))
    return out


def _to_name(keycode: int) -> str:
    try:
        return pygame.key.name(int(keycode))
    except Exception:
        return "unknown"

def load_controls() -> tuple[dict, dict]:
    """Return ``(player1, player2)`` action→keycode mappings.

    Falls back to defaults when the configuration file is missing or invalid.
    """
    data = None
    if os.path.exists(_KEYFILE):
        try:
            with open(_KEYFILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = None

    if not isinstance(data, dict):
        data = DEFAULT_KEY_NAMES

    p1_raw = data.get("player1", DEFAULT_KEY_NAMES["player1"])
    p2_raw = data.get("player2", DEFAULT_KEY_NAMES["player2"])

    try:
        p1 = _normalize_controls(p1_raw)
        p2 = _normalize_controls(p2_raw)
    except Exception:
        p1 = _normalize_controls(DEFAULT_KEY_NAMES["player1"])
        p2 = _normalize_controls(DEFAULT_KEY_NAMES["player2"])

    return p1, p2


def save_controls(player1: dict, player2: dict) -> None:
    """Persist the given action→keycode maps to ``keys.json``."""
    data = {
        "player1": {action: _to_name(code) for action, code in player1.items()},
        "player2": {action: _to_name(code) for action, code in player2.items()},
    }
    try:
        with open(_KEYFILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def default_controls() -> tuple[dict, dict]:
    """Return freshly normalised copies of the shipped default bindings."""
    return (
        _normalize_controls(DEFAULT_KEY_NAMES["player1"]),
        _normalize_controls(DEFAULT_KEY_NAMES["player2"]),
    )
