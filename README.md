Test PNGs for https://github.com/MicroPythonOS/MicroPythonOS/issues/140

All three are PNG color type 6 (8-bit RGBA, non-interlaced):
- hero_lightningpiggy_rgba.png   (80x100) — the original Lightning Piggy hero that failed on-device on MPOS 0.10.0
- hero_lightningpenguin_rgba.png (78x100) — same, penguin variant
- synthetic_rgba_64x64.png       (64x64)  — minimal Pillow-generated reproducer with a real alpha gradient (not palette-collapsible)
