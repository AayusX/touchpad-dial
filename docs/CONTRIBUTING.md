# Contributing

Thanks for helping! Contributions — code, docs, translations, bug reports, and
hardware-testing reports — are all welcome.

## Code of conduct

Be kind and constructive. Report unacceptable behavior by opening an issue.

## Getting started for developers

```bash
git clone https://github.com/AayusX/touchpad-dial.git
cd touchpad-dial
python3 -m venv .venv
.venv/bin/pip install -e .
```

Run the sanity checks:

```bash
# Import + syntax check of everything
.venv/bin/python3 -c "import creatordial.daemon, creatordial.ui_main; print('ok')"
```

## Project layout

- `creatordial/daemon.py` — daemon entry (plugins registered here)
- `creatordial/core/` — engine, input, gestures, IPC, hardware
- `creatordial/plugins/` — one directory per plugin
- `creatordial/ui/` — the overlay + tray UI
- `docs/` — this documentation

## Style

- Python 3.10+, continue existing patterns (type hints where helpful).
- **No comments unless they explain a non-obvious "why."**
- Imports: stdlib, third-party, local — separated blank line, alphabetic.
- Keep subprocess calls bounded: `capture_output=True, timeout=...`.
- Don't add dependencies casually; prefer stdlib / `libevdev` / PySide6 /
  `subprocess` to external CLIs when reasonable.

## Testing gestures locally

```bash
~/.local/share/creatordial/.venv/bin/python3 \
  ~/.local/share/creatordial/creatordial/debug.py --input
```

This prints live `Rotation CW/CCW`, `click`, `long-press`, and `activation`
events as you move your finger — the fastest way to verify changes.

## Submitting changes

1. Fork the repository.
2. Branch: `git checkout -b feat/short-description`.
3. Commit with a concise message:
   `Add volume percentage readback to UI`.
4. Push and open a PR against `main`.

PR title/description should explain **what** and **why**. Screenshots/GIFs for
UI changes go a long way.

## Bug reports

Use the issue template. Include:

- Distribution + desktop environment (KDE Plasma / GNOME / …).
- Touchpad make/model (from `debug.py`).
- `config.json` if you've modified it.
- Full journal excerpt:
  ```bash
  journalctl --user -u creatordial-daemon --no-pager -n 100
  ```

## What to work on

See the [roadmap](../README.md#-roadmap) in the README. Good first issues:

- Port the installer to other distros
- Settings GUI
- More plugins