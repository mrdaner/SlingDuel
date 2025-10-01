# constants.py
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
GROUND_Y = 680
CEILING_Y = -60  # small headroom above visible top before clamping hero
FPS = 60

COLOR_BG = (94, 129, 162)
COLOR_SCORE = (64, 64, 64)

# UI palette (banana inspired)
COLOR_TITLE = (248, 226, 92)
COLOR_ACCENT = (156, 102, 31)
COLOR_MUTED = (246, 236, 200)
COLOR_CALLOUT = (214, 143, 46)
COLOR_WARNING = (207, 61, 33)
OVERLAY_RGBA = (0, 0, 0, 160)

HERO_JUMP_FORCE = -15
GRAVITY_PER_TICK = 1

SCALE = 1/3

# Projectile physics
PROJECTILE_GRAVITY = 0.5      # pixels per frame^2 (tweak to taste)
MAX_PROJECTILE_FALL_SPEED = 18

# Throw velocities
BANANA_THROW_SPEED = 12
HOOK_THROW_BASE_SPEED = 14 * 1.3
HOOK_THROW_SPEED_MULTIPLIER = 1.5

MAX_HEALTH = 5
