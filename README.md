# SlingDuel

Local 1v1 arcade shooter built with **pygame**. Two players jump, swing, and pelt each other with bananas across floating platforms. First to reduce the other to 0 HP wins.

## Quick Start
```bash
python3 -m venv venv
source venv/bin/activate           # (Windows: venv\Scripts\activate)
pip install -r requirements.txt
python3 main.py
```


## How to Play

Move / Aim
Each player has their own keys for left/right (move) and up/down (aim). The white target shows the throw direction.

Jump
Low jump to hop between platforms.

Throw Banana
You must first pick up a banana (yellow icon near your hearts = you have one).

Direct hit: 1.0 damage.

Step on splat: 0.5 damage (one time per splat).

Hook / Sling
Fire a hook that sticks to platforms/ceiling.

While attached, holding jump pulls you strongly toward the hook.

If you don’t hold jump, it acts like a swing (Tarzan-style).

Releasing jump while attached detaches the hook.

HUD

Hearts show current health. Half-heart appears for .5 HP.

Banana icon appears if you carry one.

Hook icon appears when hook is off cooldown.

Spawning & Rules

Bananas spawn periodically (with logic to avoid overlaps).

Only one ground banana pickup at a time; others spawn on platforms.

Ground splats are limited; oldest gets removed if over the cap.

Health regen: +0.5 HP to each player every 30 seconds (clamped to max).


## License
This project is licensed under the Creative Commons Attribution-NonCommercial 4.0 International License (CC BY-NC 4.0).  
You are free to share and adapt the code and assets, but **commercial use is strictly prohibited**.  
See the [LICENSE](LICENSE) file for full details.
