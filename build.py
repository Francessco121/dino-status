#!/usr/bin/env python3
# Builds the Dinosaur Planet decomp progress site

import json
import sys
from colour import Color
from datetime import datetime
import shutil
import chevron
import os
from pathlib import Path

SRC_DIR = Path(os.path.dirname(os.path.realpath(__file__)))
BUILD_DIR = SRC_DIR.joinpath("build")

def make_nice_datetime_str(dt: datetime):
    hour = dt.hour
    if hour == 0:
        hour_str = "12"
    elif hour > 12:
        hour_str = str(hour - 12)
    else:
        hour_str = str(hour)

    return "{dt:%b} {dt.day}, {hour}:{dt:%M} {dt:%p}".format(
        dt=dt, hour=hour_str)

def lerp(a, b, alpha):
    return a + (b - a) * alpha

def load_progress(path: Path):
    if not path.exists():
        print(f"Could not find {path.relative_to(SRC_DIR)}.")
        sys.exit(1)

    with open(path, "r") as file:
        return json.load(file)

def update_assets():
    """Updates the build directory with modified assets and removes files that no longer exist."""
    suffixes = [
        ".html",
        ".png", ".jpg", ".jpeg", ".ico",
        ".css", ".ttf",
        ".nojekyll"
    ]

    build_dir_exists = BUILD_DIR.exists()
    if not build_dir_exists:
        BUILD_DIR.mkdir(exist_ok=True)

    src_files: "set[Path]" = set()

    def copy_modified(dir: Path):
        for path in dir.iterdir():
            if path.is_dir() and path.name != BUILD_DIR.name:
                # Recurse
                copy_modified(path)
            else:
                # Save path so we can detect removed files later
                if path.suffix == ".mustache":
                    src_files.add(path.with_suffix(".html"))
                else:
                    src_files.add(path)
                # Skip if not a file we should copy
                if not path.suffix in suffixes:
                    continue
                # Update file if source was modified
                dest = BUILD_DIR.joinpath(path.relative_to(SRC_DIR))
                if not dest.exists() or os.path.getmtime(path) > os.path.getmtime(dest):
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(path, dest)
    
    def delete_removed(dir: Path):
        for path in dir.iterdir():
            if path.is_dir():
                # Recurse
                delete_removed(path)
            else:
                # Delete if path isn't in source
                orig = SRC_DIR.joinpath(path.relative_to(BUILD_DIR))
                if not orig in src_files:
                    path.unlink()
    
    def delete_empty_dirs(dir: Path):
        for path in dir.iterdir():
            if not path.is_dir():
                continue
            if len(os.listdir(path)) == 0:
                path.rmdir()
            else:
                delete_empty_dirs(path)
    
    copy_modified(SRC_DIR)
    if build_dir_exists:
        delete_removed(BUILD_DIR)
        delete_empty_dirs(BUILD_DIR)

def render_template(path: Path, data):
    with open(path, "r") as file:
        html = chevron.render(file, data)
   
    out_path = BUILD_DIR.joinpath(path.relative_to(SRC_DIR).with_suffix(".html"))
    with open(out_path, "w", encoding="utf-8") as file:
        file.write(html)

def render_templates(p):
    # Render index
    render_template(SRC_DIR.joinpath("index.mustache"), {
        "total_matching_ratio": p["total"]["matching_ratio"],
        "total_matching_perct": "{:.1f}".format(p["total"]["matching_ratio"] * 100),
        "total_matching_funcs": "{:,}".format(p["total"]["matching_funcs"]),
        "total_matching_kb": "{:,.1f}".format(p["total"]["matching_bytes"] / 1024),
        "total_funcs": "{:,}".format(p["total"]["total_funcs"]),
        "total_kb": "{:,.1f}".format(p["total"]["total_bytes"] / 1024),
        
        "core_matching_ratio": p["core"]["matching_ratio"],
        "core_matching_perct": "{:.1f}".format(p["core"]["matching_ratio"] * 100),
        "core_matching_funcs": "{:,}".format(p["core"]["matching_funcs"]),
        "core_matching_kb": "{:,.1f}".format(p["core"]["matching_bytes"] / 1024),
        "core_funcs": "{:,}".format(p["core"]["total_funcs"]),
        "core_kb": "{:,.1f}".format(p["core"]["total_bytes"] / 1024),

        "dll_matching_ratio": p["dll"]["matching_ratio"],
        "dll_matching_perct": "{:.1f}".format(p["dll"]["matching_ratio"] * 100),
        "dll_matching_funcs": "{:,}".format(p["dll"]["matching_funcs"]),
        "dll_matching_kb": "{:,.1f}".format(p["dll"]["matching_bytes"] / 1024),
        "dll_funcs": "{:,}".format(p["dll"]["total_funcs"]),
        "dll_kb": "{:,.1f}".format(p["dll"]["total_bytes"] / 1024),

        "git_commit_hash": p["git"]["commit_hash"],
        "git_commit_hash_short": p["git"]["commit_hash_short"],
        "git_commit_datetime": make_nice_datetime_str(datetime.fromtimestamp(p["git"]["commit_timestamp"]))
    })

def generate_shield(name: str, label: str, matching_ratio: float):
    """Generates a shield JSON file for https://shields.io/endpoint"""
    file_path = BUILD_DIR.joinpath(f"{name}.shield.json")
    color = Color("#50ca22", hue=lerp(0, 105/255, matching_ratio))
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump({
            "schemaVersion": 1,
            "label": label,
            "message": f"{matching_ratio * 100:.2f}%",
            "color": color.hex,
        }, file)

def generate_shields(p):
    generate_shield("total", "Total", p["total"]["matching_ratio"])
    generate_shield("core", "Core", p["core"]["matching_ratio"])
    generate_shield("dlls", "DLLs", p["dll"]["matching_ratio"])

def main():
    # Load progress
    progress = load_progress(SRC_DIR.joinpath("data/progress.json"))

    # Update assets
    update_assets()

    # Render mustache templates
    render_templates(progress)
    
    # Create shields 
    generate_shields(progress)

if __name__ == "__main__":
    main()
