# SlingDuel

Local 1v1 arcade shooter built with **pygame**. Two players jump, swing, and pelt each other with bananas across floating platforms. First to reduce the other to 0 HP wins.

- **New:** in-game key remapping (`K`) and a test mode toggle (`T`), plus trajectory/sandbox overlays and a pause menu.

## Quick Start
```bash
python3 -m venv venv
source venv/bin/activate           # (Windows: venv\Scripts\activate)
pip install -r requirements.txt
python3 main.py
```

Press **ESC** to pause, **K** to remap controls, **T** to toggle test overlays.


## How to Play

### Default Controls

| Action        | Player 1 (Left) | Player 2 (Right) |
|---------------|-----------------|------------------|
| Move Left     | A               | L                |
| Move Right    | D               | ' (Apostrophe)   |
| Aim Up        | W               | P                |
| Aim Down      | S               | ;                |
| Jump          | Space           | Right Shift      |
| Hook / Sling  | V               | Enter / Return   |
| Throw Banana  | Left Shift      | K                |

> Press **K** on the start screen or pause menu to remap any binding in-game.

### Movement & Combat

- **Move / Aim:** Left/right moves, up/down rotates the aim reticle (white dot).
- **Jump:** Low arc for hopping platforms.
- **Throw Banana:** Grab a banana first (icon near hearts). Direct hits deal **1.0 HP**, splats deal **0.5 HP** once.
- **Grapple Hook:** Fire upward or to a surface. Hold jump to reel in, release to swing. Let go of hook to detach—hook and test-mode trajectories are shown as dotted arcs when available.

### HUD & Spawns

- Hearts show health (half-heart = 0.5 HP). Both players regenerate **+0.5 HP** every 30 seconds up to max.
- Banana icon lights up when you have ammo.
- Hook icon appears when the grapple is off cooldown.
- Bananas spawn up to **3** at a time. Ground bananas unlock only after several platform spawns to keep play vertical.
- Health pickups spawn on upper platforms only when someone is **≤3 HP**.

### Pause & Test Mode

- **ESC** pauses the match: resume (ESC), return to menu (M), open remap screen (K), or toggle test mode (T).
- Test mode grants infinite bananas to both players and overlays hitboxes plus banana/hook trajectory previews for sandbox testing.


## License
This project is licensed under the Creative Commons Attribution-NonCommercial 4.0 International License (CC BY-NC 4.0).  
You are free to share and adapt the code and assets, but **commercial use is strictly prohibited**.  
See the [LICENSE](LICENSE) file for full details.
