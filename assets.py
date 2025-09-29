from pathlib import Path
import pygame

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

def get_hero_frames():
    hero_dir = _ASSET_ROOT / "Hero"
    stand = load_image(hero_dir / "Hero_stand.png")
    run = [
        stand,
        load_image(hero_dir / "Hero_run_1.png"),
        load_image(hero_dir / "Hero_run_2.png"),
        load_image(hero_dir / "Hero_run_3.png"),
        load_image(hero_dir / "Hero_run_4.png"),
    ]
    jump = [
        load_image(hero_dir / "Hero_jump_1.png"),
        load_image(hero_dir / "Hero_jump_2.png"),
        load_image(hero_dir / "Hero_jump_3.png"),
    ]
    return stand, run, jump

def get_obstacle_base(kind: str):
    if kind == "banana":
        return load_image(_ASSET_ROOT / "banana.png")
    elif kind == "boss":
        return load_image(_ASSET_ROOT / "boss.png")
    else:
        raise ValueError(f"Unknown obstacle kind: {kind}")
