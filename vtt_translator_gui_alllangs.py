#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vtt_en2fa_gui.py — انتخاب فایل VTT از سیستم، ترجمه به فارسی و ذخیره خروجی.

بدون نیاز به API Key — استفاده از Google Translate غیررسمی (deep-translator)

Install:
    pip install deep-translator

Run:
    python vtt_en2fa_gui.py
"""

import io
import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import List
from deep_translator import GoogleTranslator

# الگو برای تگ‌های HTML
TAG_PATTERN = re.compile(r"(</?[^>\n]+>)")
RLE = "\u202B"  # Right-to-Left Embedding
PDF = "\u202C"  # Pop Directional Formatting

def split_text_and_tags(s: str) -> List[str]:
    if not s:
        return [s]
    parts = TAG_PATTERN.split(s)
    return [p for p in parts if p != ""]

def join_segments(segments: List[str]) -> str:
    return "".join(segments)

def is_timestamp_line(line: str) -> bool:
    return "-->" in line

def is_note_block_start(line: str) -> bool:
    return line.strip().startswith("NOTE")

def is_style_or_region_header(line: str) -> bool:
    ls = line.strip().upper()
    return ls.startswith("STYLE") or ls.startswith("REGION")

def parse_cues(lines: List[str]) -> List[List[str]]:
    blocks = []
    block = []
    for raw in lines:
        line = raw.rstrip("\n")
        if line.strip() == "":
            if block:
                blocks.append(block)
                block = []
        else:
            block.append(line)
    if block:
        blocks.append(block)
    return blocks

def convert_vtt_blocks_to_fa(blocks: List[List[str]]) -> List[List[str]]:
    translator = GoogleTranslator(source='en', target='fa')
    out_blocks = []
    for block in blocks:
        if not block:
            continue
        if block[0].strip().upper().startswith("WEBVTT"):
            out_blocks.append(block)
            continue
        if is_note_block_start(block[0]) or is_style_or_region_header(block[0]):
            out_blocks.append(block)
            continue

        idx = 0
        cue_id = None
        if not is_timestamp_line(block[0]):
            cue_id = block[0]
            idx = 1
        if idx >= len(block):
            out_blocks.append(block)
            continue
        ts_line = block[idx]
        text_lines = block[idx+1:] if idx + 1 < len(block) else []

        segments_per_line = [split_text_and_tags(t) for t in text_lines]
        to_translate = []
        positions = []
        for li, segs in enumerate(segments_per_line):
            for si, seg in enumerate(segs):
                if seg and not TAG_PATTERN.fullmatch(seg):
                    to_translate.append(seg)
                    positions.append((li, si))

        translated = []
        for t in to_translate:
            try:
                translated.append(translator.translate(t))
            except Exception:
                translated.append(t)

        for (li, si), new_text in zip(positions, translated):
            segments_per_line[li][si] = f"{RLE}{new_text}{PDF}"

        new_text_lines = [join_segments(segs) for segs in segments_per_line]

        new_block = []
        if cue_id is not None:
            new_block.append(cue_id)
        new_block.append(ts_line)
        new_block.extend(new_text_lines if new_text_lines else [])
        out_blocks.append(new_block)

    return out_blocks

def read_vtt(path: str) -> List[str]:
    with io.open(path, "r", encoding="utf-8-sig") as f:
        return f.readlines()

def write_vtt(path: str, blocks: List[List[str]]):
    with io.open(path, "w", encoding="utf-8") as f:
        first = True
        for block in blocks:
            if not first:
                f.write("\n")
            first = False
            for line in block:
                f.write(line + "\n")

def main():
    root = tk.Tk()
    root.withdraw()

    file_path = filedialog.askopenfilename(
        title="انتخاب فایل VTT",
        filetypes=[("VTT files", "*.vtt"), ("All files", "*.*")]
    )
    if not file_path:
        messagebox.showinfo("انصراف", "هیچ فایلی انتخاب نشد.")
        return

    try:
        lines = read_vtt(file_path)
        blocks = parse_cues(lines)
        out_blocks = convert_vtt_blocks_to_fa(blocks)

        if not (out_blocks and out_blocks[0][0].strip().upper().startswith("WEBVTT")):
            out_blocks = [["WEBVTT"]] + [[""]] + out_blocks

        output_path = os.path.splitext(file_path)[0] + "-fa.vtt"
        write_vtt(output_path, out_blocks)

        messagebox.showinfo("موفقیت", f"فایل ترجمه‌شده ذخیره شد:\n{output_path}")
    except Exception as e:
        messagebox.showerror("خطا", f"مشکلی پیش آمد:\n{e}")

if __name__ == "__main__":
    main()