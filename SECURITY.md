# Security Policy

## Supported versions

Security fixes are applied to the current release on `main` and the most recent
tagged release.

## Reporting a vulnerability

Please do **not** open a public issue for security problems. Instead, report
privately via GitHub's advisory flow:

1. Go to **Security → Report a vulnerability** (or use
   [this link](https://github.com/AayusX/touchpad-dial/security/advisories/new)).
2. Provide a short description, affected version, impact, and a minimal
   reproduction.

You should receive a response within 3 business days.

## Scope

This project reads raw input devices and can emit virtual keys and run the
installed system CLIs it needs (volume, brightness tools, etc.) as your user.
Security-relevant behaviors:

- The **unix socket** at `/tmp/creatordial.sock` accepts datagrams from any
  local user. It only carries *display* messages (not actions), but is
  unauthenticated — treat it as non-authoritative.
- The **udev rules** grant device access (`0660`) to the `input`, `i2c`, and
  `uinput` groups; only add trusted users to those groups.
- Plugins run `subprocess` (timeout-bounded) and may write sysfs thermal files
  (GPU mode needs root anyway). Do not install untrusted third-party plugins.

## Windows of support

- `main` — active
- Latest tagged release — patch fixes