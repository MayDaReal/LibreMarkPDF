"""Desktop translations and best-effort language persistence."""

from __future__ import annotations

import json
import locale
from pathlib import Path

LANGUAGES = ["en", "fr"]
DEFAULT_LANGUAGE = "en"

CONFIG_DIR = Path.home() / ".libremark-pdf"
CONFIG_FILE = CONFIG_DIR / "config.json"


STRINGS = {
    "en": {
        "app_title": "LibreMark PDF",
        "drop_hint": "Drop one or more .md files here",
        "browse_files": "Browse files",
        "remove_file": "Remove",
        "css_style_label": "CSS style",
        "css_default_value": "style.css (default)",
        "change": "Change",
        "advanced_header_footer": "Header and footer (advanced)",
        "tokens_hint": "Tokens: {titre} {date} {page} {total}",
        "header_label": "Header",
        "footer_label": "Footer",
        "left_placeholder": "Left",
        "center_placeholder": "Center",
        "right_placeholder": "Right",
        "preview_label": "Preview",
        "refresh_preview": "Refresh preview",
        "output_label": "Output",
        "output_default_value": "Next to each source file",
        "choose_folder": "Choose folder",
        "generate_button": "Generate PDF ({count} file(s))",
        "status_ready": "Ready.",
        "status_generating": "Generating…",
        "status_done": "Done: {count} PDF(s) created.",
        "status_done_with_errors": "{ok} succeeded, {failed} failed. See details below.",
        "status_rendering_preview": "Rendering preview…",
        "status_preview_error": "Could not render preview: {error}",
        "error_title": "Error",
        "error_no_files": "Add at least one .md file first.",
        "error_generation": "Conversion failed: {error}",
        "css_filter_name": "CSS files",
        "markdown_filter_name": "Markdown files",
        "choose_output_folder_title": "Choose an output folder",
        "choose_css_title": "Choose a CSS file",
        "choose_markdown_title": "Choose one or more Markdown files",
        "sample_preview_title": "Document title",
        "sample_preview_body": (
            "This is a live preview of your current style, header and "
            "footer. Load a file to preview its actual content."
        ),
    },
    "fr": {
        "app_title": "LibreMark PDF",
        "drop_hint": "Glisse un ou plusieurs fichiers .md ici",
        "browse_files": "Parcourir les fichiers",
        "remove_file": "Retirer",
        "css_style_label": "Style CSS",
        "css_default_value": "style.css (par défaut)",
        "change": "Changer",
        "advanced_header_footer": "En-tête et pied de page (avancé)",
        "tokens_hint": "Jetons : {titre} {date} {page} {total}",
        "header_label": "En-tête",
        "footer_label": "Pied de page",
        "left_placeholder": "Gauche",
        "center_placeholder": "Centre",
        "right_placeholder": "Droite",
        "preview_label": "Aperçu",
        "refresh_preview": "Actualiser l'aperçu",
        "output_label": "Sortie",
        "output_default_value": "À côté de chaque fichier source",
        "choose_folder": "Choisir un dossier",
        "generate_button": "Générer le PDF ({count} fichier(s))",
        "status_ready": "Prêt.",
        "status_generating": "Génération en cours…",
        "status_done": "Terminé : {count} PDF généré(s).",
        "status_done_with_errors": (
            "{ok} réussi(s), {failed} échoué(s). Voir le détail ci-dessous."
        ),
        "status_rendering_preview": "Génération de l'aperçu…",
        "status_preview_error": "Impossible de générer l'aperçu : {error}",
        "error_title": "Erreur",
        "error_no_files": "Ajoute d'abord au moins un fichier .md.",
        "error_generation": "Échec de la conversion : {error}",
        "css_filter_name": "Fichiers CSS",
        "markdown_filter_name": "Fichiers Markdown",
        "choose_output_folder_title": "Choisir un dossier de sortie",
        "choose_css_title": "Choisir un fichier CSS",
        "choose_markdown_title": "Choisir un ou plusieurs fichiers Markdown",
        "sample_preview_title": "Titre du document",
        "sample_preview_body": (
            "Ceci est un aperçu en direct de ton style, en-tête et pied de "
            "page actuels. Charge un fichier pour prévisualiser son contenu réel."
        ),
    },
}


def detect_system_language() -> str:
    """Best-effort detection of the OS language, defaulting to English."""
    try:
        lang_code, _ = locale.getlocale()
        if not lang_code:
            lang_code = locale.getdefaultlocale()[0]
    except Exception:
        # Locale APIs vary across supported operating systems.
        lang_code = None

    if lang_code and lang_code.lower().startswith("fr"):
        return "fr"
    return DEFAULT_LANGUAGE


def load_language() -> str:
    """Load the persisted language choice, or detect it on first run."""
    try:
        if CONFIG_FILE.exists():
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            lang = data.get("lang")
            if lang in LANGUAGES:
                return lang
    except Exception:
        # A malformed or unreadable preference must not block startup.
        pass
    return detect_system_language()


def save_language(lang: str) -> None:
    """Persist a supported language without making conversion depend on it."""
    if lang not in LANGUAGES:
        return
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(json.dumps({"lang": lang}), encoding="utf-8")
    except Exception:
        # Read-only profiles are valid runtime environments.
        pass


def t(key: str, lang: str, **kwargs) -> str:
    """Translate a key with English and key-name fallbacks."""
    table = STRINGS.get(lang, STRINGS[DEFAULT_LANGUAGE])
    text = table.get(key) or STRINGS[DEFAULT_LANGUAGE].get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError):
            return text
    return text
