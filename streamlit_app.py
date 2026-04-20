#!/usr/bin/env python3
#-*- coding: utf-8 -*-
"""Streamlit dashboard used to inspect TP subjects and student submissions.

The app discovers available practical sessions from the repository layout,
renders subject PDFs, previews submitted source files, and displays the
associated report when available.
"""

from __future__ import annotations

import base64
import json
import html as html_lib
import re
import statistics
import subprocess
import shutil
from pathlib import Path
from typing import Final, Sequence, TypedDict, cast

import altair as alt
import streamlit as st

# Local module
from gemini_requests import response_from_llm, help_credits_llm


# Repository layout and default values used across all dashboard modes.
ROOT_DIR: Final[Path] = Path(__file__).resolve().parent
SUBJECTS_DIR: Final[Path] = ROOT_DIR / "sujets-de-travaux-pratiques"
SUBMISSIONS_DIR: Final[Path] = ROOT_DIR / "rendus-des-etudiants"
REPOSITORY_URL: Final[str] = "https://github.com/Naereen/Auto-Eval-TP-info-MP2I-via-LLM"

# LOGO_LYCEE: Final[str] = "logo.png"
LOGO_LYCEE: Final[str] = "logo.jpeg"

# Configure the OCaml $PATH cleverly '/home/lilian/.opam/4.14.1/bin/ocaml'
# TODO: be independant of the installed version of OCaml and Opam...
OCAML_INTERPRETER_PATH: Final[Path] = Path.home() / '.opam' / '4.14.1' / 'bin' / 'ocaml'

# Preferred filenames are checked first before falling back to broader glob searches.
CODE_CANDIDATES: Final[tuple[str, ...]] = ("code_rendu.c", "code_rendu.ml")
REPORT_PDF_CANDIDATES: Final[tuple[str, ...]] = ("compte-rendu.pdf", "compte_rendu.pdf")
REPORT_MD_CANDIDATES: Final[tuple[str, ...]] = ("compte-rendu.md", "compte_rendu.md")

BAREME_FILENAME: Final[str] = "bareme.json"
NOTES_FILENAME: Final[str] = "notes.json"
DUNE_TESTS_DIR: Final[str] = "dune_tests"
OCAML_COMPILE_LOG_FILENAME: Final[str] = "ocamlopt_code_rendu.log"
OCAML_INTERPRET_LOG_FILENAME: Final[str] = "ocaml_interpreter_code_rendu.log"
OCAML_EXEC_LOG_FILENAME: Final[str] = "exec_code_rendu.log"
OCAML_TEST_LOG_FILENAME: Final[str] = "test_code_rendu.log"
OCAML_TEST_JSON_FILENAME: Final[str] = "test_code_rendu.json"
OCAML_TEST_HTML_FILENAME: Final[str] = "test_code_rendu.html"

DEFAULT_QUESTION_COUNT: Final[int] = 10
DEFAULT_QUESTION_POINTS: Final[int] = 5

APP_MODES: Final[tuple[str, ...]] = (
    "0 - Documentation",
    "1 - Barème",
    "2 - Génération IA de tests OCaml",
    "3 - Évaluation des rendus",
    "4 - Vue de la classe par TP",
    "5 - Progression annuelle individuelle",
)

SYSTEM_PROMPT = "Tu es une IA utile et extrêmement efficace, experte en informatique en français. Tu aides un professeur d'informatique en classes préparatoires CPGE, filière MP2I, en France."


# Typed payloads make the persisted JSON structures easier to reason about.
class QuestionConfig(TypedDict):
    """One normalized question entry stored in bareme.json."""

    index: int
    label: str
    points: int


class BaremeData(TypedDict):
    """Normalized marking scheme stored per practical session."""

    format_version: int
    tp_name: str
    question_count: int
    total_points: int
    questions: list[QuestionConfig]


class GradedQuestion(TypedDict):
    """One normalized grading entry aligned with a barème question."""

    index: int
    label: str
    max_points: int
    points_awarded: int


class GradingData(TypedDict):
    """Normalized grading sheet stored per student submission."""

    format_version: int
    tp_name: str
    student_name: str
    question_count: int
    total_points_awarded: int
    total_points_bareme: int
    note_sur_20: float
    questions: list[GradedQuestion]


class NumericSummary(TypedDict):
    """Compact summary used by classroom and annual dashboards."""

    mean: float
    median: float
    min: float
    max: float
    stddev: float


# Repository discovery and file loading helpers.


@st.cache_data(show_spinner=False)
def get_current_git_commit() -> tuple[str | None, str | None, str | None]:
    """Return the full, short git hashes and the date, for the current repository when available."""
    try:
        full_sha = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT_DIR,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        short_sha = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT_DIR,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        modification_date = subprocess.run(
            ["git", "log", "-1", "--format=%cr"],
            cwd=ROOT_DIR,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None, None, None

    if not full_sha or not short_sha or not modification_date:
        return None, None, None

    return full_sha, short_sha, modification_date


def list_subdirectories(directory: Path) -> list[Path]:
    """Return subdirectories sorted by name, or an empty list if the parent is missing."""
    if not directory.exists():
        return []
    return sorted((path for path in directory.iterdir() if path.is_dir()), key=lambda path: path.name.lower())


def get_subject_dir(tp_name: str) -> Path:
    """Return the directory storing assets for the selected practical session."""
    return SUBJECTS_DIR / tp_name


def get_bareme_path(tp_name: str) -> Path:
    """Return the JSON file used to persist the marking scheme for a practical session."""
    return get_subject_dir(tp_name) / BAREME_FILENAME


def get_notes_path(student_dir: Path) -> Path:
    """Return the JSON file used to persist one student's grading data."""
    return student_dir / NOTES_FILENAME


def has_saved_grading(student_dir: Path) -> bool:
    """Return whether a student's submission directory already contains saved grading data."""
    return get_notes_path(student_dir).exists()


@st.cache_data(show_spinner=True)
def discover_tp_names() -> list[str]:
    """List available practical sessions from the subjects directory."""
    return [path.name for path in list_subdirectories(SUBJECTS_DIR)]


@st.cache_data(show_spinner=True)
def find_subject_pdf(tp_name: str) -> Path | None:
    """Find the main PDF for a given practical session."""
    tp_dir = get_subject_dir(tp_name)
    preferred = sorted(tp_dir.glob("tp-*.pdf"))
    if preferred:
        return preferred[0]

    pdfs = sorted(tp_dir.glob("*.pdf"))
    if pdfs:
        return pdfs[0]

    return None


@st.cache_data(show_spinner=True)
def find_subject_tex_files(tp_name: str) -> list[Path]:
    """List LaTeX sources associated with a practical session."""
    tp_dir = get_subject_dir(tp_name)
    return sorted(tp_dir.glob("*.tex"))


@st.cache_data(show_spinner=True)
def find_subject_markdown_files(tp_name: str) -> list[Path]:
    """List Markdown sources associated with a practical session."""
    tp_dir = get_subject_dir(tp_name)
    return sorted(tp_dir.glob("*.md"))


@st.cache_data(show_spinner=True)
def discover_student_dirs(tp_name: str, name_of_dir_to_ignore=DUNE_TESTS_DIR) -> list[Path]:
    """List submission directories available for the selected practical session."""
    all_dirs = list_subdirectories(SUBMISSIONS_DIR / tp_name)
    if name_of_dir_to_ignore:
        all_dirs = [d for d in all_dirs if name_of_dir_to_ignore not in d.parts and name_of_dir_to_ignore not in str(d.name)]
    return all_dirs


@st.cache_data(show_spinner=True)
def discover_all_student_names() -> list[str]:
    """List all distinct student submission directory names across the available practical sessions."""
    student_names: set[str] = set()
    for tp_name in discover_tp_names():
        for student_dir in discover_student_dirs(tp_name):
            if DUNE_TESTS_DIR in student_dir.parts or DUNE_TESTS_DIR in str(student_dir.name):
                continue
            student_names.add(student_dir.name)
    return sorted(student_names)


def pick_first_existing(directory: Path, candidates: tuple[str, ...]) -> Path | None:
    """Return the first candidate filename that exists inside a directory."""
    for filename in candidates:
        path = directory / filename
        if path.exists():
            return path
    return None


def find_student_code(student_dir: Path) -> Path | None:
    """Locate the submitted source file, preferring the canonical filenames."""
    preferred = pick_first_existing(student_dir, CODE_CANDIDATES)
    if preferred is not None:
        return preferred

    fallback = sorted(student_dir.glob("*.c")) + sorted(student_dir.glob("*.ml"))
    return fallback[0] if fallback else None


def find_student_report_pdf(student_dir: Path) -> Path | None:
    """Locate the student report as a PDF when possible."""
    preferred = pick_first_existing(student_dir, REPORT_PDF_CANDIDATES)
    if preferred is not None:
        return preferred

    pdfs = sorted(student_dir.glob("*.pdf"))
    return pdfs[0] if pdfs else None


def find_student_report_markdown(student_dir: Path) -> Path | None:
    """Locate the student report as Markdown for the PDF fallback path."""
    preferred = pick_first_existing(student_dir, REPORT_MD_CANDIDATES)
    if preferred is not None:
        return preferred

    markdown_files = sorted(student_dir.glob("*.md"))
    return markdown_files[0] if markdown_files else None


@st.cache_data(show_spinner=True)
def read_text_file(path: str) -> str:
    """Read a UTF-8 text file from disk and cache the content."""
    return Path(path).read_text(encoding="utf-8")


@st.cache_data(show_spinner=True)
def read_binary_file(path: str) -> bytes:
    """Read a binary file from disk and cache the content."""
    return Path(path).read_bytes()


def slugify_for_filename(value: str) -> str:
    """Convert a display string into a filesystem-friendly slug."""
    slug = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    slug = slug.strip("._-")
    return slug or "artifact"


def run_command_and_capture_output(
    command: Sequence[str | Path], cwd: Path, log_path: Path, input_path=None, timeout=60
) -> tuple[int, str]:
    """Run one command safely, save its combined output, and return the exit code plus output."""
    try:
        command_parts = [str(part) for part in command]
        input_file = None
        if input_path:
            input_file = open(input_path, "r")
        completed = subprocess.run(
            command_parts,
            cwd=cwd,
            check=False,
            stdin=input_file,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout,
        )
        output = normalize_output_piece(completed.stdout)
        exit_code = completed.returncode
    except FileNotFoundError as exc:
        output = f"Commande introuvable : {exc}\n"
        exit_code = 127
    except subprocess.TimeoutExpired as exc:
        output = normalize_output_piece(exc.stdout)
        output += "\n[Erreur : délai d'exécution dépassé]"
        exit_code = 124

    if not output.strip():
        output = "Aucune sortie.\n"
    log_path.write_text(output, encoding="utf-8")
    read_text_file.clear()
    return exit_code, output


def normalize_output_piece(value: object) -> str:
    """Convert a captured output fragment into a UTF-8 string."""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, str):
        return value
    if value is None:
        return ""
    return str(value)


def load_log_text(log_path: Path) -> str:
    """Read a log file when it exists, otherwise return an empty string."""
    if not log_path.exists():
        return ""
    return read_text_file(str(log_path))


def render_code_log(log_path: Path, language: str, empty_message: str) -> None:
    """Render a text log in a syntax-highlighted code block."""
    log_text = load_log_text(log_path)
    if log_text:
        st.code(log_text, language=language, line_numbers=True, wrap_lines=True, height=520)
    else:
        st.info(empty_message)


def ansi_log_to_html(log_text: str) -> str:
    """Convert an ANSI-colored log to HTML when possible, with a safe fallback."""
    try:
        from ansi2html import Ansi2HTMLConverter  # type: ignore[reportMissingImports]
        converter = Ansi2HTMLConverter(inline=True)
        return converter.convert(log_text, full=False).replace("\n", "<br>")
    except ImportError:
        escaped = html_lib.escape(log_text)
        return f"<pre style=\"white-space: pre-wrap; font-family: monospace; margin: 0;\">{escaped}</pre>"


def render_html_log(html_path: Path, empty_message: str) -> None:
    """Render a generated HTML log inside Streamlit."""
    if not html_path.exists():
        st.info(empty_message)
        return

    html_content = read_text_file(str(html_path))
    st.iframe(html_content, height=520)


def get_ocaml_tests_dir(tp_name: str) -> Path:
    """Return the directory containing the shared OCaml dune tests for one TP."""
    return SUBMISSIONS_DIR / tp_name / DUNE_TESTS_DIR


def get_ocaml_compile_log_path(student_dir: Path) -> Path:
    """Return the path of the OCaml compilation log for one student render."""
    return student_dir / OCAML_COMPILE_LOG_FILENAME


def get_ocaml_interpret_log_path(student_dir: Path) -> Path:
    """Return the path of the OCaml interpretation log for one student render."""
    return student_dir / OCAML_INTERPRET_LOG_FILENAME


