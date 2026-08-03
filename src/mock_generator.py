#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Business logic for synthetic student submission generation with Gemini."""

from __future__ import annotations

import os
import re
from pathlib import Path

from src.mock_prompts import PROMPT_SYSTEM_BASE


def _read_api_key() -> str:
    """Resolve the Gemini API key from environment, local key file, or Streamlit secrets."""
    for env_name in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
        env_value = os.environ.get(env_name)
        if env_value:
            return env_value.strip()

    key_file = Path.home() / ".gemini_api.key"
    if key_file.exists():
        key_value = key_file.read_text(encoding="utf-8").strip()
        if key_value:
            return key_value

    try:
        import streamlit as st

        for secret_name in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
            if secret_name in st.secrets:
                secret_value = str(st.secrets[secret_name]).strip()
                if secret_value:
                    return secret_value
    except Exception:
        pass

    raise RuntimeError(
        "No Gemini API key found. Define GEMINI_API_KEY (or GOOGLE_API_KEY), "
        "or create ~/.gemini_api.key, or add the key to .streamlit/secrets.toml."
    )


def call_gemini_api(prompt: str, model_name: str = "gemini-flash-latest") -> str:
    """Call Google Gemini and return the plain text response."""
    if not prompt.strip():
        raise ValueError("The prompt cannot be empty.")

    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:
        raise RuntimeError(
            "Missing dependency 'google-genai'. Install it with: pip install google-genai"
        ) from exc

    api_key = _read_api_key()
    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model=model_name,
        contents=[PROMPT_SYSTEM_BASE, prompt],
        config=types.GenerateContentConfig(response_mime_type="text/plain"),
    )

    return response.text or ""


def _extract_filename_from_header(header: str) -> str | None:
    """Extract a filename declaration from a fence header line."""
    header_match = re.search(r"(?:fichier|file|filename)\s*:\s*([A-Za-z0-9._/-]+)", header, re.IGNORECASE)
    if header_match:
        return header_match.group(1).strip()
    return None


def _extract_filename_from_content(content: str) -> str | None:
    """Extract a filename declaration from the first lines of a code block."""
    lines = content.splitlines()
    for line in lines[:4]:
        file_match = re.search(r"(?:fichier|file|filename)\s*:\s*([A-Za-z0-9._/-]+)", line, re.IGNORECASE)
        if file_match:
            return file_match.group(1).strip()
    return None


def _sanitize_relative_filename(filename: str, fallback_index: int) -> str:
    """Normalize filename to avoid path traversal and invalid empty values."""
    safe_name = Path(filename).name.strip()
    if not safe_name:
        return f"generated_file_{fallback_index}.txt"
    return safe_name


def extract_files_from_markdown(response_text: str) -> dict[str, str]:
    """Parse a Markdown response and extract generated files as a name/content mapping."""
    if not isinstance(response_text, str) or not response_text.strip():
        return {"compte_rendu.md": ""}

    fence_pattern = re.compile(r"```([^\n`]*)\n(.*?)```", re.DOTALL)
    matches = list(fence_pattern.finditer(response_text))

    if not matches:
        return {"compte_rendu.md": response_text.strip() + "\n"}

    files: dict[str, str] = {}
    # Unnamed blocks are accumulated and merged into a single compte_rendu.md
    # instead of being split across compte_rendu.md, code_rendu_2.txt, etc.
    unnamed_parts: list[str] = []

    for match_index, match in enumerate(matches, start=1):
        header = (match.group(1) or "").strip()
        content = (match.group(2) or "").strip("\n")

        filename = _extract_filename_from_header(header)
        if filename is None:
            filename = _extract_filename_from_content(content)

        if filename is None:
            unnamed_parts.append(content.rstrip())
            continue

        filename = _sanitize_relative_filename(filename, match_index)
        deduplicated_name = filename
        suffix_counter = 2
        while deduplicated_name in files:
            stem = Path(filename).stem
            suffix = Path(filename).suffix
            deduplicated_name = f"{stem}_{suffix_counter}{suffix}"
            suffix_counter += 1

        files[deduplicated_name] = content.rstrip() + "\n"

    if unnamed_parts:
        merged = "\n\n".join(unnamed_parts) + "\n"
        if "compte_rendu.md" in files:
            files["compte_rendu.md"] = files["compte_rendu.md"].rstrip() + "\n\n" + merged
        else:
            files["compte_rendu.md"] = merged

    if not files:
        return {"compte_rendu.md": response_text.strip() + "\n"}

    return files


def save_mock_submission(target_dir: str, files: dict[str, str]) -> list[str]:
    """Save generated submission files to disk and return saved path strings."""
    target_path = Path(target_dir)
    target_path.mkdir(parents=True, exist_ok=True)

    saved_paths: list[str] = []
    for index, (filename, content) in enumerate(files.items(), start=1):
        safe_filename = _sanitize_relative_filename(filename, index)
        file_path = target_path / safe_filename
        file_path.write_text(content, encoding="utf-8")
        saved_paths.append(str(file_path))

    return saved_paths
