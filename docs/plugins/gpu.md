# GPU Plugin

Reports GPU utilization and switches ASUS laptop power modes.

| Gesture | Action |
|---|---|
| Rotate CW | Silent → Balanced → Performance |
| Rotate CCW | Performance → Balanced → Silent |

### Information shown

- Live GPU utilization (%) from `nvidia-smi`
- Temperature, VRAM usage, power draw (in the UI details)

### Power-mode switching

Switches the ASUS thermal policy file:

```
/sys/devices/platform/asus-nb-wmi/throttle_thermal_policy
 0 = silent | 1 = balanced | 2 = performance
```

> This sysfs file is root-writable only. If the write is denied, the plugin
> logs it and continues to report GPU utilization. On non-ASUS hardware the
> mode buttons simply do nothing — a clean no-op.

On Intel-only laptops where `nvidia-smi` is absent, utilization reports `0`
and settings remain available.