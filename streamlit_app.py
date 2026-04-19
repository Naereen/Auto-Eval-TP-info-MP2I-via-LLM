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
import statistics
from pathlib import Path

import altair as alt
import streamlit as st


ROOT_DIR = Path(__file__).resolve().parent
SUBJECTS_DIR = ROOT_DIR / "sujets-de-travaux-pratiques"
SUBMISSIONS_DIR = ROOT_DIR / "rendus-des-etudiants"
# Preferred filenames are checked first before falling back to broader glob searches.
CODE_CANDIDATES = ("code_rendu.c", "code_rendu.ml")
REPORT_PDF_CANDIDATES = ("compte-rendu.pdf", "compte_rendu.pdf")
REPORT_MD_CANDIDATES = ("compte-rendu.md", "compte_rendu.md")
BAREME_FILENAME = "bareme.json"
NOTES_FILENAME = "notes.json"
DEFAULT_QUESTION_COUNT = 10
DEFAULT_QUESTION_POINTS = 5
APP_MODES = (
    "1 - Barème",
    "2 - Évaluation des rendus",
    "3 - Vue de la classe par TP",
    "4 - Progression annuelle individuelle",
)


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
def discover_student_dirs(tp_name: str) -> list[Path]:
    """List submission directories available for the selected practical session."""
    return list_subdirectories(SUBMISSIONS_DIR / tp_name)


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


