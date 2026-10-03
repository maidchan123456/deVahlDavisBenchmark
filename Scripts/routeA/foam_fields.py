#!/usr/bin/env python3
"""Small ASCII OpenFOAM field readers used by the Route A audit scripts."""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np


def _internal_text(path: Path) -> tuple[str, str]:
    text = path.read_text()
    match = re.search(r"\binternalField\s+(uniform|nonuniform)\s+", text)
    if not match:
        raise ValueError(f"No internalField in {path}")
    return match.group(1), text[match.end():]


def read_scalar(path: Path, size: int) -> np.ndarray:
    kind, tail = _internal_text(path)
    if kind == "uniform":
        value = float(tail.split(";", 1)[0].strip())
        return np.full(size, value, dtype=float)
    match = re.match(r"List<scalar>\s+(\d+)\s*\(\s*(.*?)\s*\)\s*;", tail, re.S)
    if not match:
        raise ValueError(f"Cannot parse scalar list in {path}")
    count = int(match.group(1))
    values = np.fromstring(match.group(2), sep=" ")
    if count != size or values.size != count:
        raise ValueError(f"Expected {size} scalars in {path}, got {count}/{values.size}")
    return values


def read_vector(path: Path, size: int) -> np.ndarray:
    kind, tail = _internal_text(path)
    if kind == "uniform":
        match = re.match(r"\(\s*([^)]*)\)\s*;", tail, re.S)
        if not match:
            raise ValueError(f"Cannot parse uniform vector in {path}")
        value = np.fromstring(match.group(1), sep=" ")
        return np.tile(value, (size, 1))
    match = re.match(r"List<vector>\s+(\d+)\s*\(\s*(.*?)\s*\)\s*;", tail, re.S)
    if not match:
        raise ValueError(f"Cannot parse vector list in {path}")
    count = int(match.group(1))
    rows = re.findall(r"\(\s*([^()]*)\)", match.group(2))
    values = np.array([np.fromstring(row, sep=" ") for row in rows])
    if count != size or values.shape != (count, 3):
        raise ValueError(f"Expected {(size, 3)} vectors in {path}, got {values.shape}")
    return values


def _named_block(text: str, name: str) -> str:
    match = re.search(rf"\b{re.escape(name)}\s*\{{", text)
    if not match:
        raise ValueError(f"No block {name}")
    start = text.find("{", match.start())
    depth = 0
    for index in range(start, len(text)):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                return text[start + 1:index]
    raise ValueError(f"Unclosed block {name}")


def read_boundary_scalar(path: Path, patch: str, size: int) -> np.ndarray:
    text = path.read_text()
    boundary = _named_block(text, "boundaryField")
    block = _named_block(boundary, patch)
    match = re.search(r"\bvalue\s+(uniform|nonuniform)\s+", block)
    if not match:
        raise ValueError(f"No scalar value for patch {patch} in {path}")
    kind = match.group(1)
    tail = block[match.end():]
    if kind == "uniform":
        return np.full(size, float(tail.split(";", 1)[0].strip()))
    match = re.match(r"List<scalar>\s+(\d+)\s*\(\s*(.*?)\s*\)\s*;", tail, re.S)
    if not match:
        raise ValueError(f"Cannot parse patch {patch} in {path}")
    count = int(match.group(1))
    values = np.fromstring(match.group(2), sep=" ")
    if count != size or values.size != size:
        raise ValueError(f"Expected {size} patch values in {path}, got {count}/{values.size}")
    return values


def latest_time(case: Path) -> tuple[float, Path]:
    values = []
    for path in case.iterdir():
        if path.is_dir():
            try:
                values.append((float(path.name), path))
            except ValueError:
                pass
    if not values:
        raise ValueError(f"No time directories in {case}")
    return max(values, key=lambda pair: pair[0])
