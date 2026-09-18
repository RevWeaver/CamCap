# CamCap

A portable, appliance-like digital recorder that turns a Raspberry Pi into a
purpose-built camcorder front-end for a Sony HDR-FX7. Built so it can be
powered on and used like a real camcorder — no terminal required — for
filming hands-on work (e.g. car repair) solo for YouTube.

## Why this exists

The HDR-FX7 only outputs 1080i over HDMI, and YouTube wants clean 1080p.
Deinterlacing the capture is the entire point of this pipeline, not a
nice-to-have. 4K is explicitly out of scope.

## Signal path

```
Sony HDR-FX7 (1080i, HDMI) -> Elgato Cam Link 4K (USB) -> Raspberry Pi
    -> ffmpeg (yadif deinterlace, libx264 "veryfast") -> USB SSD (MKV)
```

- Capture device is resolved via the Cam Link's persistent
  `/dev/v4l/by-id/...` path (`camera.py`), not a raw `/dev/videoN` index,
  since those renumber across reboots/USB resets.
- Recording writes to a `.tmp` file and is atomically renamed to its final
  name on a clean stop, so a crash or power loss never leaves a half-written
  file masquerading as a finished recording.
- A live low-res preview (deinterlace skipped, scaled down) runs on the
  touchscreen/HDMI display so framing can be checked in the moment; it stops
  while a recording is active ("one reader at a time" — the capture device
  can only support a single simultaneous consumer reliably).

## Storage

`DriveManager` (`drivemanager.py`) treats the destination as "any compatible
USB SSD," not a drive assumed to always be labeled `CAMCAP`:

- Detects, mounts, and verifies a drive is actually *writable* (not just
  mounted) before recording is allowed to start.
- Auto-fixes ownership on a freshly formatted/foreign drive once, the way a
  camera preps a memory card, rather than requiring manual `chown`.
- Lays out `CamCap/{DCIM/100CAMCAP,LOGS,CONFIG}` plus a `.camcap_drive`
  marker on first use.
- Fails with a clear, honest error instead of crashing or silently reporting
  success when a drive can't be made to work.

## App

`ui/main_window.py` is a PyQt5 touch UI (Camera / Review / Playback screens)
running headless via the `eglfs` platform plugin — no X11/Wayland desktop
required. `ui/playback.py` handles listing and replaying recordings from the
drive.

## Boot / lifecycle

Runs as a systemd service (`camcap.service`) enabled for
`multi-user.target`, so it starts automatically on boot like a real
appliance, independent of any desktop session or login. SSH stays available
separately for backend access. `main.py` handles SIGTERM/SIGINT so
`systemctl stop`, `reboot`, and `poweroff` all finalize an in-progress
recording cleanly instead of leaving it stranded as a `.tmp` file — this
only covers graceful shutdowns, not an abrupt power cut.

## Known hardware quirk

The Elgato Cam Link 4K's UVC driver can wedge under heavy rapid open/close
cycling (`Failed to resubmit video URB` in `dmesg`, capture stalls at
`frame=0`). Fix is a USB-level reset (toggle
`/sys/bus/usb/devices/<bus-port>/authorized` off/on) or a physical
unplug/replug — not something the app tries to paper over with retries.

## Status

Active development happens on `live-status`; `master` predates the storage
reliability refactor and is stale.

## Not yet built

- Dedicated small on-camera display (touchscreen mounted on the accessory
  rail) — currently developed/tested against HDMI output.
- Physical power button wired to trigger a clean shutdown.