def get_ocaml_exec_log_path(student_dir: Path) -> Path:
    """Return the path of the NsJail execution log for one student render."""
    return student_dir / OCAML_EXEC_LOG_FILENAME


def get_ocaml_test_log_path(tp_name: str) -> Path:
    """Return the path of the dune test log for one TP."""
    return get_ocaml_tests_dir(tp_name) / OCAML_TEST_LOG_FILENAME


def get_ocaml_test_json_path(tp_name: str) -> Path:
    """Return the path of the dune JSON output for one TP."""
    return get_ocaml_tests_dir(tp_name) / OCAML_TEST_JSON_FILENAME


def get_ocaml_test_html_path(tp_name: str) -> Path:
    """Return the path of the HTML rendering generated from the dune test log."""
    return get_ocaml_tests_dir(tp_name) / OCAML_TEST_HTML_FILENAME


def get_ocaml_test_source_path(tp_name: str) -> Path:
    """Return the path of the OCaml test source file for one TP."""
    return get_ocaml_tests_dir(tp_name) / "test_code_rendu.ml"


def get_ocaml_test_generation_llm_response_key(tp_name: str) -> str:
    """Return the session key used to store the last AI-generated OCaml test suite response."""
    return f"ocaml_tests_llm_response::{tp_name}"


def get_ocaml_test_overwrite_authorization_key(tp_name: str) -> str:
    """Return the session key used to unlock overwriting an existing OCaml test suite."""
    return f"ocaml_tests_allow_overwrite::{tp_name}"


def ocaml_test_suite_is_present(tp_name: str) -> bool:
    """Return whether a generated OCaml test suite already exists for one TP."""
    return get_ocaml_test_source_path(tp_name).exists()


def strip_llm_code_fences(response: object) -> str | None:
    """Extract raw source code from a fenced LLM response when possible."""
    if not isinstance(response, str):
        return None

    payload = response.strip()
    if not payload:
        return None

    if payload.startswith("```"):
        lines = payload.splitlines()
        if lines:
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        payload = "\n".join(lines).strip()

    return payload or None


def save_generated_ocaml_tests(tp_name: str, source_code: str) -> Path:
    """Persist a generated OCaml test suite and ensure the dune scaffold exists."""
    tests_dir = get_ocaml_tests_dir(tp_name)
    tests_dir.mkdir(parents=True, exist_ok=True)

    scaffold_dir = ROOT_DIR / "default_dune_tests"
    for filename in ("dune", "dune-project"):
        target_path = tests_dir / filename
        if target_path.exists():
            continue
        template_path = scaffold_dir / filename
        if template_path.exists():
            shutil.copy2(template_path, target_path)

    test_path = get_ocaml_test_source_path(tp_name)
    test_path.write_text(source_code.rstrip() + "\n", encoding="utf-8")
    read_text_file.clear()
    return test_path


def render_ocaml_tests_generation_mode(tp_name: str) -> None:
    """Render the AI-assisted OCaml test generation workflow for one practical session."""
    bareme_data = get_bareme_data(tp_name)
    subject_pdf = find_subject_pdf(tp_name)
    tex_files = find_subject_tex_files(tp_name)
    markdown_files = find_subject_markdown_files(tp_name)
    bareme_path = get_bareme_path(tp_name)
    tests_dir = get_ocaml_tests_dir(tp_name)
    test_source_path = get_ocaml_test_source_path(tp_name)
    test_suite_exists = ocaml_test_suite_is_present(tp_name)
    overwrite_authorization_key = get_ocaml_test_overwrite_authorization_key(tp_name)
    overwrite_is_authorized = bool(st.session_state.get(overwrite_authorization_key, False))

    st.title(f"Génération automatisée de tests OCaml - `{tp_name}`")
    st.caption(
        "Mode de préparation du banc de tests Dune partagé, avec génération assistée par IA du fichier `test_code_rendu.ml` quand il n'existe pas encore."
    )

    subject_col, tests_col = st.columns((1.1, 1), gap="large")

    with subject_col:
        render_subject_panel(tp_name, height=1540)

    with tests_col:
        st.subheader("Banc de tests OCaml")
        if test_suite_exists:
            st.write(
                "Ce mode prépare le dossier `dune_tests/` du TP courant. Un fichier de tests existe déjà ; son écrasement n'est possible qu'après déverrouillage explicite puis confirmation de génération."
            )
        else:
            st.write(
                "Ce mode prépare le dossier `dune_tests/` du TP courant et génère le fichier `test_code_rendu.ml` lorsqu'il est absent."
            )

        st.caption(f"Dossier cible : `{tests_dir}`")
        if test_suite_exists:
            st.success("Un fichier `test_code_rendu.ml` existe déjà pour ce TP.")
            if overwrite_is_authorized:
                st.warning(
                    "L'écrasement du fichier existant a été explicitement autorisé pour ce TP. La génération ci-dessous remplacera `dune_tests/test_code_rendu.ml`."
                )
                if st.button(
                    "Verrouiller à nouveau la protection contre l'écrasement",
                    width="stretch",
                    help="Réactive la protection et masque le bouton de génération destructive.",
                ):
                    st.session_state[overwrite_authorization_key] = False
                    st.rerun()
            else:
                st.caption(
                    "La protection contre l'écrasement est active. Déverrouillez-la explicitement si vous souhaitez remplacer le banc de tests actuel par une nouvelle génération IA."
                )
                if st.button(
                    "⚠️ Autoriser l'écrasement du fichier de tests existant",
                    width="stretch",
                    help="Déverrouille le second bouton de génération pour ce TP seulement, sans lancer encore la génération.",
                ):
                    st.session_state[overwrite_authorization_key] = True
                    st.rerun()
            existing_files = []
            if tests_dir.exists():
                for path in sorted(tests_dir.iterdir(), key=lambda item: item.name.lower()):
                    existing_files.append({"Fichier": path.name, "Type": "Dossier" if path.is_dir() else "Fichier"})
            if existing_files:
                st.dataframe(existing_files, width="stretch", hide_index=True)
            if test_source_path.exists():
                with st.expander("Afficher le fichier de tests existant"):
                    with st.container(height=520):
                        st.code(read_text_file(str(test_source_path)), language="ocaml", line_numbers=True, wrap_lines=True)

        missing_files = [filename for filename in ("dune", "dune-project", "test_code_rendu.ml") if not (tests_dir / filename).exists()]
        if missing_files:
            st.info("Fichiers absents avant génération : " + ", ".join(f"`{name}`" for name in missing_files))

        if not bareme_path.exists():
            st.warning(
                "Aucun `bareme.json` n'est encore sauvegardé pour ce TP ; la génération utilisera le barème courant en session si nécessaire."
            )

        generate_button_help = (
            "Analyse le sujet PDF, ses sources et le barème courant pour proposer un fichier `test_code_rendu.ml` Dune/Alcotest/QCheck. "
            f"{help_credits_llm}"
        )
        generation_is_unlocked = (not test_suite_exists) or overwrite_is_authorized
        if test_suite_exists and not generation_is_unlocked:
            st.info(
                "Le bouton de génération reste masqué tant que l'autorisation explicite d'écrasement n'a pas été donnée."
            )

        if generation_is_unlocked and st.button(
            "✨ Générer le fichier de tests OCaml par IA ? ✨",
            width="stretch",
            help=generate_button_help,
        ):
            overwrite_instruction = (
                "- tu peux remplacer le fichier existant `test_code_rendu.ml` par une nouvelle version complète et cohérente ;"
                if test_suite_exists
                else "- crée le fichier `test_code_rendu.ml` attendu dans le dossier de tests ;"
            )
            prompt = f"""
Analyse ce sujet de Travaux Pratiques d'Informatique en MP2I.

Je te donne :
- le sujet du TP, avec ses sources LaTeX ou Markdown,
- le barème JSON courant du sujet.

Je veux que tu génères le fichier OCaml complet `test_code_rendu.ml` pour un banc de tests dans le contexte d'un projet `Dune`.

Contraintes impératives :
- ne renvoie QUE le code source OCaml final, sans verbiage inutile ni explication, sans Markdown, sans bloc de code ;
- le fichier doit être compatible avec le framework de test composé de `dune`, `alcotest` plus `qcheck`, et `qcheck-alcotest` ;
- le module principal à tester s'appelle `Code_rendu` et sera importé comme `module CR = Code_rendu` ;
- écris à la fois des tests unitaires (avec Alcotest) et des tests de propriétés (avec QCheck), quand c'est pertinent ;
- privilégie des helpers lisibles, des assertions explicites et des générateurs QCheck robustes ;
- si l'API exacte n'est pas entièrement déductible, construis des tests génériques utiles à partir du sujet et des exemples présents ;
{overwrite_instruction}

Le résultat doit constituer un banc de tests sérieux, vraiment très complet, pédagogique et directement exploitable, sans erreur de compilation ou autre problème.
            """

            system_prompt = SYSTEM_PROMPT

            json_paths: list[Path] = []
            if bareme_path.exists():
                json_paths.append(bareme_path)

            additional_messages: list[str] | None = None
            if not json_paths:
                additional_messages = [
                    "Barème courant en mémoire de session :\n" + json.dumps(bareme_data, ensure_ascii=False, indent=2)
                ]

            source_paths: list[Path] = list(tex_files) + list(markdown_files)
            with st.spinner("Génération du fichier de tests en cours grâce à l'IA..."):
                response = response_from_llm(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    additionnal_messages=additional_messages,
                    paths_pdf=[subject_pdf] if subject_pdf is not None else None,
                    paths_json=json_paths or None,
                    paths_source=source_paths or None,
                    force_json_response=False,
                )

            st.session_state[get_ocaml_test_generation_llm_response_key(tp_name)] = response
            generated_tests = strip_llm_code_fences(response)
            if generated_tests is None:
                st.error("La réponse de l'IA n'a pas pu être convertie en fichier de tests OCaml exploitable.")
            else:
                test_path = save_generated_ocaml_tests(tp_name, generated_tests)
                st.session_state[overwrite_authorization_key] = False
                st.success(f"Le fichier de tests a été généré et sauvegardé dans `{test_path.name}`.")
                st.rerun()

        generation_llm_response_key = get_ocaml_test_generation_llm_response_key(tp_name)
        if generation_llm_response_key in st.session_state:
            with st.expander("Afficher la réponse brute de l'IA pour les tests OCaml"):
                with st.container(height=520):
                    st.write(st.session_state[generation_llm_response_key])

        if test_source_path.exists():
            with st.expander("Prévisualiser le fichier `test_code_rendu.ml` actuel"):
                with st.container(height=520):
                    st.code(read_text_file(str(test_source_path)), language="ocaml", line_numbers=True, wrap_lines=True)

        if tests_dir.exists():
            st.subheader("Contenu actuel du dossier `dune_tests/`")
            current_files = []
            for path in sorted(tests_dir.iterdir(), key=lambda item: item.name.lower()):
                current_files.append({"Fichier": path.name, "Type": "Dossier" if path.is_dir() else "Fichier"})
            if current_files:
                st.dataframe(current_files, width="stretch", hide_index=True)


def get_ocaml_compiled_exe_path(tp_name: str, student_name: str) -> Path:
    """Return the path of the compiled OCaml binary for one student render."""
    return Path("/tmp") / f"test_ocaml__{slugify_for_filename(tp_name)}__{slugify_for_filename(student_name)}.exe"


def compile_ocaml_submission(
    student_dir: Path, code_path: Path, compiled_exe_path: Path
) -> tuple[int, Path, Path, str]:
    """Compile one OCaml submission and persist the compiler output."""
    log_path = get_ocaml_compile_log_path(student_dir)
    exit_code, output = run_command_and_capture_output(
        ["ocamlopt", "-color", "never", "-ccopt", "-static", "-o", str(compiled_exe_path), code_path.name],
        cwd=student_dir,
        log_path=log_path,
    )
    return exit_code, compiled_exe_path, log_path, output


def interpret_ocaml_submission_in_nsjail(
    student_dir: Path, code_path: Path
) -> tuple[int, Path, str]:
    """Interpret one OCaml submission and persist the interpreter output."""
    log_path = get_ocaml_interpret_log_path(student_dir)
    nsjail_config = ROOT_DIR / "nsjail_config.cfg"
    exit_code, output = run_command_and_capture_output(
        ["nsjail", "--config", str(nsjail_config), "--", str(OCAML_INTERPRETER_PATH), "-color", "never"],
        cwd=student_dir,
        log_path=log_path,
        input_path=code_path,
    )
    return exit_code, log_path, output


def run_ocaml_submission_in_nsjail(student_dir: Path, compiled_exe_path: Path) -> tuple[int, Path, str]:
    """Run one compiled OCaml binary inside NsJail and persist the output."""
    log_path = get_ocaml_exec_log_path(student_dir)
    nsjail_config = ROOT_DIR / "nsjail_config.cfg"
    exit_code, output = run_command_and_capture_output(
        ["nsjail", "--config", str(nsjail_config), "--", str(compiled_exe_path)],
        cwd=student_dir,
        log_path=log_path,
    )
    return exit_code, log_path, output


