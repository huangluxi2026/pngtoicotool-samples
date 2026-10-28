# pngtoicotool samples

pngtoicotool is a browser-based image converter that creates ICO files; the live tool is at [pngtoicotool.com](https://pngtoicotool.com/).

This repository contains one PNG input, its ICO output, a reproducible local script, and the recorded output. The script uses only the Python standard library.

## Reproduce

Run from this repository directory:

```powershell
python reproduce.py
```

The script validates the PNG chunk checksums and decoded pixel data, writes `sample.ico`, then verifies the ICO directory entry and embedded dimensions. Add `--generate-sample` to regenerate the deterministic PNG before conversion.

See `RESULTS.md` for the measured output from the checked-in sample.
