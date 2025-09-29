# assets.py
from pathlib import Path
import pygame
from constants import SCALE

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
    sky = load_image(_ASSET_ROOT / "Background" / "Sky.png")
    ground = load_image(_ASSET_ROOT / "Background" / "Ground.png")
    return sky, ground

def _scale(surf: pygame.Surface) -> pygame.Surface:
    if SCALE == 1:
        return surf
    return pygame.transform.rotozoom(surf, 0, SCALE)

def get_hero_frames():
    hero_dir = _ASSET_ROOT / "Hero"

    stand = _scale(load_image(hero_dir / "Hero_stand.png"))
    run = [
        stand,
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

def get_target():
    surf = pygame.image.load(str(_ASSET_ROOT / "Target.png")).convert_alpha()
    return _scale(surf)

def get_heart():
    surf = pygame.image.load(str(_ASSET_ROOT / "Heart.png")).convert_alpha()
    return _scale(surf)

def get_heart_half():
    surf = pygame.image.load(str(_ASSET_ROOT / "Heart_2.png")).convert_alpha()
    return _scale(surf)

def get_banana_image():
    return _scale(load_image(_ASSET_ROOT / "Banana.png"))

def get_banana_splashed() -> pygame.Surface:
    surf = pygame.image.load(str(_ASSET_ROOT / "Banana_squashed.png")).convert_alpha()
    return _scale(surf)

def get_hook_image() -> pygame.Surface:
    return _scale(load_image(_ASSET_ROOT / "Hook.png"))

def get_floor_images() -> list[pygame.Surface]:
    """Return Floor_1..4 surfaces, first scaled by SCALE, then enlarged by +50%."""
    floors = []
    floor_dir = _ASSET_ROOT / "Floor"
    for i in (1, 2, 3, 4):
        p = floor_dir / f"Floor_{i}.png"
        if p.exists():
            base = _scale(load_image(p))
            bigger = pygame.transform.rotozoom(base, 0, 1.5)  # +50%
            floors.append(bigger)
    return floors