def build_default_bareme(tp_name: str, question_count: int) -> dict[str, object]:
    """Create an in-memory marking scheme with numbered questions and default scores."""
    questions = [
        {"index": index, "label": f"Question {index}", "points": DEFAULT_QUESTION_POINTS}
        for index in range(1, question_count + 1)
    ]
    return {
        "format_version": 1,
        "tp_name": tp_name,
        "question_count": question_count,
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
    normalized_questions: list[dict[str, object]] = []
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


def get_grading_points_widget_key(tp_name: str, student_name: str, question_index: int) -> str:
    """Return the widget key used by the grading editor for one student question."""
    return f"grading_points::{tp_name}::{student_name}::{question_index}"


def get_grading_session_key(tp_name: str, student_name: str) -> str:
    """Return the Streamlit session key used to store one student's grading data."""
    return f"grading::{tp_name}::{student_name}"


def build_default_grading_data(
    tp_name: str, student_name: str, bareme_questions: list[dict[str, object]]
) -> dict[str, object]:
    """Create default grading data for one student from the current marking scheme."""
    graded_questions = []
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

    normalized_questions = []
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
        st.session_state[session_key] = load_grading_data(tp_name, student_name, student_dir, bareme_questions)
        sync_grading_widgets(tp_name, student_name, st.session_state[session_key])
    else:
        st.session_state[session_key] = normalize_grading_data(
            tp_name,
            student_name,
            bareme_questions,
            st.session_state[session_key],
        )

    return st.session_state[session_key]


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


def get_question_index(question: dict[str, object]) -> int:
    """Extract a validated question index from a normalized question entry."""
    raw_index = question.get("index", 0)
    return raw_index if isinstance(raw_index, int) else 0


def get_question_label(question: dict[str, object]) -> str:
    """Extract a display label from a normalized question entry."""
    raw_label = question.get("label", "")
    return raw_label if isinstance(raw_label, str) else ""


def get_question_points(question: dict[str, object]) -> int:
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

    session_key = get_bareme_session_key(tp_name)
    st.session_state[session_key] = resized_bareme
    return resized_bareme


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
    normalized_bareme = normalize_bareme_data(tp_name, updated_bareme)
    st.session_state[get_bareme_session_key(tp_name)] = normalized_bareme
    for question in get_bareme_questions(normalized_bareme):
        question_index = get_question_index(question)
        st.session_state[get_bareme_points_widget_key(tp_name, question_index)] = get_question_points(question)
    return normalized_bareme


def render_pdf(path: Path, height: int = 720) -> None:
    """Embed a local PDF in the Streamlit page through a data URL."""
    encoded = base64.b64encode(read_binary_file(str(path))).decode("ascii")

    # On ajoute les paramètres après le base64, séparés par un '#'
    # pagemode=none : masque le menu latéral
    # view=FitH : ajuste à la largeur de l'iframe
    # toolbar=1 : garde la barre d'outils (0 pour masquer)
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


def render_subject_panel(tp_name: str) -> None:
    """Render the subject PDF and LaTeX metadata for the selected practical session."""
    subject_pdf = find_subject_pdf(tp_name)
    tex_files = find_subject_tex_files(tp_name)

    st.subheader("Sujet du TP")
    if subject_pdf is not None:
        render_pdf(subject_pdf, height=820)
        st.caption(f"PDF détecté : {subject_pdf.name}")
    else:
        st.warning("Aucun PDF de sujet n'a été trouvé pour ce TP.")

    if tex_files:
        tex_names = ", ".join(path.name for path in tex_files)
        st.caption(f"Sources LaTeX détectées : {tex_names}")


def render_bareme_mode(tp_name: str) -> None:
    """Render the marking scheme editor and persist it in the session state."""

    st.title(f"Rédaction du barème de notation - `{tp_name}`")
    st.caption("Mode de préparation du barème du TP sélectionné, avec sauvegarde locale et rechargement, par sujet (fichiers JSON).")

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

        if st.button("Appliquer un même barème à toutes les questions", use_container_width=True):
            st.session_state[uniform_points_state_key] = not st.session_state[uniform_points_state_key]

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
            if st.button("Valider la mise à jour globale", type="primary", use_container_width=True):
                st.session_state[uniform_points_state_key] = False
                update_all_question_points(tp_name, uniform_points)
                st.rerun()

        if requested_question_count != question_count:
            bareme_data = update_bareme_question_count(tp_name, requested_question_count)
            question_count = get_bareme_question_count(bareme_data)
            questions = get_bareme_questions(bareme_data)

        updated_questions: list[dict[str, object]] = []
        questions_container = st.container(height=550, border=True)
        with questions_container:
            st.caption("Édition du barème par question")
            for i, question in enumerate(questions):
                question_index = get_question_index(question)
                label = get_question_label(question)
                points = int(
                    st.number_input(
                        f"**{label}**",
                        min_value=0,
                        max_value=100,
                        value=get_question_points(question),
                        step=1,
                        key=get_bareme_points_widget_key(tp_name, question_index),
                    )
                )
                updated_questions.append({"index": question_index, "label": label, "points": points})

        bareme_data = {
            "format_version": 1,
            "tp_name": tp_name,
            "question_count": question_count,
            "total_points": sum(get_question_points(question) for question in updated_questions),
            "questions": updated_questions,
        }
        st.session_state[get_bareme_session_key(tp_name)] = bareme_data

        total_points = sum(get_question_points(question) for question in updated_questions)
        st.caption(f"Barème courant : {question_count} questions, {total_points} points au total.")

        if st.button("Sauvegarder le barème", type="primary"):
            save_bareme(tp_name, bareme_data)
            read_text_file.clear()
            st.success(f"Barème sauvegardé dans {get_bareme_path(tp_name).name}.")


def render_submissions_mode(tp_name: str) -> None:
    """Render the original submission review workflow for a practical session."""
    student_dirs = discover_student_dirs(tp_name)
    student_names = [path.name for path in student_dirs]
    bareme_data = get_bareme_data(tp_name)
    bareme_questions = get_bareme_questions(bareme_data)
    selected_student_name = st.sidebar.selectbox(
        "Choisir un rendu étudiant",
        student_names,
        index=0 if student_names else None,
        placeholder="Aucun rendu disponible",
    )

    selected_student_dir = None
    if selected_student_name:
        selected_student_dir = next((path for path in student_dirs if path.name == selected_student_name), None)

    grading_data = get_grading_data(tp_name, selected_student_name, selected_student_dir, bareme_questions)

    total_points, total_points_bareme, note_sur_20 = get_current_grading_summary(
        tp_name, selected_student_name, bareme_questions
    )

    st.title(f"Évaluation des rendus de TP - `{tp_name}`")
    st.caption(
        "Mode d'évaluation des rendus pour parcourir un sujet de TP, consulter les rendus et préparer l'évaluation automatique."
    )
    col_rendus, col_etudiant, col_total, col_note = st.columns(4)
    # col_tp.metric("Nom de ce TP", f"`{tp_name}`")
    col_rendus.metric("Nombre de rendus détectés", len(student_dirs))
    col_etudiant.metric("Étudiant sélectionné", f"**{selected_student_name}**" or "aucun")
    col_total.metric("Points obtenus", f"{total_points} / {total_points_bareme}")
    col_note.metric("Note", f"{note_sur_20}/20")

    subject_col, grading_col, student_col = st.columns((0.7, 0.3, 0.8), gap="small")

    with subject_col:
        render_subject_panel(tp_name)

    with grading_col:
        st.subheader("Évaluation")
        if selected_student_dir is None:
            st.info("Sélectionnez un rendu étudiant pour saisir l'évaluation question par question.")
        elif not bareme_questions:
            st.warning("Aucun barème n'est disponible pour ce TP. Commencez par renseigner le mode « 1 - Barème ».")
        else:
            updated_grades: list[int] = []
            updated_questions: list[dict[str, object]] = []
            with st.container(height=720):
                for question in bareme_questions:
                    question_index = get_question_index(question)
                    question_label = get_question_label(question)
                    max_points = get_question_points(question)
                    input_col_label, input_col_value = st.columns((2.2, 1), gap="small")
                    with input_col_label:
                        st.markdown(f"**{question_label}**")
                    with input_col_value:
                        widget_key = get_grading_points_widget_key(tp_name, selected_student_name, question_index)
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
                st.session_state[get_grading_session_key(tp_name, selected_student_name)] = grading_data

                if st.button("Sauvegarder la notation", type="primary", use_container_width=True):
                    save_grading_data(selected_student_dir, grading_data)
                    read_text_file.clear()
                    st.success(f"Notation sauvegardée dans {get_notes_path(selected_student_dir).name}.")

    with student_col:
        st.subheader("Rendu étudiant")
        if selected_student_dir is None:
            st.info("Aucun rendu étudiant disponible pour ce TP.")
        else:
            code_path = find_student_code(selected_student_dir)
            report_pdf = find_student_report_pdf(selected_student_dir)
            report_md = find_student_report_markdown(selected_student_dir)

            tabs = st.tabs(["Code source", "Compte-rendu PDF", "Compte-rendu brut", "Fichiers rendus"])

            with tabs[0]:
                if code_path is None:
                    st.warning("Aucun fichier source rendu n'a été trouvé.")
                else:
                    code = read_text_file(str(code_path))
                    st.code(code, language=detect_language(code_path), line_numbers=True, height=720)
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
            notes_chart = (
                alt.Chart(alt.Data(values=student_notes_rows))
                .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
                .encode(
                    x=alt.X("Étudiant:N", sort=None, title="Étudiant"),
                    y=alt.Y("Note /20:Q", scale=alt.Scale(domain=[0, 20]), title="Note /20"),
                    color=alt.Color(
                        "Note /20:Q",
                        scale=alt.Scale(domain=[0, 20], range=["#c62828", "#1565c0"]),
                        legend=alt.Legend(title="Note /20"),
                    ),
                    tooltip=[
                        alt.Tooltip("Étudiant:N", title="Étudiant"),
                        alt.Tooltip("Note /20:Q", title="Note", format=".2f"),
                    ],
                )
                .properties(height=320)
            )
            st.altair_chart(notes_chart, use_container_width=True)
            st.dataframe(student_notes_rows, use_container_width=True, hide_index=True)

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
        st.dataframe(per_question_rows, use_container_width=True, hide_index=True)

    with st.expander("Afficher le sujet du TP pour contextualiser la vue de classe"):
        render_subject_panel(tp_name)


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
        page_title="Auto-Eval TP MP2I @ Lycée Kléber (Lilian BESSON)",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    tp_names = discover_tp_names()
    if not tp_names:
        st.error("Aucun TP n'a été trouvé dans le dossier des sujets.")
        return

    st.sidebar.title("Auto-Eval TP MP2I")
    st.sidebar.subheader("Navigation")
    selected_mode = st.sidebar.selectbox("Choisir un mode", APP_MODES, index=0)
    selected_tp = st.sidebar.selectbox("Choisir un TP", tp_names)

    if selected_mode == "1 - Barème":
        render_bareme_mode(selected_tp)
    elif selected_mode == "2 - Évaluation des rendus":
        render_submissions_mode(selected_tp)
    elif selected_mode == "3 - Vue de la classe par TP":
        render_classroom_mode(selected_tp)
    else:
        render_placeholder_mode(selected_tp, selected_mode)

    st.divider()
    st.markdown(
        """
        ### Suite prévue
        Les prochaines étapes incluent l'amélioration du mode barème (calcul automatique par LLM/IA depuis la lecture automatique du sujet ?),
        puis l'analyse du code et du compte-rendu étudiant pour l'évaluer semi-automatiquement par LLM/IA,
        ainsi que l'ajout de vues des notes de la classe et de statistiques de progression individuelles au fil des TP, ou de la cohorte classe au fil de l'année.

        Des idées ? [Ouvrez un ticket !](https://github.com/Naereen/Auto-Eval-TP-info-MP2I-via-LLM/issues/new)
        """
    )

    st.divider()
    st.markdown(
        """
        ### À propos
        Dashboard développé par [Lilian BESSON](https://github.com/Naereen/) pour les TP de MP2I au Lycée Kléber. Le code source est disponible sur [GitHub](https://github.com/Naereen/Auto-Eval-TP-info-MP2I-via-LLM), sous [License MIT](https://lbesson.mit-license.org/).
        """
    )


if __name__ == "__main__":
    main()