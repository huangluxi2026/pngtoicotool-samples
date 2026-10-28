# Reproduction result

Run locally on 2026-10-28 with CPython 3.14.7:

```text
Input: sample.png | 128x128 | 466 bytes
Output: sample.ico | 488 bytes
ICO directory entries: 1
Embedded PNG layer: 128x128 | 466 bytes
```

The script verified the PNG chunk CRCs, decompressed RGBA pixel data, one ICO directory entry, and matching embedded dimensions. This records the generated file structure; it does not test browser rendering or operating-system icon selection.
