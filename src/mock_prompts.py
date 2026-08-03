#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prompt templates used to generate synthetic student submissions."""

from __future__ import annotations

from typing import Final

PROMPT_SYSTEM_BASE: Final[str] = """
You are generating realistic student submissions for a French MP2I computer-science practical session.

Strict output format requirements:
1) Return only Markdown code blocks.
2) Each generated file must be inside its own fenced block.
3) The first line after the fence header must declare the filename with one of:
    - // fichier: <name> // Langage C
    - (* fichier: <name> *) (* Langage OCaml *)
    - <!-- # fichier: <name> --> <!-- Langage Markdown -->
4) Use coherent file names, such as `code_rendu.ml` or `code_rendu.c` for OCaml / C source code, and `compte_rendu.md` for the Markdown report.
5) The Markdown report can include some simple LaTeX formulas delimited with $...$ or $$...$$.
6) Do not add prose outside code blocks.
""".strip()

PROMPTS_PROFILES: Final[dict[str, dict[str, str]]] = {
    "MOCK_20_20": {
        "label": "Excellent (20/20)",
        "instructions": (
            "Generate a near-perfect submission. All requested questions are answered. "
            "The source code is clear, modular, and robust. Include assertions where relevant, "
            "clean edge-case handling, and algorithmically efficient choices. "
            "For C code, avoid memory leaks and undefined behavior. "
            "For OCaml code, keep strong functional clarity and safe pattern matching. "
            "Include meaningful internal tests if the TP context allows it."
        ),
    },
    "MOCK_12_20": {
        "label": "Moyen (12/20)",
        "instructions": (
            "Generate a realistic mid-level submission: the beginning is mostly correct, "
            "but the last 2 to 3 questions are incomplete or missing due to lack of time. "
            "The code must remain compilable and readable, with minor weaknesses such as "
            "light testing and occasionally suboptimal complexity choices."
        ),
    },
    "MOCK_05_20": {
        "label": "Faible (05/20)",
        "instructions": (
            "Generate a weak but plausible submission: only the first 2 to 3 basic questions are attempted. "
            "The implementation can be naive and very incomplete. "
            "Absolute constraint: the source code must compile without syntax errors. "
            "Do not return intentionally broken syntax."
        ),
    },
}


def build_generation_prompt(subject_text: str, profile_key: str) -> str:
    """Build a synthetic-submission generation prompt from subject context and profile."""
    if profile_key not in PROMPTS_PROFILES:
        valid_profiles = ", ".join(sorted(PROMPTS_PROFILES))
        raise ValueError(f"Unknown profile '{profile_key}'. Expected one of: {valid_profiles}.")

    profile = PROMPTS_PROFILES[profile_key]
    profile_instructions = profile.get("instructions", "")

    return (
        "Tu vas simuler un rendu étudiant (faux mais très réaliste), pour un TP d'informatique en CPGE MP2I.\n\n"
        f"{PROMPT_SYSTEM_BASE}\n\n"
        "# Contraintes prioritaires:\n"
        "- Générer au moins un fichier de code source principal (C : `code_rendu.c` ou OCaml : `code_rendu.ml` selon le TP).\n"
        "- Générer un compte-rendu explicatif, concis mais précis, plus ou moins détaillé selon le niveau attendu par le rendu, rédigé en Markdown (`compte_rendu.md`) et qui soit parfaitement cohérent avec le code produit. Le compte-rendu peut inclure quelques formules mathématiques en LaTeX.\n"
        "- Le style doit ressembler à un vrai rendu étudiant, pas à un corrigé officiel (sauf pour le profil excellent 20/20).\n"
        "- Respect strict du format de sortie imposé par le system prompt.\n\n"
        f"# Profil ciblé: {profile_key} ({profile.get('label', profile_key)}).\n"
        f"# Consignes de profil:\n{profile_instructions}\n\n"
        "Sujet et contexte:\n"
        f"{subject_text}\n"
    )
