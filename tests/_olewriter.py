"""Minimal pure-Python OLE2 / Compound File Binary (CFB) writer for tests.

olefile is read-only, so to exercise the parser end-to-end we synthesize a real,
valid OLE2 file here. Small streams (<4096 bytes) are stored in the mini-stream
via the mini-FAT, exactly like Altium files store their records. This is a
test-only helper, not part of the shipped package.
"""

from __future__ import annotations

import struct
from pathlib import Path

SECTOR = 512
MINI = 64
FREESECT = 0xFFFFFFFF
ENDOFCHAIN = 0xFFFFFFFE
FATSECT = 0xFFFFFFFD
NOSTREAM = 0xFFFFFFFF


def _pad(data: bytes, size: int) -> bytes:
    if len(data) % size:
        data += b"\x00" * (size - (len(data) % size))
    return data


def _dir_entry(
    name: str,
    obj_type: int,
    start_sector: int,
    stream_size: int,
    child: int = NOSTREAM,
    left: int = NOSTREAM,
    right: int = NOSTREAM,
) -> bytes:
    name_utf16 = name.encode("utf-16-le")
    name_field = name_utf16 + b"\x00" * (64 - len(name_utf16))
    name_len = len(name_utf16) + 2  # include null terminator
    return struct.pack(
        "<64sHBBIII16sIQQIQ",
        name_field,
        name_len,
        obj_type,
        1,  # color: black
        left,
        right,
        child,
        b"\x00" * 16,  # CLSID
        0,  # state bits
        0,  # creation time
        0,  # modified time
        start_sector,
        stream_size,
    )


def write_ole(path: str | Path, streams: dict[str, bytes]) -> None:
    """Write `streams` (name -> bytes) as a valid OLE2 file with mini-FAT."""

    names = list(streams)

    # --- build mini stream + mini FAT ---
    mini_fat: list[int] = []
    mini_stream = bytearray()
    stream_meta: list[tuple[str, int, int]] = []  # (name, start_mini_sector, size)
    for name in names:
        data = streams[name]
        size = len(data)
        start = len(mini_fat)
        n_mini = max(1, (size + MINI - 1) // MINI)
        for i in range(n_mini):
            mini_fat.append(ENDOFCHAIN if i == n_mini - 1 else start + i + 1)
        mini_stream += _pad(data, MINI)
        stream_meta.append((name, start, size))

    mini_stream = bytes(mini_stream)
    mini_container_sectors = max(1, (len(mini_stream) + SECTOR - 1) // SECTOR)

    # --- sector layout ---
    # 0: FAT  1: directory  2: mini-FAT  3..: mini-stream container
    fat_sector = 0
    dir_sector = 1
    minifat_sector = 2
    mini_start = 3
    total_sectors = 3 + mini_container_sectors

    # --- FAT ---
    fat = [FREESECT] * (SECTOR // 4)
    fat[fat_sector] = FATSECT
    fat[dir_sector] = ENDOFCHAIN
    fat[minifat_sector] = ENDOFCHAIN
    for i in range(mini_container_sectors):
        sec = mini_start + i
        fat[sec] = ENDOFCHAIN if i == mini_container_sectors - 1 else sec + 1
    fat_bytes = b"".join(struct.pack("<I", v) for v in fat)

    # --- mini-FAT sector ---
    minifat_full = mini_fat + [FREESECT] * ((SECTOR // 4) - len(mini_fat))
    minifat_bytes = b"".join(struct.pack("<I", v) for v in minifat_full)

    # --- directory: root + one entry per stream (degenerate right-chain tree) ---
    entries = []
    root_child = 1 if names else NOSTREAM
    entries.append(
        _dir_entry("Root Entry", 5, mini_start, len(mini_stream), child=root_child)
    )
    for idx, (name, start, size) in enumerate(stream_meta):
        right = (idx + 2) if idx + 1 < len(stream_meta) else NOSTREAM
        entries.append(_dir_entry(name, 2, start, size, right=right))
    dir_bytes = _pad(b"".join(entries), SECTOR)

    # --- header (512 bytes) ---
    header = bytearray()
    header += b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"  # signature
    header += b"\x00" * 16  # CLSID
    header += struct.pack("<HH", 0x003E, 0x0003)  # minor, major version
    header += struct.pack("<H", 0xFFFE)  # byte order
    header += struct.pack("<HH", 0x0009, 0x0006)  # sector / mini-sector shift
    header += b"\x00" * 6  # reserved
    header += struct.pack("<I", 0)  # num dir sectors (0 for v3)
    header += struct.pack("<I", 1)  # num FAT sectors
    header += struct.pack("<I", dir_sector)  # first dir sector
    header += struct.pack("<I", 0)  # transaction signature
    header += struct.pack("<I", 4096)  # mini stream cutoff
    header += struct.pack("<I", minifat_sector)  # first mini-FAT sector
    header += struct.pack("<I", 1)  # num mini-FAT sectors
    header += struct.pack("<I", ENDOFCHAIN)  # first DIFAT sector
    header += struct.pack("<I", 0)  # num DIFAT sectors
    difat = [fat_sector] + [FREESECT] * 108
    header += b"".join(struct.pack("<I", v) for v in difat)
    assert len(header) == SECTOR, len(header)

    # --- assemble ---
    blob = bytearray(header)
    sectors = [b"\x00" * SECTOR] * total_sectors
    sectors[fat_sector] = fat_bytes
    sectors[dir_sector] = dir_bytes
    sectors[minifat_sector] = minifat_bytes
    mini_padded = _pad(mini_stream, SECTOR)
    for i in range(mini_container_sectors):
        sectors[mini_start + i] = mini_padded[i * SECTOR : (i + 1) * SECTOR]
    for s in sectors:
        blob += s

    Path(path).write_bytes(bytes(blob))
