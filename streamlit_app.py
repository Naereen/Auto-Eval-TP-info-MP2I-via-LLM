"""Streamlit dashboard used to inspect TP subjects and student submissions.

The app discovers available practical sessions from the repository layout,
renders subject PDFs, previews submitted source files, and displays the
associated report when available.
"""

from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components


ROOT_DIR = Path(__file__).resolve().parent
SUBJECTS_DIR = ROOT_DIR / "sujets-de-travaux-pratiques"
SUBMISSIONS_DIR = ROOT_DIR / "rendus-des-etudiants"
# Preferred filenames are checked first before falling back to broader glob searches.
CODE_CANDIDATES = ("code_rendu.c", "code_rendu.ml")
REPORT_PDF_CANDIDATES = ("compte-rendu.pdf", "compte_rendu.pdf")
REPORT_MD_CANDIDATES = ("compte-rendu.md", "compte_rendu.md")


def list_subdirectories(directory: Path) -> list[Path]:
    """Return subdirectories sorted by name, or an empty list if the parent is missing."""
    if not directory.exists():
        return []
    return sorted((path for path in directory.iterdir() if path.is_dir()), key=lambda path: path.name.lower())


@st.cache_data(show_spinner=True)
def discover_tp_names() -> list[str]:
    """List available practical sessions from the subjects directory."""
    return [path.name for path in list_subdirectories(SUBJECTS_DIR)]


@st.cache_data(show_spinner=True)
def find_subject_pdf(tp_name: str) -> Path | None:
    """Find the main PDF for a given practical session."""
    tp_dir = SUBJECTS_DIR / tp_name
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
    tp_dir = SUBJECTS_DIR / tp_name
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


def render_pdf(path: Path, height: int = 780) -> None:
    """Embed a local PDF in the Streamlit page through a data URL."""
    encoded = base64.b64encode(read_binary_file(str(path))).decode("ascii")
    iframe = f"""
    <iframe
        src="data:application/pdf;base64,{encoded}"
        width="100%"
        height="{height}"
        style="border: 1px solid rgba(148, 163, 184, 0.35); border-radius: 14px; background: white;"
    ></iframe>
    """
    components.html(iframe, height=height + 20)


def detect_language(path: Path) -> str:
    """Map supported source file extensions to Streamlit syntax highlighters."""
    if path.suffix == ".c":
        return "c"
    if path.suffix == ".ml":
        return "ocaml"
    return "text"


def render_header(tp_name: str, student_name: str | None, student_count: int) -> None:
    """Render the page title and the key metrics for the current selection."""
    st.title("Dashboard d'évaluation des rendus de TP d'informatique en MP2I @ Lycée Kléber (Lilian BESSON)")
    st.caption(
        "Premier jet Streamlit pour parcourir un sujet de TP, consulter les rendus et préparer l'évaluation automatique."
    )
    col_tp, col_rendus, col_etudiant = st.columns(3)
    col_tp.metric("TP", tp_name)
    col_rendus.metric("Rendus détectés", student_count)
    col_etudiant.metric("Étudiant sélectionné", student_name or "aucun")


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

    st.sidebar.title("Navigation")
    selected_tp = st.sidebar.selectbox("Choisir un TP", tp_names)

    student_dirs = discover_student_dirs(selected_tp)
    student_names = [path.name for path in student_dirs]
    selected_student_name = st.sidebar.selectbox(
        "Choisir un rendu étudiant",
        student_names,
        index=0 if student_names else None,
        placeholder="Aucun rendu disponible",
    )

    selected_student_dir = None
    if selected_student_name:
        selected_student_dir = next((path for path in student_dirs if path.name == selected_student_name), None)

    render_header(selected_tp, selected_student_name, len(student_dirs))

    subject_pdf = find_subject_pdf(selected_tp)
    tex_files = find_subject_tex_files(selected_tp)

    subject_col, student_col = st.columns((1.1, 1), gap="large")

    with subject_col:
        st.subheader("Sujet du TP")
        if subject_pdf is not None:
            render_pdf(subject_pdf, height=820)
            st.caption(f"PDF détecté : {subject_pdf.name}")
        else:
            st.warning("Aucun PDF de sujet n'a été trouvé pour ce TP.")

        if tex_files:
            tex_names = ", ".join(path.name for path in tex_files)
            st.caption(f"Sources LaTeX détectées : {tex_names}")

    with student_col:
        st.subheader("Rendu étudiant")
        if selected_student_dir is None:
            st.info("Aucun rendu étudiant disponible pour ce TP.")
            return

        code_path = find_student_code(selected_student_dir)
        report_pdf = find_student_report_pdf(selected_student_dir)
        report_md = find_student_report_markdown(selected_student_dir)

        tabs = st.tabs(["Code source", "Compte-rendu", "Fichiers"])

        with tabs[0]:
            if code_path is None:
                st.warning("Aucun fichier source rendu n'a été trouvé.")
            else:
                code = read_text_file(str(code_path))
                st.code(code, language=detect_language(code_path), line_numbers=True)
                st.caption(f"Fichier affiché : {code_path.name}")

        with tabs[1]:
            if report_pdf is not None:
                render_pdf(report_pdf, height=720)
                st.caption(f"Compte-rendu PDF affiché : {report_pdf.name}")
            elif report_md is not None:
                st.info("Aucun PDF trouvé. Affichage du compte-rendu Markdown en secours.")
                st.markdown(read_text_file(str(report_md)))
                st.caption(f"Fichier affiché : {report_md.name}")
            else:
                st.warning("Aucun compte-rendu PDF ou Markdown n'a été trouvé.")

        with tabs[2]:
            for path in sorted(selected_student_dir.iterdir(), key=lambda item: item.name.lower()):
                label = "Dossier" if path.is_dir() else "Fichier"
                st.write(f"- {label}: {path.name}")

    st.divider()
    st.markdown(
        """
        ### Suite prévue
        L'étape suivante sera d'ajouter la lecture automatique du sujet, des fichiers de correction,
        puis l'analyse du code et du compte-rendu étudiant afin de produire une pré-évaluation assistée.
        """
    )


if __name__ == "__main__":
    main()