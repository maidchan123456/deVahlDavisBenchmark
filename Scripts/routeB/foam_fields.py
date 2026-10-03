#!/usr/bin/env python3
"""Minimal readers for ASCII OpenFOAM v6 field files."""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np


def _internal(path: Path) -> tuple[str, str]:
    text = path.read_text()
    match = re.search(r"\binternalField\s+(uniform|nonuniform)\s+", text)
    if not match:
        raise ValueError(f"No internalField in {path}")
    return match.group(1), text[match.end():]


def read_scalar(path: Path, size: int) -> np.ndarray:
    kind, tail = _internal(path)
    if kind == "uniform":
        return np.full(size, float(tail.split(";", 1)[0].strip()))
    match = re.match(r"List<scalar>\s+(\d+)\s*\(\s*(.*?)\s*\)\s*;", tail, re.S)
    if not match:
        raise ValueError(f"Cannot parse scalar field {path}")
    values = np.fromstring(match.group(2), sep=" ")
    if int(match.group(1)) != size or values.size != size:
        raise ValueError(f"Wrong scalar count in {path}")
    return values


def read_vector(path: Path, size: int) -> np.ndarray:
    kind, tail = _internal(path)
    if kind == "uniform":
        match = re.match(r"\(\s*([^)]*)\)\s*;", tail, re.S)
        value = np.fromstring(match.group(1), sep=" ")
        return np.tile(value, (size, 1))
    match = re.match(r"List<vector>\s+(\d+)\s*\(\s*(.*?)\s*\)\s*;", tail, re.S)
    if not match:
        raise ValueError(f"Cannot parse vector field {path}")
    rows = re.findall(r"\(\s*([^()]*)\)", match.group(2))
    values = np.array([np.fromstring(row, sep=" ") for row in rows])
    if int(match.group(1)) != size or values.shape != (size, 3):
        raise ValueError(f"Wrong vector count in {path}: {values.shape}")
    return values


def read_label_list(path: Path) -> np.ndarray:
    """Read an OpenFOAM labelList such as polyMesh owner/neighbour."""
    text = path.read_text()
    # The list count immediately precedes the opening parenthesis after the header.
    match = re.search(r"\n\s*(\d+)\s*\(\s*([0-9+\-\s]+?)\s*\)", text, re.S)
    if not match:
        raise ValueError(f"Cannot parse labelList {path}")
    values = np.fromstring(match.group(2), sep=" ", dtype=np.int64)
    if values.size != int(match.group(1)):
        raise ValueError(f"Wrong label count in {path}")
    return values


def _block(text: str, name: str) -> str:
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


def _boundary_value(path: Path, patch: str) -> tuple[str, str]:
    boundary = _block(path.read_text(), "boundaryField")
    patch_block = _block(boundary, patch)
    match = re.search(r"\bvalue\s+(uniform|nonuniform)\s+", patch_block)
    if not match:
        raise ValueError(f"No value in {path}:{patch}")
    return match.group(1), patch_block[match.end():]


def read_boundary_scalar(path: Path, patch: str, size: int) -> np.ndarray:
    kind, tail = _boundary_value(path, patch)
    if kind == "uniform":
        return np.full(size, float(tail.split(";", 1)[0].strip()))
    match = re.match(r"List<scalar>\s+(\d+)\s*\(\s*(.*?)\s*\)\s*;", tail, re.S)
    values = np.fromstring(match.group(2), sep=" ")
    if int(match.group(1)) != size or values.size != size:
        raise ValueError(f"Wrong patch scalar count in {path}:{patch}")
    return values


def read_boundary_vector(path: Path, patch: str, size: int) -> np.ndarray:
    kind, tail = _boundary_value(path, patch)
    if kind == "uniform":
        match = re.match(r"\(\s*([^)]*)\)\s*;", tail, re.S)
        return np.tile(np.fromstring(match.group(1), sep=" "), (size, 1))
    match = re.match(r"List<vector>\s+(\d+)\s*\(\s*(.*?)\s*\)\s*;", tail, re.S)
    rows = re.findall(r"\(\s*([^()]*)\)", match.group(2))
    values = np.array([np.fromstring(row, sep=" ") for row in rows])
    if int(match.group(1)) != size or values.shape != (size, 3):
        raise ValueError(f"Wrong patch vector count in {path}:{patch}")
    return values


def latest_time(case: Path) -> tuple[int, Path]:
    times = []
    for path in case.iterdir():
        if path.is_dir():
            try:
                times.append((int(round(float(path.name))), path))
            except ValueError:
                pass
    return max(times, key=lambda pair: pair[0])
