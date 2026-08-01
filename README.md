# Pin Laser

A small Windows tray app that draws a glowing laser pointer (with a fading
trail) on top of the screen, following your mouse cursor. It is purely visual:
all mouse clicks pass through to the apps underneath.

By default the fading trail only appears while you **hold the mouse button**
(dot always follows), so you can sweep-highlight an area on the screen. All
behavior is configurable from the tray menu → **Settings…**.

## Install

```
py -m pip install -e .
```

Or, if you prefer not to install it:

```
py -m pip install -r requirements.txt
```

## Run

```
pinlaser
```

Or without installing:

```
py main.py
```

## Usage

- Press `Ctrl+Shift+L` to show/hide the laser pointer.
- Right-click the tray icon for the same options, **Settings…** and **Quit**.
- Left-clicking the tray icon also toggles the laser.
- **Settings…** lets you pick:
  - Trail behavior: *Only while clicking* (default) or *Always show trail*.
  - The trigger button (*Left / Right / Either*) when on-click mode is active.
  - Laser color, glow size, and trail length.
  - Settings are saved automatically and restored next launch.

## Notes

- The laser only renders while the overlay is shown; normal desktop use is
  unaffected until you toggle it on.
- On very high-DPI / mixed-DPI multi-monitor setups the dot is placed using
  each monitor's scale factor, so it tracks the cursor correctly everywhere.
