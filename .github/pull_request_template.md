name: Pull Request
description: Submit changes to Touchpad Dial
title: "[feat]: "
labels: []
body:
  - type: markdown
    attributes:
      value: |
        Thanks for contributing! Describe what you changed and why.
  - type: textarea
    id: summary
    attributes:
      label: Summary
      description: What does this PR do?
    validations:
      required: true
  - type: textarea
    id: testing
    attributes:
      label: How was it tested
      description: Include commands run, gestures exercised, screenshots/GIFs for UI changes.
    validations:
      required: true
  - type: checkboxes
    id: checks
    attributes:
      label: Checklist
      options:
        - label: Import/syntax check passes on all modified modules
        - label: Existing gesture/plugin behavior unchanged (tested via `debug.py --input`)
        - label: Docs updated if configuration or behavior changed