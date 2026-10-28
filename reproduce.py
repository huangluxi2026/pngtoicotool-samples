#!/usr/bin/env python3
"""Generate a deterministic PNG sample and wrap it in a one-entry ICO file."""

from __future__ import annotations

import argparse
import math
import platform
import struct
import sys
import zlib
from pathlib import Path


HERE = Path(__file__).resolve().parent
PNG_PATH = HERE / "sample.png"
ICO_PATH = HERE / "sample.ico"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def png_chunk(kind: bytes, data: bytes) -> bytes:
    body = kind + data
    return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)


def make_sample_png(path: Path, size: int = 128) -> None:
    rows = bytearray()
    center = (size - 1) / 2
    radius = size * 0.42
    for y in range(size):
        rows.append(0)  # PNG filter: None
        for x in range(size):
            dx, dy = x - center, y - center
            distance = math.hypot(dx, dy)
            if distance <= radius:
                rgba = (31, 78, 155, 255)
            else:
                rgba = (0, 0, 0, 0)

            # A simple white conversion mark made from two bars and an arrow head.
            if size * 0.30 <= x <= size * 0.68 and size * 0.43 <= y <= size * 0.57:
                rgba = (255, 255, 255, 255)
            if size * 0.57 <= x <= size * 0.70 and abs(y - center) <= (x - size * 0.57) * 0.8:
                rgba = (255, 255, 255, 255)
            rows.extend(rgba)

    ihdr = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)
    data = PNG_SIGNATURE + png_chunk(b"IHDR", ihdr) + png_chunk(b"IDAT", zlib.compress(bytes(rows), 9)) + png_chunk(b"IEND", b"")
    path.write_bytes(data)


def png_dimensions(data: bytes) -> tuple[int, int]:
    if not data.startswith(PNG_SIGNATURE) or data[12:16] != b"IHDR":
        raise ValueError("Input is not a PNG with an IHDR header")
    return struct.unpack(">II", data[16:24])


def validate_sample_png(data: bytes) -> tuple[int, int]:
    width, height = png_dimensions(data)
    offset = 8
    compressed = bytearray()
    saw_end = False
    while offset < len(data):
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        kind = data[offset + 4 : offset + 8]
        chunk_data = data[offset + 8 : offset + 8 + length]
        stored_crc = struct.unpack(">I", data[offset + 8 + length : offset + 12 + length])[0]
        if (zlib.crc32(kind + chunk_data) & 0xFFFFFFFF) != stored_crc:
            raise ValueError(f"PNG {kind.decode('ascii', 'replace')} CRC check failed")
        if kind == b"IHDR" and (chunk_data[8:] != bytes((8, 6, 0, 0, 0))):
            raise ValueError("Sample PNG must use non-interlaced RGBA with standard compression/filter methods")
        if kind == b"IDAT":
            compressed.extend(chunk_data)
        if kind == b"IEND":
            saw_end = True
            offset += length + 12
            break
        offset += length + 12
    if not saw_end or offset != len(data):
        raise ValueError("PNG chunk stream is incomplete or has trailing data")
    pixels = zlib.decompress(bytes(compressed))
    stride = width * 4
    if len(pixels) != height * (stride + 1):
        raise ValueError("Decoded PNG byte count does not match its RGBA dimensions")
    if any(pixels[row * (stride + 1)] != 0 for row in range(height)):
        raise ValueError("Sample PNG contains an unsupported row filter")
    return width, height


def write_ico_from_png(png_path: Path, ico_path: Path) -> tuple[int, int, int]:
    png_data = png_path.read_bytes()
    width, height = png_dimensions(png_data)
    if width != height or not (1 <= width <= 256):
        raise ValueError("The sample ICO supports square PNG images from 1 to 256 pixels")

    encoded_dimension = 0 if width == 256 else width
    directory = struct.pack(
        "<BBBBHHII",
        encoded_dimension,
        encoded_dimension,
        0,  # palette colors
        0,  # reserved
        1,  # color planes
        32,  # bits per pixel
        len(png_data),
        22,  # ICONDIR (6 bytes) + one ICONDIRENTRY (16 bytes)
    )
    ico_data = struct.pack("<HHH", 0, 1, 1) + directory + png_data
    ico_path.write_bytes(ico_data)

    reserved, image_type, count = struct.unpack("<HHH", ico_data[:6])
    entry_width, entry_height, _, _, _, _, image_size, image_offset = struct.unpack("<BBBBHHII", ico_data[6:22])
    embedded = ico_data[image_offset : image_offset + image_size]
    decoded_width, decoded_height = validate_sample_png(embedded)
    source_width, source_height = validate_sample_png(png_data)
    if reserved != 0 or image_type != 1 or count != 1 or embedded != png_data:
        raise ValueError("ICO directory or embedded PNG validation failed")
    if (entry_width or 256, entry_height or 256) != (decoded_width, decoded_height):
        raise ValueError("ICO directory dimensions do not match the embedded PNG")
    if (source_width, source_height) != (decoded_width, decoded_height):
        raise ValueError("Embedded PNG dimensions do not match the input PNG")
    return decoded_width, decoded_height, count


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generate-sample", action="store_true", help="regenerate the deterministic sample.png first")
    args = parser.parse_args()

    if args.generate_sample or not PNG_PATH.exists():
        make_sample_png(PNG_PATH)
    width, height, layers = write_ico_from_png(PNG_PATH, ICO_PATH)
    print(f"Python: {platform.python_implementation()} {platform.python_version()}")
    print(f"Input: {PNG_PATH.name} | {width}x{height} | {PNG_PATH.stat().st_size} bytes")
    print(f"Output: {ICO_PATH.name} | {ICO_PATH.stat().st_size} bytes")
    print(f"ICO directory entries: {layers}")
    print(f"Embedded PNG layer: {width}x{height} | {PNG_PATH.stat().st_size} bytes")


if __name__ == "__main__":
    main()