def load_json_object(path: Path) -> object | None:
    """Load a JSON file safely and return None when it cannot be parsed."""
    try:
        raw_text = read_text_file(str(path))
    except (OSError, json.JSONDecodeError):
        return None

    candidate_text = raw_text.lstrip()
    if not candidate_text:
        return None

    if not candidate_text.startswith(("{", "[")):
        first_object_pos = candidate_text.find("{")
        first_array_pos = candidate_text.find("[")
        candidate_positions = [pos for pos in (first_object_pos, first_array_pos) if pos != -1]
        if not candidate_positions:
            return None
        candidate_text = candidate_text[min(candidate_positions) :]

    try:
        parsed_value, _ = json.JSONDecoder().raw_decode(candidate_text)
    except json.JSONDecodeError:
        return None
    return parsed_value

def compute_ocaml_tests_note_sur_20(successes: object, failures: object) -> float:
    """Compute an automatic note on 20 from the summary of an OCaml test run."""
    if not isinstance(successes, (int, float)) or not isinstance(failures, (int, float)):
        return 0.0

    total_tests = float(successes) + float(failures)
    if total_tests <= 0:
        return 0.0

    return round(20 * float(successes) / total_tests, 2)


def run_ocaml_dune_tests(
    tp_name: str, code_path: Path, json_mode: bool
) -> tuple[int, Path, Path, str]:
    """Copy one OCaml submission into the shared dune tests and run them."""
    tests_dir = get_ocaml_tests_dir(tp_name)
    tests_dir.mkdir(parents=True, exist_ok=True)

    dune_code_path = tests_dir / "code_rendu.ml"
    shutil.copy2(code_path, dune_code_path)

    log_path = get_ocaml_test_log_path(tp_name)
    artifact_path = get_ocaml_test_json_path(tp_name) if json_mode else get_ocaml_test_html_path(tp_name)

    command: list[str | Path] = [
        "dune",
        "exec",
        # "--print-metrics",
        # "--verbose",
        "--display=quiet",
        "./test_code_rendu.exe",
        "--",
        "--show-errors",
        "--compact",
    ]
    if json_mode:
        command.append("--color")
        command.append("never")
        command.append("--json")
    else:
        command.append("--color")
        command.append("always")

    exit_code, output = run_command_and_capture_output(
        command,
        cwd=tests_dir,
        log_path=log_path,
    )

    artifact_path.write_text(output, encoding="utf-8")
    if not json_mode:
        artifact_path.write_text(ansi_log_to_html(output), encoding="utf-8")
    read_text_file.clear()
    return exit_code, log_path, artifact_path, output


def build_default_bareme(tp_name: str, question_count: int) -> dict[str, object]:
    """Create an in-memory marking scheme with numbered questions and default scores."""
    questions: list[QuestionConfig] = [
        {"index": index, "label": f"Question {index}", "points": DEFAULT_QUESTION_POINTS}
        for index in range(1, question_count + 1)
    ]
    return {
        "format_version": 1,
        "tp_name": tp_name,
        "question_count": question_count,
        "total_points": sum(question["points"] for question in questions),
        "questions": questions,
    }


def normalize_bareme_data(tp_name: str, data: dict[str, object] | None) -> dict[str, object]:
    """Sanitize loaded JSON data and rebuild a consistent marking scheme structure."""
    if not isinstance(data, dict):
        return build_default_bareme(tp_name, DEFAULT_QUESTION_COUNT)

    raw_question_count = data.get("question_count", DEFAULT_QUESTION_COUNT)
    question_count = raw_question_count if isinstance(raw_question_count, int) else DEFAULT_QUESTION_COUNT
    question_count = max(1, question_count)

    raw_questions = data.get("questions", [])
    normalized_questions: list[QuestionConfig] = []
    if isinstance(raw_questions, list):
        for index, question in enumerate(raw_questions[:question_count], start=1):
            points = DEFAULT_QUESTION_POINTS
            label = f"Question {index}"
            if isinstance(question, dict):
                raw_points = question.get("points", 0)
                raw_label = question.get("label", label)
                if isinstance(raw_points, (int, float)):
                    points = int(max(0, min(100, raw_points)))
                if isinstance(raw_label, str) and raw_label.strip():
                    label = raw_label
            normalized_questions.append({"index": index, "label": label, "points": points})

    for index in range(len(normalized_questions) + 1, question_count + 1):
        normalized_questions.append(
            {"index": index, "label": f"Question {index}", "points": DEFAULT_QUESTION_POINTS}
        )

    return {
        "format_version": 1,
        "tp_name": tp_name,
        "question_count": question_count,
        "total_points": sum(get_question_points(question) for question in normalized_questions),
        "questions": normalized_questions,
    }


def load_bareme(tp_name: str) -> dict[str, object]:
    """Load a saved marking scheme from disk, or create a default one when absent."""
    bareme_path = get_bareme_path(tp_name)
    if not bareme_path.exists():
        return build_default_bareme(tp_name, DEFAULT_QUESTION_COUNT)

    try:
        loaded_data = json.loads(read_text_file(str(bareme_path)))
    except (OSError, json.JSONDecodeError):
        return build_default_bareme(tp_name, DEFAULT_QUESTION_COUNT)

    return normalize_bareme_data(tp_name, loaded_data if isinstance(loaded_data, dict) else None)


