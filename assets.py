# assets.py
from pathlib import Path
import pygame
from constants import SCALE  # e.g., SCALE = 1/3

_ASSET_ROOT = Path(__file__).resolve().parent / "graphics"
_font_cache = {}
_image_cache = {}

def load_image(path: Path):
    key = str(path)
    if key not in _image_cache:
        _image_cache[key] = pygame.image.load(str(path)).convert_alpha()
    return _image_cache[key]

def get_font(name="ByteBounce.ttf", size=100):
    key = (name, size)
    if key not in _font_cache:
        _font_cache[key] = pygame.font.Font(str(_ASSET_ROOT / name), size)
    return _font_cache[key]

def get_background():
    # Keep backgrounds unscaled so they match your screen fill.
    sky = load_image(_ASSET_ROOT / "Background" / "Sky.png")
    ground = load_image(_ASSET_ROOT / "Background" / "Ground.png")
    return sky, ground

def _scale(surf: pygame.Surface) -> pygame.Surface:
    # Use rotozoom for nice downscaling; skip work if SCALE==1.
    if SCALE == 1:
        return surf
    return pygame.transform.rotozoom(surf, 0, SCALE)

def get_hero_frames():
    hero_dir = _ASSET_ROOT / "Hero"

    stand = _scale(load_image(hero_dir / "Hero_stand.png"))
    run = [
        stand,  # already scaled
        _scale(load_image(hero_dir / "Hero_run_1.png")),
        _scale(load_image(hero_dir / "Hero_run_2.png")),
        _scale(load_image(hero_dir / "Hero_run_3.png")),
        _scale(load_image(hero_dir / "Hero_run_4.png")),
    ]
    jump = [
        _scale(load_image(hero_dir / "Hero_jump_1.png")),
        _scale(load_image(hero_dir / "Hero_jump_2.png")),
        _scale(load_image(hero_dir / "Hero_jump_3.png")),
    ]
    throw = [
        _scale(load_image(hero_dir / "Hero_throw_1.png")),
        _scale(load_image(hero_dir / "Hero_throw_2.png")),
    ]
    return stand, run, jump, throw

def get_obstacle_base(kind: str):
    if kind == "banana":
        base = load_image(_ASSET_ROOT / "banana.png")
    elif kind == "boss":
        base = load_image(_ASSET_ROOT / "boss.png")
    else:
        raise ValueError(f"Unknown obstacle kind: {kind}")
    return _scale(base)

def get_target():
    surf = pygame.image.load(str(_ASSET_ROOT / "Target.png")).convert_alpha()
    return _scale(surf)

def get_heart():
    surf = pygame.image.load(str(_ASSET_ROOT / "Heart.png")).convert_alpha()
    return _scale(surf)