def save_bareme(tp_name: str, bareme_data: dict[str, object]) -> None:
    """Persist the current marking scheme as formatted JSON in the subject directory."""
    bareme_path = get_bareme_path(tp_name)
    bareme_to_save = normalize_bareme_data(tp_name, bareme_data)
    bareme_path.write_text(json.dumps(bareme_to_save, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def get_bareme_session_key(tp_name: str) -> str:
    """Return the Streamlit session key used to store a TP-specific marking scheme."""
    return f"bareme::{tp_name}"


def get_bareme_points_widget_key(tp_name: str, question_index: int) -> str:
    """Return the widget key used by the point editor for one question."""
    return f"bareme_points::{tp_name}::{question_index}"


def get_bareme_label_widget_key(tp_name: str, question_index: int) -> str:
    """Return the widget key used by the label editor for one question."""
    return f"bareme_label::{tp_name}::{question_index}"


def get_bareme_llm_response_key(tp_name: str) -> str:
    """Return the session key used to store the last AI-generated marking scheme response."""
    return f"bareme_llm_response::{tp_name}"


def sync_bareme_widgets(tp_name: str, bareme_data: dict[str, object]) -> None:
    """Copy one marking scheme into the Streamlit widget state for the current TP."""
    for question in get_bareme_questions(bareme_data):
        question_index = get_question_index(question)
        st.session_state[get_bareme_label_widget_key(tp_name, question_index)] = get_question_label(question)
        st.session_state[get_bareme_points_widget_key(tp_name, question_index)] = get_question_points(question)


def set_bareme_data(
    tp_name: str, bareme_data: dict[str, object], *, sync_widgets: bool = True
) -> dict[str, object]:
    """Normalize and store a TP marking scheme in session state, optionally syncing its widgets."""
    normalized_bareme = normalize_bareme_data(tp_name, bareme_data)
    st.session_state[get_bareme_session_key(tp_name)] = normalized_bareme
    if sync_widgets:
        sync_bareme_widgets(tp_name, normalized_bareme)
    return normalized_bareme


def parse_llm_json_object(response: object) -> dict[str, object] | None:
    """Extract a JSON object from a raw LLM response when possible."""
    if isinstance(response, dict):
        return response

    if isinstance(response, str):
        payload = response.strip()
        if payload.startswith("```"):
            lines = payload.splitlines()
            if lines:
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            payload = "\n".join(lines).strip()

        try:
            parsed_response = json.loads(payload)
        except json.JSONDecodeError:
            return None
        return parsed_response if isinstance(parsed_response, dict) else None

    return None


def build_bareme_from_llm_response(tp_name: str, response: object) -> tuple[dict[str, object] | None, str | None]:
    """Validate one AI response and convert it into a normalized marking scheme."""
    parsed_response = parse_llm_json_object(response)
    if parsed_response is None:
        return None, "La réponse de l'IA n'est pas un objet JSON exploitable."

    raw_questions = parsed_response.get("questions")
    if not isinstance(raw_questions, list) or not raw_questions:
        return None, "La réponse de l'IA ne contient pas de liste de questions exploitable."

    candidate_bareme = dict(parsed_response)
    candidate_bareme["tp_name"] = tp_name
    return normalize_bareme_data(tp_name, candidate_bareme), None


# Grading helpers keep the editor, saved JSON, and AI proposals aligned.


def get_grading_llm_response_key(tp_name: str, student_name: str) -> str:
    """Return the session key used to store the last AI-generated grading response."""
    return f"grading_llm_response::{tp_name}::{student_name}"


def set_grading_data(
    tp_name: str,
    student_name: str,
    bareme_questions: list[dict[str, object]],
    grading_data: dict[str, object],
    *,
    sync_widgets: bool = True,
) -> dict[str, object]:
    """Normalize and store one student's grading data, optionally syncing its widgets."""
    normalized_grading = normalize_grading_data(tp_name, student_name, bareme_questions, grading_data)
    st.session_state[get_grading_session_key(tp_name, student_name)] = normalized_grading
    if sync_widgets:
        sync_grading_widgets(tp_name, student_name, normalized_grading)
    return normalized_grading


def build_grading_from_llm_response(
    tp_name: str,
    student_name: str,
    bareme_questions: list[dict[str, object]],
    response: object,
) -> tuple[dict[str, object] | None, str | None]:
    """Validate one AI response and convert it into normalized grading data."""
    parsed_response = parse_llm_json_object(response)
    if parsed_response is None:
        return None, "La réponse de l'IA n'est pas un objet JSON exploitable."

    raw_questions = parsed_response.get("questions")
    if not isinstance(raw_questions, list) or not raw_questions:
        return None, "La réponse de l'IA ne contient pas de liste de questions exploitable."

    candidate_grading = dict(parsed_response)
    candidate_grading["tp_name"] = tp_name
    candidate_grading["student_name"] = student_name
    return normalize_grading_data(tp_name, student_name, bareme_questions, candidate_grading), None


def get_grading_points_widget_key(tp_name: str, student_name: str, question_index: int) -> str:
    """Return the widget key used by the grading editor for one student question."""
    return f"grading_points::{tp_name}::{student_name}::{question_index}"


def get_grading_session_key(tp_name: str, student_name: str) -> str:
    """Return the Streamlit session key used to store one student's grading data."""
    return f"grading::{tp_name}::{student_name}"


def get_grading_selection_key(tp_name: str) -> str:
    """Return the session key tracking the currently loaded student for one practical session."""
    return f"grading_selection::{tp_name}"


def build_default_grading_data(
    tp_name: str, student_name: str, bareme_questions: list[dict[str, object]]
) -> dict[str, object]:
    """Create default grading data for one student from the current marking scheme."""
    graded_questions: list[GradedQuestion] = []
    for question in bareme_questions:
        graded_questions.append(
            {
                "index": get_question_index(question),
                "label": get_question_label(question),
                "max_points": get_question_points(question),
                "points_awarded": 0,
            }
        )

    total_points_bareme = sum(get_question_points(question) for question in bareme_questions)
    return {
        "format_version": 1,
        "tp_name": tp_name,
        "student_name": student_name,
        "question_count": len(graded_questions),
        "total_points_awarded": 0,
        "total_points_bareme": total_points_bareme,
        "note_sur_20": 0.0,
        "questions": graded_questions,
    }


def normalize_grading_data(
    tp_name: str,
    student_name: str,
    bareme_questions: list[dict[str, object]],
    data: dict[str, object] | None,
) -> dict[str, object]:
    """Sanitize persisted grading data and align it with the current marking scheme."""
    default_data = build_default_grading_data(tp_name, student_name, bareme_questions)
    if not isinstance(data, dict):
        return default_data

    raw_questions = data.get("questions", [])
    persisted_by_index: dict[int, int] = {}
    if isinstance(raw_questions, list):
        for question in raw_questions:
            if not isinstance(question, dict):
                continue
            raw_index = question.get("index", 0)
            raw_points_awarded = question.get("points_awarded", 0)
            if isinstance(raw_index, int) and isinstance(raw_points_awarded, (int, float)):
                persisted_by_index[raw_index] = int(raw_points_awarded)

    normalized_questions: list[GradedQuestion] = []
    total_points_awarded = 0
    total_points_bareme = sum(get_question_points(question) for question in bareme_questions)
    for question in bareme_questions:
        question_index = get_question_index(question)
        max_points = get_question_points(question)
        points_awarded = max(0, min(max_points, persisted_by_index.get(question_index, 0)))
        total_points_awarded += points_awarded
        normalized_questions.append(
            {
                "index": question_index,
                "label": get_question_label(question),
                "max_points": max_points,
                "points_awarded": points_awarded,
            }
        )

    note_sur_20 = round(20 * total_points_awarded / float(total_points_bareme), 2) if total_points_bareme else 0.0
    return {
        "format_version": 1,
        "tp_name": tp_name,
        "student_name": student_name,
        "question_count": len(normalized_questions),
        "total_points_awarded": total_points_awarded,
        "total_points_bareme": total_points_bareme,
        "note_sur_20": note_sur_20,
        "questions": normalized_questions,
    }


def load_grading_data(
    tp_name: str, student_name: str, student_dir: Path, bareme_questions: list[dict[str, object]]
) -> dict[str, object]:
    """Load persisted grading data for one student, or build a default empty grading sheet."""
    notes_path = get_notes_path(student_dir)
    if not notes_path.exists():
        return build_default_grading_data(tp_name, student_name, bareme_questions)

    try:
        loaded_data = json.loads(read_text_file(str(notes_path)))
    except (OSError, json.JSONDecodeError):
        return build_default_grading_data(tp_name, student_name, bareme_questions)

    return normalize_grading_data(
        tp_name,
        student_name,
        bareme_questions,
        loaded_data if isinstance(loaded_data, dict) else None,
    )


def save_grading_data(student_dir: Path, grading_data: dict[str, object]) -> None:
    """Persist one student's grading data as formatted JSON in the submission directory."""
    notes_path = get_notes_path(student_dir)
    notes_path.write_text(json.dumps(grading_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sync_grading_widgets(tp_name: str, student_name: str, grading_data: dict[str, object]) -> None:
    """Copy persisted grading values into the Streamlit widget state for one student."""
    raw_questions = grading_data.get("questions", [])
    if not isinstance(raw_questions, list):
        return

    for question in raw_questions:
        if not isinstance(question, dict):
            continue
        question_index = question.get("index", 0)
        points_awarded = question.get("points_awarded", 0)
        if isinstance(question_index, int) and isinstance(points_awarded, (int, float)):
            widget_key = get_grading_points_widget_key(tp_name, student_name, question_index)
            st.session_state[widget_key] = int(points_awarded)


def get_grading_data(
    tp_name: str, student_name: str | None, student_dir: Path | None, bareme_questions: list[dict[str, object]]
) -> dict[str, object] | None:
    """Return the current in-session grading data for the selected student."""
    if not student_name or student_dir is None:
        return None

    session_key = get_grading_session_key(tp_name, student_name)
    if session_key not in st.session_state:
        set_grading_data(
            tp_name,
            student_name,
            bareme_questions,
            load_grading_data(tp_name, student_name, student_dir, bareme_questions),
        )
    else:
        # Reopening the evaluation mode can reuse persisted session data while the
        # associated number-input widgets have not been recreated yet. Re-sync the
        # widget state here so the first displayed student immediately reflects
        # the latest known grading values.
        set_grading_data(
            tp_name,
            student_name,
            bareme_questions,
            st.session_state[session_key],
            sync_widgets=True,
        )

    return st.session_state[session_key]


def ensure_selected_grading_loaded(
    tp_name: str, student_name: str | None, student_dir: Path | None, bareme_questions: list[dict[str, object]]
) -> None:
    """Load grading data from disk when the selected student changes in evaluation mode."""
    selection_key = get_grading_selection_key(tp_name)
    current_signature = student_name if student_name is not None else ""
    previous_signature = st.session_state.get(selection_key, "")

    if current_signature == previous_signature:
        return

    st.session_state[selection_key] = current_signature
    if not student_name or student_dir is None:
        return

    loaded_grading_data = load_grading_data(tp_name, student_name, student_dir, bareme_questions)
    set_grading_data(tp_name, student_name, bareme_questions, loaded_grading_data)


def get_current_grading_summary(
    tp_name: str, student_name: str | None, bareme_questions: list[dict[str, object]]
) -> tuple[int, int, float]:
    """Compute the current grading summary from the widget state for one student."""
    total_points_bareme = sum(get_question_points(question) for question in bareme_questions)
    if not student_name or not bareme_questions:
        return 0, total_points_bareme, 0.0

    total_points = 0
    for question in bareme_questions:
        question_index = get_question_index(question)
        widget_key = get_grading_points_widget_key(tp_name, student_name, question_index)
        raw_grade = st.session_state.get(widget_key, 0)
        grade = int(raw_grade) if isinstance(raw_grade, (int, float)) else 0
        total_points += max(0, min(get_question_points(question), grade))

    note_sur_20 = round(20 * total_points / float(total_points_bareme), 2) if total_points_bareme else 0.0
    return total_points, total_points_bareme, note_sur_20


def summarize_numeric_values(values: list[float]) -> dict[str, float]:
    """Compute a compact statistical summary for a numeric series."""
    if not values:
        return {"mean": 0.0, "median": 0.0, "min": 0.0, "max": 0.0, "stddev": 0.0}

    return {
        "mean": round(statistics.fmean(values), 2),
        "median": round(statistics.median(values), 2),
        "min": round(min(values), 2),
        "max": round(max(values), 2),
        "stddev": round(statistics.pstdev(values), 2) if len(values) > 1 else 0.0,
    }


# Statistics helpers power the class and yearly synthesis views.


def compute_linear_trend_slope(values: list[float]) -> float:
    """Compute the slope of the best-fit first-order regression line for a numeric series."""
    if len(values) < 2:
        return 0.0

    x_values = [float(index) for index in range(len(values))]
    x_mean = statistics.fmean(x_values)
    y_mean = statistics.fmean(values)
    numerator = sum((x_value - x_mean) * (y_value - y_mean) for x_value, y_value in zip(x_values, values))
    denominator = sum((x_value - x_mean) ** 2 for x_value in x_values)
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 3)


def get_record_student_name(record: dict[str, object]) -> str:
    """Extract a student name from a class record."""
    raw_student_name = record.get("student_name", "")
    return raw_student_name if isinstance(raw_student_name, str) else ""


def get_record_total_points(record: dict[str, object]) -> float:
    """Extract awarded total points from a class record."""
    raw_total_points = record.get("total_points", 0)
    return float(raw_total_points) if isinstance(raw_total_points, (int, float)) else 0.0


def get_record_note_sur_20(record: dict[str, object]) -> float:
    """Extract the global grade on 20 from a class record."""
    raw_note_sur_20 = record.get("note_sur_20", 0.0)
    return float(raw_note_sur_20) if isinstance(raw_note_sur_20, (int, float)) else 0.0


def get_record_question_points(record: dict[str, object]) -> list[int]:
    """Extract per-question awarded points from a class record."""
    raw_question_points = record.get("question_points", [])
    if not isinstance(raw_question_points, list):
        return []

    points: list[int] = []
    for value in raw_question_points:
        points.append(int(value) if isinstance(value, (int, float)) else 0)
    return points


def get_classroom_int(stats: dict[str, object], key: str) -> int:
    """Extract an integer value from classroom statistics."""
    raw_value = stats.get(key, 0)
    return raw_value if isinstance(raw_value, int) else 0


def get_classroom_str_list(stats: dict[str, object], key: str) -> list[str]:
    """Extract a string list from classroom statistics."""
    raw_value = stats.get(key, [])
    if not isinstance(raw_value, list):
        return []
    return [value for value in raw_value if isinstance(value, str)]


def get_classroom_summary(stats: dict[str, object], key: str) -> dict[str, float]:
    """Extract a numeric summary mapping from classroom statistics."""
    raw_value = stats.get(key, {})
    if not isinstance(raw_value, dict):
        return summarize_numeric_values([])

    return {
        "mean": float(raw_value.get("mean", 0.0)) if isinstance(raw_value.get("mean", 0.0), (int, float)) else 0.0,
        "median": float(raw_value.get("median", 0.0)) if isinstance(raw_value.get("median", 0.0), (int, float)) else 0.0,
        "min": float(raw_value.get("min", 0.0)) if isinstance(raw_value.get("min", 0.0), (int, float)) else 0.0,
        "max": float(raw_value.get("max", 0.0)) if isinstance(raw_value.get("max", 0.0), (int, float)) else 0.0,
        "stddev": float(raw_value.get("stddev", 0.0)) if isinstance(raw_value.get("stddev", 0.0), (int, float)) else 0.0,
    }


def get_classroom_rows(stats: dict[str, object], key: str) -> list[dict[str, object]]:
    """Extract a list of rows from classroom statistics."""
    raw_value = stats.get(key, [])
    if not isinstance(raw_value, list):
        return []
    return [row for row in raw_value if isinstance(row, dict)]


def get_row_float(row: dict[str, object], key: str) -> float:
    """Extract one float-like value from a generic row dictionary."""
    raw_value = row.get(key, 0.0)
    return float(raw_value) if isinstance(raw_value, (int, float)) else 0.0


def find_student_dir_for_tp(tp_name: str, student_name: str) -> Path | None:
    """Find a student's submission directory for one practical session."""
    return next((path for path in discover_student_dirs(tp_name) if path.name == student_name), None)


def build_classroom_statistics(tp_name: str, bareme_questions: list[dict[str, object]]) -> dict[str, object]:
    """Aggregate saved student grades into class-level statistics for one practical session."""
    student_dirs = discover_student_dirs(tp_name)
    evaluated_records: list[dict[str, object]] = []
    pending_students: list[str] = []

    for student_dir in student_dirs:
        if not has_saved_grading(student_dir):
            pending_students.append(student_dir.name)
            continue

        grading_data = load_grading_data(tp_name, student_dir.name, student_dir, bareme_questions)
        raw_questions = grading_data.get("questions", [])
        awarded_by_index: dict[int, int] = {}
        if isinstance(raw_questions, list):
            for question in raw_questions:
                if not isinstance(question, dict):
                    continue
                raw_index = question.get("index", 0)
                raw_points_awarded = question.get("points_awarded", 0)
                if isinstance(raw_index, int) and isinstance(raw_points_awarded, (int, float)):
                    awarded_by_index[raw_index] = int(raw_points_awarded)

        question_points = [awarded_by_index.get(get_question_index(question), 0) for question in bareme_questions]
        total_points = sum(question_points)
        total_points_bareme = sum(get_question_points(question) for question in bareme_questions)
        note_sur_20 = round(20 * total_points / float(total_points_bareme), 2) if total_points_bareme else 0.0
        evaluated_records.append(
            {
                "student_name": student_dir.name,
                "question_points": question_points,
                "total_points": total_points,
                "total_points_bareme": total_points_bareme,
                "note_sur_20": note_sur_20,
            }
        )

    global_notes = [get_record_note_sur_20(record) for record in evaluated_records]
    global_totals = [get_record_total_points(record) for record in evaluated_records]
    question_rows: list[dict[str, object]] = []
    for position, question in enumerate(bareme_questions):
        label = get_question_label(question)
        bareme_points = get_question_points(question)
        question_values = [float(get_record_question_points(record)[position]) for record in evaluated_records]
        summary = summarize_numeric_values(question_values)
        question_rows.append(
            {
                "Question": label,
                "Barème": bareme_points,
                "Moyenne": summary["mean"],
                "Médiane": summary["median"],
                "Minimum": summary["min"],
                "Maximum": summary["max"],
                "Écart-type": summary["stddev"],
            }
        )

    notes_summary = summarize_numeric_values(global_notes)
    totals_summary = summarize_numeric_values(global_totals)

    sorted_records = sorted(evaluated_records, key=get_record_note_sur_20, reverse=True)
    student_notes_rows = [
        {"Étudiant": get_record_student_name(record), "Note /20": get_record_note_sur_20(record)}
        for record in sorted_records
    ]

    return {
        "student_count": len(student_dirs),
        "evaluated_count": len(evaluated_records),
        "pending_count": len(pending_students),
        "pending_students": pending_students,
        "notes_summary": notes_summary,
        "totals_summary": totals_summary,
        "student_notes_rows": student_notes_rows,
        "per_question_rows": question_rows,
    }


def build_individual_progress_statistics(student_name: str) -> dict[str, object]:
    """Aggregate saved grades across all practical sessions for one student."""
    evaluated_rows: list[dict[str, object]] = []
    pending_tp_names: list[str] = []
    missing_submission_tp_names: list[str] = []

    for tp_name in discover_tp_names():
        student_dir = find_student_dir_for_tp(tp_name, student_name)
        if student_dir is None:
            missing_submission_tp_names.append(tp_name)
            continue

        bareme_data = load_bareme(tp_name)
        bareme_questions = get_bareme_questions(bareme_data)
        if not has_saved_grading(student_dir):
            pending_tp_names.append(tp_name)
            continue

        grading_data = load_grading_data(tp_name, student_name, student_dir, bareme_questions)
        raw_total_points = grading_data.get("total_points_awarded", 0)
        raw_total_points_bareme = grading_data.get("total_points_bareme", 0)
        raw_note_sur_20 = grading_data.get("note_sur_20", 0.0)
        total_points = int(raw_total_points) if isinstance(raw_total_points, (int, float)) else 0
        total_points_bareme = int(raw_total_points_bareme) if isinstance(raw_total_points_bareme, (int, float)) else 0
        note_sur_20 = float(raw_note_sur_20) if isinstance(raw_note_sur_20, (int, float)) else 0.0
        ratio = round(total_points / float(total_points_bareme), 3) if total_points_bareme else 0.0
        evaluated_rows.append(
            {
                "TP": tp_name,
                "Note /20": round(note_sur_20, 2),
                "Points obtenus": total_points,
                "Barème total": total_points_bareme,
                "Taux de réussite": ratio,
            }
        )

    notes = [get_row_float(row, "Note /20") for row in evaluated_rows]
    points = [get_row_float(row, "Points obtenus") for row in evaluated_rows]
    notes_summary = summarize_numeric_values(notes)
    points_summary = summarize_numeric_values(points)
    progression_delta = compute_linear_trend_slope(notes)

    return {
        "evaluated_tp_count": len(evaluated_rows),
        "pending_tp_count": len(pending_tp_names),
        "missing_submission_tp_count": len(missing_submission_tp_names),
        "pending_tp_names": pending_tp_names,
        "missing_submission_tp_names": missing_submission_tp_names,
        "notes_summary": notes_summary,
        "points_summary": points_summary,
        "progression_delta": progression_delta,
        "evaluated_rows": evaluated_rows,
    }


def get_bareme_data(tp_name: str) -> dict[str, object]:
    """Return the current in-session marking scheme for a practical session."""
    session_key = get_bareme_session_key(tp_name)
    if session_key not in st.session_state:
        st.session_state[session_key] = load_bareme(tp_name)
    return normalize_bareme_data(tp_name, st.session_state[session_key])


def get_bareme_question_count(bareme_data: dict[str, object]) -> int:
    """Extract a validated question count from a normalized marking scheme."""
    raw_question_count = bareme_data.get("question_count", DEFAULT_QUESTION_COUNT)
    return raw_question_count if isinstance(raw_question_count, int) else DEFAULT_QUESTION_COUNT


def get_bareme_questions(bareme_data: dict[str, object]) -> list[dict[str, object]]:
    """Extract the normalized list of questions from a marking scheme."""
    raw_questions = bareme_data.get("questions", [])
    return raw_questions if isinstance(raw_questions, list) else []


def get_question_index(question: QuestionConfig | GradedQuestion | dict[str, object]) -> int:
    """Extract a validated question index from a normalized question entry."""
    raw_index = question.get("index", 0)
    return raw_index if isinstance(raw_index, int) else 0


def get_question_label(question: QuestionConfig | GradedQuestion | dict[str, object]) -> str:
    """Extract a display label from a normalized question entry."""
    raw_label = question.get("label", "")
    return raw_label if isinstance(raw_label, str) else ""


def get_question_points(question: QuestionConfig | dict[str, object]) -> int:
    """Extract a validated integer score from a normalized question entry."""
    raw_points = question.get("points", 0)
    return int(raw_points) if isinstance(raw_points, (int, float)) else 0


def update_bareme_question_count(tp_name: str, question_count: int) -> dict[str, object]:
    """Resize the in-session marking scheme while preserving existing point allocations."""
    bareme_data = get_bareme_data(tp_name)
    existing_questions = bareme_data.get("questions", [])
    existing_points: list[int] = []
    if isinstance(existing_questions, list):
        for question in existing_questions:
            if isinstance(question, dict) and isinstance(question.get("points"), (int, float)):
                existing_points.append(int(max(0, min(100, question["points"]))))

    resized_bareme = build_default_bareme(tp_name, question_count)
    questions = resized_bareme["questions"]
    if isinstance(questions, list):
        for index, question in enumerate(questions):
            if index < len(existing_points):
                question["points"] = existing_points[index]

    return set_bareme_data(tp_name, resized_bareme)


def update_all_question_points(tp_name: str, points: int) -> dict[str, object]:
    """Apply the same score to every question in the in-session marking scheme."""
    bareme_data = get_bareme_data(tp_name)
    updated_questions = []
    for question in get_bareme_questions(bareme_data):
        updated_questions.append(
            {
                "index": get_question_index(question),
                "label": get_question_label(question),
                "points": points,
            }
        )

    updated_bareme = {
        "format_version": 1,
        "tp_name": tp_name,
        "question_count": len(updated_questions),
        "questions": updated_questions,
    }
    return set_bareme_data(tp_name, updated_bareme)


# Rendering helpers split the UI by workflow so each mode stays readable.


def render_pdf(path: Path, height: int = 720) -> None:
    """Embed a local PDF in the Streamlit page through a data URL."""
    encoded = base64.b64encode(read_binary_file(str(path))).decode("ascii")

    # Keep the embedded PDF readable while avoiding the left-side page thumbnails.
    pdf_params = "#pagemode=none&view=FitH&toolbar=1"

    src_url = f"data:application/pdf;base64,{encoded}{pdf_params}"

    iframe = f"""
    <iframe
        src="{src_url}"
        width="100%"
        height="{height}"
        style="border: 1px solid rgba(148, 163, 184, 0.35); border-radius: 14px; background: white;"
    ></iframe>
    """
    st.iframe(iframe, height=height + 30)


def detect_language(path: Path) -> str:
    """Map supported source file extensions to Streamlit syntax highlighters."""
    if path.suffix == ".c":
        return "c"
    if path.suffix == ".ml":
        return "ocaml"
    return "text"


def render_subject_panel(tp_name: str, height=820) -> None:
    """Render the subject PDF and LaTeX metadata for the selected practical session."""
    subject_pdf = find_subject_pdf(tp_name)
    tex_files = find_subject_tex_files(tp_name)
    markdown_files = find_subject_markdown_files(tp_name)

    st.subheader("Sujet du TP")
    if subject_pdf is not None:
        render_pdf(subject_pdf, height=height)
        st.caption(f"PDF détecté : `{subject_pdf.name}`")
    else:
        st.warning("Aucun PDF de sujet n'a été trouvé pour ce TP.")

    if tex_files:
        tex_names = ", ".join(f"`{path.name}`" for path in tex_files)
        st.caption(f"Sources LaTeX détectées : {tex_names}")

    if markdown_files:
        markdown_names = ", ".join(f"`{path.name}`" for path in markdown_files)
        st.caption(f"Sources Markdown détectées : {markdown_names}")


def render_bareme_mode(tp_name: str) -> None:
    """Render the marking scheme editor and persist it in the session state."""

    st.title(f"Rédaction du barème de notation - `{tp_name}`")
    st.caption(
        "Mode de préparation du barème du TP sélectionné, avec sauvegarde locale, rechargement et proposition assistée par IA."
    )

    bareme_data = get_bareme_data(tp_name)
    question_count = get_bareme_question_count(bareme_data)
    questions = get_bareme_questions(bareme_data)
    total_points = sum(get_question_points(question) for question in questions)

    subject_col, bareme_col = st.columns((1.1, 1), gap="large")

    with subject_col:
        render_subject_panel(tp_name)

    with bareme_col:
        st.subheader("Conception et écriture du barème")
        summary_col_questions, summary_col_total = st.columns(2)
        summary_col_questions.metric("Nombre de questions", question_count)
        summary_col_total.metric("Total de points", total_points)

        requested_question_count = int(
            st.number_input(
                "Choix du nombre de questions",
                min_value=1,
                max_value=100,
                value=question_count,
                step=1,
                help=f"Ajuste le nombre de questions à noter pour le TP courant. La valeur par défaut est {DEFAULT_QUESTION_COUNT}.",
            )
        )

        uniform_points_state_key = f"bareme_uniform_editor::{tp_name}"
        uniform_points_input_key = f"bareme_uniform_points::{tp_name}"
        if uniform_points_state_key not in st.session_state:
            st.session_state[uniform_points_state_key] = False
        if uniform_points_input_key not in st.session_state:
            st.session_state[uniform_points_input_key] = DEFAULT_QUESTION_POINTS

        if st.button("Appliquer un même barème à toutes les questions", width='stretch'):
            st.session_state[uniform_points_state_key] = not st.session_state[uniform_points_state_key]

        if st.button("✨ Proposer un barème automatique par IA ? ✨", width='stretch', help=f"Analyse le sujet PDF et ses sources LaTeX et Markdown, pour proposer un barème qui pourra être sauvegardé dans un fichier local. {help_credits_llm}"):
            # On construit le prompt
            prompt = """
Analyse ce sujet de Travaux Pratiques d'Informatique, je t'ai joint le sujet du TP, avec ses sources LaTeX ou Markdown.
Tu vas identifier les exercices et questions.

**Propose un barème, avec chaque questions entre 1 et 10 points (1 point si question très facile, 10 points si question plutôt dure), en respectant la difficulté relative des notions (ex: récursivité terminale en OCaml vs manipulation de pointeurs en C).**

Renvoie uniquement un JSON sous cette forme (par exemple) :

```json
{ "format_version": 1, "tp_name": "37-graphes-euleriens", "question_count": NOMBRE, "total_points": TOTAL, "questions": [ { "index": 1, "label": "Question XXXVII.1.1", "points": 2 }, { "index": 2, "label": "Question XXXVII.1.2", "points": 7 }, { "index": 3, "label": "Question XXXVII.2.1", "points": 5 }, { "index": 2, "label": "Question XXXVII.2.2", "points": 10 }, ... { "index": 15, "label": "Question XXXVII.9.1", "points": 10 } ] }
```
            """

            system_prompt = SYSTEM_PROMPT

            subject_pdf = find_subject_pdf(tp_name)
            tex_files = find_subject_tex_files(tp_name)
            markdown_files = find_subject_markdown_files(tp_name)

            with st.spinner("Génération du barème en cours grâce à l'IA..."):
                response = response_from_llm(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    paths_pdf=[subject_pdf],
                    paths_source=
                        tex_files
                        + markdown_files
                    ,
                    force_json_response=True,
                )
            st.session_state[get_bareme_llm_response_key(tp_name)] = response

            llm_bareme, error_message = build_bareme_from_llm_response(tp_name, response)
            if llm_bareme is None:
                st.error(error_message or "La réponse de l'IA n'a pas pu être convertie en barème.")
            else:
                set_bareme_data(tp_name, llm_bareme)
                st.session_state[uniform_points_state_key] = False
                st.success("Le barème proposé par l'IA a été injecté dans l'éditeur courant.")
                st.rerun()

        bareme_llm_response_key = get_bareme_llm_response_key(tp_name)
        if bareme_llm_response_key in st.session_state:
            with st.expander("Afficher la réponse brute de l'IA pour le barème (JSON)"):
                with st.container(height=520):
                    st.json(st.session_state[bareme_llm_response_key])

        if st.session_state[uniform_points_state_key]:
            uniform_points = int(
                st.number_input(
                    "Barème unique pour toutes les questions",
                    min_value=0,
                    max_value=100,
                    step=1,
                    key=uniform_points_input_key,
                )
            )
            if st.button("Valider la mise à jour globale", type="primary", width='stretch'):
                st.session_state[uniform_points_state_key] = False
                update_all_question_points(tp_name, uniform_points)
                st.rerun()

        if requested_question_count != question_count:
            bareme_data = update_bareme_question_count(tp_name, requested_question_count)
            question_count = get_bareme_question_count(bareme_data)
            questions = get_bareme_questions(bareme_data)

        updated_questions: list[QuestionConfig] = []
        questions_container = st.container(height=550, border=True)
        with questions_container:
            st.caption("Édition du barème par question")
            for question in questions:
                question_index = get_question_index(question)
                default_label = get_question_label(question)
                label_widget_key = get_bareme_label_widget_key(tp_name, question_index)
                if label_widget_key not in st.session_state:
                    st.session_state[label_widget_key] = default_label

                label_col, points_col = st.columns((2.4, 1), gap="small")
                with label_col:
                    edited_label = st.text_input(
                        f"Libellé de la question {question_index}",
                        value=default_label,
                        key=label_widget_key,
                    ).strip()
                with points_col:
                    points = int(
                        st.number_input(
                            f"Points pour la question {question_index}",
                            min_value=0,
                            max_value=100,
                            value=get_question_points(question),
                            step=1,
                            key=get_bareme_points_widget_key(tp_name, question_index),
                        )
                    )

                updated_questions.append(
                    {
                        "index": question_index,
                        "label": edited_label or f"Question {question_index}",
                        "points": points,
                    }
                )

        bareme_data = {
            "format_version": 1,
            "tp_name": tp_name,
            "question_count": question_count,
            "total_points": sum(get_question_points(question) for question in updated_questions),
            "questions": updated_questions,
        }
        set_bareme_data(tp_name, bareme_data, sync_widgets=False)

        total_points = sum(get_question_points(question) for question in updated_questions)
        st.caption(f"Barème courant : {question_count} questions, {total_points} points au total.")

        if st.button("Sauvegarder le barème", type="primary"):
            save_bareme(tp_name, bareme_data)
            read_text_file.clear()
            st.success(f"Barème sauvegardé dans {get_bareme_path(tp_name).name}.")


def render_submissions_mode(tp_name: str) -> None:
    """Render the original submission review workflow for a practical session."""
    student_dirs: list[Path] = discover_student_dirs(tp_name)
    student_names: list[str] = [path.name for path in student_dirs]
    bareme_data = get_bareme_data(tp_name)
    bareme_questions = get_bareme_questions(bareme_data)
    selected_student_name = st.sidebar.selectbox(
        "Choisir un rendu étudiant",
        student_names,
        index=0 if student_names else None,
        placeholder="Aucun rendu disponible",
    )

    selected_student_dir: Path | None = None
    if selected_student_name:
        selected_student_dir = next((path for path in student_dirs if path.name == selected_student_name), None)

    code_path: Path | None = None
    report_pdf: Path | None = None
    report_md: Path | None = None
    if selected_student_dir is not None:
        code_path = find_student_code(selected_student_dir)
        report_pdf = find_student_report_pdf(selected_student_dir)
        report_md = find_student_report_markdown(selected_student_dir)

    ensure_selected_grading_loaded(tp_name, selected_student_name, selected_student_dir, bareme_questions)
    grading_data = get_grading_data(tp_name, selected_student_name, selected_student_dir, bareme_questions)

    total_points, total_points_bareme, note_sur_20 = get_current_grading_summary(
        tp_name, selected_student_name, bareme_questions
    )
    ocaml_tests_note_key = f"ocaml_tests_note::{tp_name}::{selected_student_name or ''}"
    raw_ocaml_tests_note = st.session_state.get(ocaml_tests_note_key)
    ocaml_tests_note_sur_20 = (
        float(raw_ocaml_tests_note) if isinstance(raw_ocaml_tests_note, (int, float)) else None
    )

    st.title(f"Évaluation des rendus de TP - `{tp_name}`")
    st.caption(
        "Mode d'évaluation des rendus pour parcourir un sujet de TP, consulter les rendus et préparer l'évaluation automatique."
    )
    col_rendus, col_etudiant, col_total, col_note, col_tests_note = st.columns(5)
    col_rendus.metric("**Nombre de rendus détectés**", len(student_dirs))
    col_etudiant.metric("**Étudiant sélectionné**", f"**{selected_student_name}**" or "aucun")
    col_total.metric("**Points obtenus**", f"{total_points} / {total_points_bareme}")
    col_note.metric("**Note par lecture des rendus**", f"{note_sur_20}/20")
    col_tests_note.metric(
        "**Note aux tests automatiques**",
        f"{ocaml_tests_note_sur_20}/20" if ocaml_tests_note_sur_20 is not None else "—",
    )

    subject_col, grading_col, student_col = st.columns((0.7, 0.3, 0.8), gap="small")

    with subject_col:
        render_subject_panel(tp_name)

    with grading_col:
        st.subheader("Évaluation du rendu")
        if selected_student_dir is None:
            st.info("Sélectionnez un rendu étudiant pour saisir l'évaluation question par question.")
        elif not bareme_questions:
            st.warning("Aucun barème n'est disponible pour ce TP. Commencez par renseigner le mode « 1 - Barème ».")
        else:
            student_identifier = selected_student_name or ""

            if selected_student_name and selected_student_dir is not None:
                if st.button(
                    "✨ Proposer une notation automatique par IA ? ✨",
                    width='stretch',
                    help=f"Analyse le sujet, le barème sauvegardé, le code rendu et le compte-rendu pour proposer une notation question par question. {help_credits_llm}",
                ):
                    prompt = f"""
Analyse ce rendu de Travaux Pratiques d'Informatique.

Je te donne :
- le sujet du TP en PDF et ses sources LaTeX,
- le barème JSON courant du sujet,
- le code rendu par l'étudiant,
- le compte-rendu de l'étudiant en Markdown, ou en PDF si le Markdown n'est pas disponible.

Évalue chaque question du barème. Attribue un nombre entier de points entre 0 et le maximum de la question.
Calcule ensuite le total des points obtenus et la note sur 20 correspondante.

Réponds uniquement avec un JSON de cette forme (par exemple) :

```json
{{ "format_version": 1, "tp_name": "{tp_name}", "student_name": "{selected_student_name}", "question_count": {len(bareme_questions)}, "total_points_awarded": 57, "total_points_bareme": {sum(get_question_points(question) for question in bareme_questions)}, "note_sur_20": 12.67, "questions": [ {{ "index": 1, "label": "Question 1", "max_points": 10, "points_awarded": 10 }}, ..., {{ "index": {len(bareme_questions)}, "label": "Question {len(bareme_questions)}", "max_points": 10, "points_awarded": 9 }} ] }}
```

Ne renvoie aucune explication, aucun commentaire et aucun texte hors JSON.
                    """

                    system_prompt = SYSTEM_PROMPT

                    subject_pdf = find_subject_pdf(tp_name)
                    tex_files = find_subject_tex_files(tp_name)
                    markdown_files = find_subject_markdown_files(tp_name)
                    bareme_path = get_bareme_path(tp_name)
                    pdf_paths: list[Path] = []
                    if subject_pdf is not None:
                        pdf_paths.append(subject_pdf)
                    if report_md is None and report_pdf is not None:
                        pdf_paths.append(report_pdf)

                    source_paths: list[Path] = list(tex_files) + list(markdown_files)
                    if code_path is not None:
                        source_paths.append(code_path)
                    if report_md is not None:
                        source_paths.append(report_md)

                    json_paths: list[Path] = []
                    if bareme_path.exists():
                        json_paths.append(bareme_path)

                    additional_messages: list[str] | None = None
                    if not json_paths:
                        additional_messages = [
                            "Barème JSON courant :\n" + json.dumps(bareme_data, ensure_ascii=False, indent=2)
                        ]

                    with st.spinner("Génération de l'évaluation de ce rendu de TP, en cours grâce à l'IA ..."):
                        response = response_from_llm(
                            prompt=prompt,
                            system_prompt=system_prompt,
                            additionnal_messages=additional_messages,
                            paths_pdf=pdf_paths or None,
                            paths_json=json_paths or None,
                            paths_source=source_paths or None,
                            force_json_response=True,
                        )

                    st.session_state[get_grading_llm_response_key(tp_name, selected_student_name)] = response
                    llm_grading, error_message = build_grading_from_llm_response(
                        tp_name,
                        selected_student_name,
                        bareme_questions,
                        response,
                    )
                    if llm_grading is None:
                        st.error(error_message or "La réponse de l'IA n'a pas pu être convertie en notation.")
                    else:
                        set_grading_data(tp_name, selected_student_name, bareme_questions, llm_grading)
                        st.success("La notation proposée par l'IA a été injectée dans l'éditeur courant.")
                        st.rerun()

                grading_llm_response_key = get_grading_llm_response_key(tp_name, selected_student_name)
                if grading_llm_response_key in st.session_state:
                    with st.expander("Afficher la réponse brute de l'IA pour la notation (JSON)"):
                        with st.container(height=420):
                            st.json(st.session_state[grading_llm_response_key])

            updated_grades: list[int] = []
            updated_questions: list[GradedQuestion] = []
            with st.container(height=720):
                for question in bareme_questions:
                    question_index = get_question_index(question)
                    question_label = get_question_label(question)
                    max_points = get_question_points(question)
                    input_col_label, input_col_value = st.columns((2.2, 1), gap="small")
                    with input_col_label:
                        st.markdown(f"**{question_label}**")
                    with input_col_value:
                        widget_key = get_grading_points_widget_key(tp_name, student_identifier, question_index)
                        if widget_key not in st.session_state:
                            st.session_state[widget_key] = 0
                        grade = int(
                            st.number_input(
                                f"Points pour {question_label}",
                                min_value=0,
                                max_value=max_points,
                                step=1,
                                key=widget_key,
                                label_visibility="collapsed",
                            )
                        )
                    updated_grades.append(grade)
                    updated_questions.append(
                        {
                            "index": question_index,
                            "label": question_label,
                            "max_points": max_points,
                            "points_awarded": grade,
                        }
                    )
                    st.caption(f"Maximum : {max_points} point{'s' if max_points > 1 else ''}")

            total_points = sum(updated_grades)
            note_sur_20 = round(20 * total_points / float(total_points_bareme), 2) if total_points_bareme else 0.0
            if selected_student_name:
                grading_data = {
                    "format_version": 1,
                    "tp_name": tp_name,
                    "student_name": selected_student_name,
                    "question_count": len(updated_questions),
                    "total_points_awarded": total_points,
                    "total_points_bareme": total_points_bareme,
                    "note_sur_20": note_sur_20,
                    "questions": updated_questions,
                }
                set_grading_data(tp_name, selected_student_name, bareme_questions, grading_data, sync_widgets=False)

                if st.button("Sauvegarder la notation", type="primary", width='stretch'):
                    save_grading_data(selected_student_dir, grading_data)
                    read_text_file.clear()
                    st.success(f"Notation sauvegardée dans {get_notes_path(selected_student_dir).name}.")

    with student_col:
        st.subheader("Fichiers rendus par l'étudiant")
        if selected_student_dir is None:
            st.info("Aucun rendu étudiant disponible pour ce TP.")
        else:
            tabs = st.tabs(["Code source", "Rapport PDF", "Compte-rendu (Markdown)", "Fichiers rendus"])

            with tabs[0]:
                if code_path is None:
                    st.warning("Aucun fichier source rendu n'a été trouvé.")
                else:
                    code = read_text_file(str(code_path))
                    st.code(code, language=detect_language(code_path), line_numbers=True, wrap_lines=True, height=720)
                    st.caption(f"Fichier affiché : {code_path.name}")

            with tabs[1]:
                if report_pdf is not None:
                    render_pdf(report_pdf, height=720)
                    st.caption(f"Compte-rendu PDF affiché : {report_pdf.name}")
                else:
                    st.warning("Aucun compte-rendu PDF n'a été trouvé.")

            with tabs[2]:
                if report_md is not None:
                    with st.container(height=720):
                        st.markdown(read_text_file(str(report_md)))
                    st.caption(f"Fichier affiché : {report_md.name}")
                else:
                    st.warning("Aucun compte-rendu Markdown n'a été trouvé.")

            with tabs[3]:
                for path in sorted(selected_student_dir.iterdir(), key=lambda item: item.name.lower()):
                    label = "Dossier" if path.is_dir() else "Fichier"
                    st.write(f"- {label} : `{path.name}`")


    st.divider()
    st.subheader("Outils d'évaluation de code OCaml semi-automatisé")
    st.caption(
        "Aucune action n'est lancée automatiquement : la compilation, l'exécution NsJail et les tests Dune ne démarrent qu'après clic explicite sur un bouton."
    )

    if selected_student_dir is None or code_path is None:
        st.info("Sélectionnez d'abord un rendu étudiant contenant un fichier `code_rendu.ml` pour activer ces actions.")
        return

    if code_path.suffix != ".ml":
        st.warning("Les actions à la demande sont pour l'instant réservées aux rendus OCaml (`code_rendu.ml`).")
        return

    compiled_exe_path = get_ocaml_compiled_exe_path(tp_name, selected_student_name or "")
    ocaml_tools_tabs = st.tabs(["A - Compiler", "B - Interpréter dans la safebox", "C - Exécuter dans la safebox", "D - Tests complets", "E - (TODO) Auto-évaluation complète en un clic"])

    with ocaml_tools_tabs[0]:
        st.write("Compiler le fichier OCaml rendu, mais sans prendre encore le risque de lancer le binaire (il faut rester un peu prudent).")
        compile_button_key = f"ocaml_compile_button::{tp_name}::{selected_student_name}"
        if st.button("Compiler le rendu OCaml (ocamlopt)", key=compile_button_key, type="primary", width='stretch'):
            exit_code, compiled_exe_path, log_path, output = compile_ocaml_submission(selected_student_dir, code_path, compiled_exe_path)
            if exit_code == 0:
                st.success(f"Compilation réussie, terminée avec succès, le binaire est disponible dans {compiled_exe_path}.")
            else:
                st.warning(f"Compilation échouée, terminée avec le code de retour {exit_code}.")

            st.markdown("**Sortie de cette commande Bash (log)**")
            # st.code(output, language="bash", line_numbers=True, wrap_lines=True)

            render_code_log(
                log_path,
                detect_language(code_path),
                "Aucun log de compilation n'est encore disponible. Cliquez sur le bouton de compilation pour en générer un.",
            )

    with ocaml_tools_tabs[1]:
        st.write("Interpréter le fichier OCaml rendu en montrant les sorties (ligne par ligne).")
        interpret_button_key = f"ocaml_interpret_button::{tp_name}::{selected_student_name}"
        if st.button("Interpréter le rendu OCaml", key=interpret_button_key, type="primary", width='stretch'):
            exit_code, log_path, output = interpret_ocaml_submission_in_nsjail(selected_student_dir, code_path)
            if exit_code == 0:
                st.success(f"Interprétration réussie, terminée avec succès.")
            else:
                st.warning(f"Interprétration échouée, terminée avec le code de retour {exit_code}.")

            st.markdown("**Sortie de cette commande Bash (log)**")
            # st.code(output, language="bash", line_numbers=True, wrap_lines=True)

            render_code_log(
                log_path,
                detect_language(code_path),
                "Aucun log de compilation n'est encore disponible. Cliquez sur le bouton de compilation pour en générer un.",
            )

    with ocaml_tools_tabs[2]:
        st.write("Exécuter le binaire compilé dans une sandbox NsJail.")
        run_button_key = f"ocaml_run_button::{tp_name}::{selected_student_name}"
        if st.button("Exécuter dans une safebox (NsJail)", key=run_button_key, type="primary", width='stretch'):
            if not compiled_exe_path.exists():
                st.error(
                    f"Le binaire {compiled_exe_path} n'existe pas encore : compilez d'abord le rendu OCaml."
                )
            else:
                exit_code, _, output = run_ocaml_submission_in_nsjail(selected_student_dir, compiled_exe_path)
                if exit_code == 0:
                    st.success("Exécution NsJail terminée avec succès.")

                    # st.markdown("**Sortie de cette commande Bash (log)**")
                    # st.code(output, language="bash", line_numbers=True, wrap_lines=True)

                    render_code_log(
                        get_ocaml_exec_log_path(selected_student_dir),
                        detect_language(code_path),
                        "Aucun log d'exécution n'est encore disponible. Cliquez sur le bouton d'exécution pour en générer un.",
                    )
                else:
                    st.warning(f"Exécution NsJail terminée avec le code de retour {exit_code}.")

    with ocaml_tools_tabs[3]:
        st.write("Copier le rendu OCaml dans le banc de tests Dune partagé, puis lancer les tests (QCheck + Alcotest) préparés à la main.")
        test_button_key = f"ocaml_test_button::{tp_name}::{selected_student_name}"
        tests_dir = get_ocaml_tests_dir(tp_name)
        if not tests_dir.exists():
            st.info(
                f"Le dossier partagé des tests est absent pour ce TP : {tests_dir}. Il sera créé automatiquement au premier lancement."
            )

        if st.button("Lancer les tests (Dune)", key=test_button_key, type="primary", width='stretch'):
            exit_code, log_path, artifact_path, output = run_ocaml_dune_tests(
                tp_name, code_path, json_mode=False
            )
            if exit_code == 0:
                st.success(f"Tests Dune terminés entièrement avec succès. Le rendu a été généré dans `{artifact_path.name}`.")
            else:
                st.success(f"Tests Dune terminés avec une erreur, et le code de retour {exit_code}. Le rendu a-t-il été généré dans `{artifact_path.name}` ?")

            # TODO: je veux aussi afficher le JSON ?
            exit_code_json, log_path_json, artifact_path_json, output_json = run_ocaml_dune_tests(
                tp_name, code_path, json_mode=True
            )

            st.markdown("**Sortie de cette commande Bash (log)**")
            # st.code(output, language="bash", line_numbers=True, wrap_lines=True)

            test_html_tab, test_log_tab = st.tabs(["Jolie sortie", "Log brut"])
            with test_html_tab:
                if artifact_path_json and artifact_path_json.exists():
                    json_payload = load_json_object(artifact_path_json)
                    if json_payload is None:
                        st.error(
                            f"Le fichier JSON/HTML {artifact_path_json.name} n'a pas pu être lu correctement."
                        )
                        st.code(read_text_file(str(artifact_path)), language="json", line_numbers=True, wrap_lines=True, height=520)
                    else:
                        # st.json(json_payload)
                        if isinstance(json_payload, dict):
                            json_payload_dict = cast(dict[str, object], json_payload)
                            success = json_payload_dict.get("success")
                            failures = json_payload_dict.get("failures")
                            time = json_payload_dict.get("time")
                            ocaml_tests_note_sur_20 = compute_ocaml_tests_note_sur_20(success, failures)
                            st.session_state[ocaml_tests_note_key] = ocaml_tests_note_sur_20

                            st.metric("**Note aux tests automatiques**", f"{ocaml_tests_note_sur_20}/20")
                            st.caption(
                                f"Résumé des tests OCaml : {success} succès, {failures} échec{'s' if int(str(failures)) > 0 else ''}, temps d'exécution {time}s."
                            )
                        else:
                            st.warning("Le contenu JSON des tests n'a pas le format attendu.")
                # HTML, by default
                # else:
                render_html_log(
                    artifact_path,
                    "Aucun rendu HTML des tests Dune n'est encore disponible. Cliquez sur le bouton de tests pour en générer un.",
                )
            with test_log_tab:
                render_code_log(
                    log_path,
                    detect_language(code_path),
                    "Aucun log de tests Dune n'est encore disponible. Cliquez sur le bouton de tests pour en générer un.",
                )

    with ocaml_tools_tabs[4]:
        st.write("Lancer un processus complet d'évaluation quasi-automatique du code rendu par l'étudiant, de la compilation à la lecture du fichier JSON produit par Alcotest (`dune exec`).")
        pass
        # TODO: ici, il faudrait un bouton qui fasse le job de la compilation (étape "A - Compiler") et ("D - Tests complets") en un seul clic... pas facile ?


def render_classroom_mode(tp_name: str) -> None:
    """Render the class-level overview for one practical session from saved student grades."""
    bareme_data = get_bareme_data(tp_name)
    bareme_questions = get_bareme_questions(bareme_data)

    st.title(f"Vue de la classe par TP - `{tp_name}`")
    st.caption(
        "Tableau de bord de synthèse pour visualiser les notes déjà sauvegardées de toute la classe sur ce TP."
    )

    if not bareme_questions:
        st.warning("Aucun barème n'est disponible pour ce TP. Commencez par renseigner le mode « 1 - Barème ».")
        return

    classroom_stats = build_classroom_statistics(tp_name, bareme_questions)
    evaluated_count = get_classroom_int(classroom_stats, "evaluated_count")
    if evaluated_count == 0:
        st.info("Aucune notation sauvegardée n'a encore été trouvée pour ce TP. Commencez par évaluer au moins un rendu.")
        return

    notes_summary = get_classroom_summary(classroom_stats, "notes_summary")
    totals_summary = get_classroom_summary(classroom_stats, "totals_summary")
    student_notes_rows = get_classroom_rows(classroom_stats, "student_notes_rows")
    per_question_rows = get_classroom_rows(classroom_stats, "per_question_rows")
    pending_count = get_classroom_int(classroom_stats, "pending_count")
    student_count = get_classroom_int(classroom_stats, "student_count")
    pending_students = get_classroom_str_list(classroom_stats, "pending_students")

    top_row_1, top_row_2, top_row_3, top_row_4 = st.columns(4)
    top_row_1.metric("Rendus détectés", student_count)
    top_row_2.metric("Évaluations sauvegardées", evaluated_count)
    top_row_3.metric("Moyenne générale", f"{notes_summary['mean']}/20")
    top_row_4.metric("Écart-type global", f"{notes_summary['stddev']}")

    second_row_1, second_row_2, second_row_3, second_row_4 = st.columns(4)
    second_row_1.metric("Médiane générale", f"{notes_summary['median']}/20")
    second_row_2.metric("Note minimale", f"{notes_summary['min']}/20")
    second_row_3.metric("Note maximale", f"{notes_summary['max']}/20")
    second_row_4.metric("Moyenne en points", f"{totals_summary['mean']} pts")

    st.caption(
        f"Les statistiques ci-dessous portent sur {evaluated_count} rendu{'s' if evaluated_count > 1 else ''} déjà noté{'s' if evaluated_count > 1 else ''}."
    )
    if pending_count:
        pending_preview = ", ".join(str(name) for name in pending_students[:8])
        suffix = "..." if pending_count > 8 else ""
        st.info(f"{pending_count} rendu(x) restent sans `notes.json` pour ce TP : {pending_preview}{suffix}")

    chart_col_left, chart_col_right = st.columns((1.15, 1), gap="large")
    with chart_col_left:
        st.subheader("Répartition des notes de la classe")
        if student_notes_rows:
                notes_chart_rows: list[dict[str, object]] = []
                for row in student_notes_rows:
                    notes_chart_rows.append({**row, "TP": tp_name})

                notes_chart = (
                    alt.Chart(alt.Data(values=notes_chart_rows))
                    .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
                    .encode(
                        x=alt.X("Étudiant:N", sort=None, title="Étudiant", axis=alt.Axis(labelAngle=45)),
                        y=alt.Y("Note /20:Q", scale=alt.Scale(domain=[0, 20]), title="Note /20"),
                        color=alt.Color(
                            "Note /20:Q",
                            scale=alt.Scale(domain=[0, 20], range=["#c62828", "#1565c0"]),
                            legend=alt.Legend(title="Note /20"),
                        ),
                        tooltip=[
                            alt.Tooltip("TP:N", title="TP"),
                            alt.Tooltip("Étudiant:N", title="Étudiant"),
                            alt.Tooltip("Note /20:Q", title="Note", format=".2f"),
                        ],
                    )
                    .properties(height=320, title=f"Répartition des notes pour {tp_name}")
                )
                st.altair_chart(notes_chart, width='stretch')
                st.dataframe(student_notes_rows, width='stretch', hide_index=True)

    with chart_col_right:
        st.subheader("Moyenne par question vs barème")
        if per_question_rows:
            st.bar_chart(per_question_rows, x="Question", y=["Moyenne", "Barème"], stack=False)
            st.caption("Lecture rapide : la barre « Moyenne » se compare directement au nombre de points disponibles au barème.")

    st.subheader("Dispersion par question")
    if per_question_rows:
        st.line_chart(per_question_rows, x="Question", y=["Minimum", "Médiane", "Maximum"])
        st.caption("Chaque question affiche son minimum, sa médiane et son maximum observés dans la classe.")

    st.subheader("Statistiques détaillées par question")
    if per_question_rows:
        st.dataframe(per_question_rows, width='stretch', hide_index=True)

    with st.expander("Afficher le sujet du TP pour contextualiser la vue de classe"):
        render_subject_panel(tp_name)


def render_individual_progress_mode() -> None:
    """Render an annual progress dashboard for one selected student across all practical sessions."""
    student_names: list[str] = discover_all_student_names()

    st.title("Progression annuelle individuelle")
    st.caption(
        "Vue transversale pour suivre l'évolution d'un étudiant au fil des TP évalués pendant l'année."
    )

    if not student_names:
        st.info("Aucun étudiant n'a encore été détecté dans les dossiers de rendus.")
        return

    selected_student_name = st.selectbox(
        "Choisir un étudiant",
        student_names,
        index=0,
        key="individual_progress_selected_student",
        help="La progression annuelle agrège les fichiers `notes.json` déjà sauvegardés pour cet étudiant sur l'ensemble des TP.",
    )

    progress_stats = build_individual_progress_statistics(selected_student_name)
    evaluated_tp_count = get_classroom_int(progress_stats, "evaluated_tp_count")
    pending_tp_count = get_classroom_int(progress_stats, "pending_tp_count")
    missing_submission_tp_count = get_classroom_int(progress_stats, "missing_submission_tp_count")
    notes_summary = get_classroom_summary(progress_stats, "notes_summary")
    points_summary = get_classroom_summary(progress_stats, "points_summary")
    progression_delta = get_row_float(progress_stats, "progression_delta")
    evaluated_rows = get_classroom_rows(progress_stats, "evaluated_rows")
    pending_tp_names = get_classroom_str_list(progress_stats, "pending_tp_names")
    missing_submission_tp_names = get_classroom_str_list(progress_stats, "missing_submission_tp_names")

    if evaluated_tp_count == 0:
        st.info("Aucune note sauvegardée n'a encore été trouvée pour cet étudiant sur l'année.")
        if pending_tp_names:
            st.caption(f"TP avec rendu mais sans évaluation sauvegardée : {', '.join(pending_tp_names)}")
        return

    summary_row_1, summary_row_2, summary_row_3, summary_row_4 = st.columns(4)
    summary_row_1.metric("TP évalués", evaluated_tp_count)
    summary_row_2.metric("Moyenne annuelle", f"{notes_summary['mean']}/20")
    summary_row_3.metric("Note minimale", f"{notes_summary['min']}/20")
    summary_row_4.metric("Note maximale", f"{notes_summary['max']}/20")

    summary_row_5, summary_row_6, summary_row_7, summary_row_8 = st.columns(4)
    summary_row_5.metric("Médiane", f"{notes_summary['median']}/20")
    summary_row_6.metric("Écart-type", f"{notes_summary['stddev']}")
    summary_row_7.metric("Pente de tendance", f"{progression_delta:+.3f}")
    summary_row_8.metric("Moyenne en points", f"{points_summary['mean']} pts")

    st.caption(
        f"Cette vue calcule une moyenne *non pondérée* sur {evaluated_tp_count} TP noté{'s' if evaluated_tp_count > 1 else ''} pour {selected_student_name}."
    )

    status_col_left, status_col_right = st.columns((1, 1), gap="large")
    with status_col_left:
        if pending_tp_count:
            preview = ", ".join(pending_tp_names[:8])
            suffix = "..." if pending_tp_count > 8 else ""
            st.info(f"TP déjà rendus mais encore sans `notes.json` : {preview}{suffix}")
    with status_col_right:
        if missing_submission_tp_count:
            preview = ", ".join(missing_submission_tp_names[:8])
            suffix = "..." if missing_submission_tp_count > 8 else ""
            st.caption(f"TP sans dossier de rendu détecté : {preview}{suffix}")

    charts_col_left, charts_col_right = st.columns((1.2, 1), gap="large")
    with charts_col_left:
        st.subheader("Trajectoire des notes au fil des TP")
        timeline_rows: list[dict[str, object]] = []
        for row in evaluated_rows:
            timeline_rows.append({**row, "Étudiant": selected_student_name})
        notes_timeline_chart = (
            alt.Chart(alt.Data(values=timeline_rows))
            .mark_line(point=alt.OverlayMarkDef(filled=True, size=90), strokeWidth=3)
            .encode(
                x=alt.X("TP:N", sort=None, title="TP"),
                y=alt.Y("Note /20:Q", scale=alt.Scale(domain=[0, 20]), title="Note /20"),
                color=alt.Color(
                    "Note /20:Q",
                    scale=alt.Scale(domain=[0, 20], range=["#c62828", "#1565c0"]),
                    legend=None,
                ),
                tooltip=[
                    alt.Tooltip("Étudiant:N", title="Étudiant"),
                    alt.Tooltip("TP:N", title="TP"),
                    alt.Tooltip("Note /20:Q", title="Note", format=".2f"),
                    alt.Tooltip("Points obtenus:Q", title="Points"),
                    alt.Tooltip("Barème total:Q", title="Barème total"),
                ],
            )
            .properties(height=340, title=f"Progression de {selected_student_name}")
        )
        st.altair_chart(notes_timeline_chart, width="stretch")

    with charts_col_right:
        st.subheader("Comparaison note / moyenne personnelle")
        reference_rows: list[dict[str, object]] = []
        personal_mean = notes_summary["mean"]
        for row in evaluated_rows:
            tp_name = row.get("TP", "") if isinstance(row.get("TP", ""), str) else ""
            note_value = row.get("Note /20", 0.0)
            reference_rows.append(
                {
                    "TP": tp_name,
                    "Note /20": float(note_value) if isinstance(note_value, (int, float)) else 0.0,
                    "Moyenne personnelle": personal_mean,
                }
            )
        st.bar_chart(reference_rows, x="TP", y=["Note /20", "Moyenne personnelle"], stack=False)
        st.caption("Chaque TP est comparé à la moyenne annuelle de l'étudiant pour repérer rapidement les hausses et les baisses.")

    # st.subheader("Rythme de réussite")
    # success_chart = (
    #     alt.Chart(alt.Data(values=timeline_rows))
    #     .mark_area(opacity=0.55)
    #     .encode(
    #         x=alt.X("TP:N", sort=None, title="TP"),
    #         y=alt.Y("Taux de réussite:Q", scale=alt.Scale(domain=[0, 1]), title="Taux de réussite"),
    #         color=alt.Color(
    #             "Taux de réussite:Q",
    #             scale=alt.Scale(domain=[0, 1], range=["#ef9a9a", "#1e88e5"]),
    #             legend=None,
    #         ),
    #         tooltip=[
    #             alt.Tooltip("Étudiant:N", title="Étudiant"),
    #             alt.Tooltip("TP:N", title="TP"),
    #             alt.Tooltip("Taux de réussite:Q", title="Taux", format=".1%"),
    #         ],
    #     )
    #     .properties(height=220, title=f"Taux de réussite de {selected_student_name}")
    # )
    # st.altair_chart(success_chart, width="stretch")

    st.subheader("Historique détaillé")
    st.dataframe(evaluated_rows, width="stretch", hide_index=True)


def render_documentation_mode() -> None:
    """Render an integrated help page describing the dashboard workflows."""
    tp_names = discover_tp_names()
    student_names = discover_all_student_names()
    submission_count = sum(len(discover_student_dirs(tp_name)) for tp_name in tp_names)

    st.title("Documentation intégrée du dashboard")
    st.caption(
        "Cette page résume le fonctionnement de l'outil, l'ordre conseillé d'utilisation et les fichiers produits pendant l'évaluation."
    )

    top_col_1, top_col_2, top_col_3 = st.columns(3)
    top_col_1.metric("TP détectés", len(tp_names))
    top_col_2.metric("Rendus détectés", submission_count)
    top_col_3.metric("Étudiants détectés", len(student_names))

    st.subheader("Prise en main rapide")
    st.markdown(
        """
        1. Choisir le mode `1 - Barème` pour préparer le barème d'un TP.
        2. Vérifier le sujet affiché à gauche, puis renseigner ou faire proposer les questions et leurs points.
        3. Passer au mode `2 - Génération automatisée de tests OCaml` pour préparer un banc de tests Dune/Alcotest/QCheck.
        4. Passer au mode `3 - Évaluation des rendus` pour noter un étudiant question par question.
        5. Sauvegarder les notes, puis consulter les synthèses dans les modes `4` et `5`.
        """
    )

    st.subheader("Rôle de chaque mode")
    mode_rows = [
        {
            "Mode": "0 - Documentation",
            "Usage": "Relire le fonctionnement de l'application, les conventions de fichiers et l'ordre conseillé des actions.",
        },
        {
            "Mode": "1 - Barème",
            "Usage": "Définir le nombre de questions, leurs libellés, leurs points et sauvegarder le `bareme.json` du TP.",
        },
        {
            "Mode": "2 - Génération automatisée de tests OCaml",
            "Usage": "Créer un banc de tests OCaml Dune/Alcotest/QCheck si aucun `test_code_rendu.ml` n'est encore présent.",
        },
        {
            "Mode": "3 - Évaluation des rendus",
            "Usage": "Ouvrir un rendu étudiant, lire son code et son rapport, puis saisir ou pré-remplir la notation avant sauvegarde.",
        },
        {
            "Mode": "4 - Vue de la classe par TP",
            "Usage": "Consulter les statistiques globales d'un TP à partir des `notes.json` déjà sauvegardés.",
        },
        {
            "Mode": "5 - Progression annuelle individuelle",
            "Usage": "Suivre un étudiant sur l'ensemble des TP déjà évalués durant l'année.",
        },
    ]
    st.dataframe(mode_rows, width="stretch", hide_index=True)

    left_col, right_col = st.columns((1, 1), gap="large")
    with left_col:
        st.subheader("Fichiers attendus")
        st.markdown(
            """
            - `sujets-de-travaux-pratiques/<tp>/` contient le sujet, idéalement en PDF, avec éventuellement ses sources LaTeX ou Markdown.
            - `rendus-des-etudiants/<tp>/<etudiant>/` contient le code rendu et, si disponible, un compte-rendu PDF ou Markdown.
            - Le dashboard recherche en priorité `code_rendu.c` ou `code_rendu.ml`.
            - Les noms `compte-rendu.pdf`, `compte_rendu.pdf`, `compte-rendu.md` et `compte_rendu.md` sont reconnus automatiquement.
            """
        )

        st.subheader("Fichiers générés")
        st.markdown(
            """
            - `bareme.json` est sauvegardé dans le dossier du TP.
            - `notes.json` est sauvegardé dans le dossier du rendu étudiant.
            - Les vues de synthèse lisent uniquement ces fichiers sauvegardés.
            """
        )

    with right_col:
        st.subheader("Fonctionnalités IA")
        st.markdown(
            f"""
            - Le mode `1 - Barème` peut proposer un barème automatique à partir du sujet et de ses sources.
            - Le mode `2 - Génération automatisée de tests OCaml` peut générer automatiquement un fichier `test_code_rendu.ml` s'il n'existe pas encore, à partir du sujet et du barème courant.
            - Le mode `3 - Évaluation des rendus` peut proposer une notation automatique à partir du sujet, du barème, du code et du compte-rendu.
            - Les modes `1` et `3` injectent leur proposition IA dans l'éditeur courant, puis restent modifiables avant sauvegarde.
            - Le mode `2` écrit directement un fichier `test_code_rendu.ml` dans `dune_tests/` si la génération est demandée.
            - À propos de ces requêtes AI : {help_credits_llm}
            """
        )

        st.subheader("Conseils d'usage")
        st.markdown(
            """
            - Commencer par sauvegarder un barème stable avant d'évaluer plusieurs étudiants.
            - Relire les propositions IA avant sauvegarde, surtout si le sujet ou le rendu est incomplet.
            - Utiliser les vues de synthèse uniquement après avoir sauvegardé les notations individuelles.
            """
        )

    with st.expander("Afficher les TP actuellement détectés"):
        if tp_names:
            st.write("- " + "\n- ".join(tp_names))
        else:
            st.info("Aucun TP n'est actuellement détecté dans le dépôt.")


def render_placeholder_mode(tp_name: str, mode_name: str) -> None:
    """Render a placeholder for future dashboard modes that are not implemented yet."""
    st.title("Dashboard d'évaluation et de pilotage des TP")
    st.caption("Cette vue est réservée aux prochains développements du dashboard.")
    col_mode, col_tp = st.columns(2)
    col_mode.metric("Mode", mode_name)
    col_tp.metric("TP", tp_name)
    st.info(f"Le mode « {mode_name} » sera ajouté dans une prochaine version.")


def main() -> None:
    """Build the Streamlit interface and wire repository discovery to UI widgets."""
    st.set_page_config(
        page_title="Évaluator TP MP2I @ Lycée Kléber (par Lilian BESSON)",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    tp_names = discover_tp_names()

    st.sidebar.title(f"*Évaluator* TP info MP2I")

    st.sidebar.subheader("Navigation")
    selected_mode = st.sidebar.selectbox("Choisir un mode", APP_MODES, index=0)

    if selected_mode == "0 - Documentation":
        render_documentation_mode()
    elif not tp_names:
        st.error("Aucun TP n'a été trouvé dans le dossier des sujets.")
        return
    elif selected_mode == "1 - Barème":
        selected_tp = st.sidebar.selectbox("Choisir un TP pour lequel il faut rédiger son barème", tp_names)
        render_bareme_mode(selected_tp)

    elif selected_mode == "2 - Génération IA de tests OCaml":
        selected_tp = st.sidebar.selectbox("Choisir un TP pour lequel il faut générer les tests OCaml", tp_names)
        render_ocaml_tests_generation_mode(selected_tp)
    elif selected_mode == "3 - Évaluation des rendus":
        selected_tp = st.sidebar.selectbox("Choisir un TP pour lequel il faut évaluer les documents rendus par la classe", tp_names)
        render_submissions_mode(selected_tp)
    elif selected_mode == "4 - Vue de la classe par TP":
        selected_tp = st.sidebar.selectbox("Choisir un TP pour lequel il faut visualiser les performances de la classe", tp_names)
        render_classroom_mode(selected_tp)
    elif selected_mode == "5 - Progression annuelle individuelle":
        render_individual_progress_mode()
    else:
        render_placeholder_mode("TODO: TP à sélectionner", selected_mode)

    st.sidebar.subheader("À propos de cet outil ?")
    st.sidebar.markdown("Vous avez des *idées* ? Un *bug* à signaler ? [Ouvrez un ticket sur GitHub](https://github.com/Naereen/Auto-Eval-TP-info-MP2I-via-LLM/issues/new) !")
    st.sidebar.markdown("Ce dashboard utilise Python 3 et streamlit, et a été développé en avril 2026, par [Lilian BESSON](https://github.com/Naereen/) pour les TP de la MP2I au Lycée Kléber. Le code source est disponible sur [GitHub](https://github.com/Naereen/Auto-Eval-TP-info-MP2I-via-LLM), sous [license libre MIT](https://lbesson.mit-license.org/).")
    st.sidebar.caption("*Note* : des outils d'IA génératives ✨, comme [Google Gemini](https://gemini.google.com/) et [GitHub Copilot](https://github.com/copilot/), m'ont aidés à produire \"rapidement\" cette démo d'une idée de micro-logiciel.")

    if LOGO_LYCEE:
        st.sidebar.image(str(ROOT_DIR / LOGO_LYCEE), width=120)

    st.sidebar.caption("Développé pour mes usages personnels, pour la MP2I au Lycée Kléber.")
    full_sha, short_sha, modification_date = get_current_git_commit()
    if full_sha and short_sha and modification_date:
        st.sidebar.caption(f"[Version git {short_sha}, modifié {modification_date}]({REPOSITORY_URL}/commit/{full_sha})")

if __name__ == "__main__":
    main()