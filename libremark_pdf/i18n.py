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
        "source_files_label": "Source files",
        "drop_hint": "Drop one or more .md files here",
        "browse_files": "Browse files",
        "files_heading": "Files",
        "file_count_one": "1 file",
        "file_count_many": "{count} files",
        "add_files": "Add files",
        "drop_or_browse": "Drop Markdown files here, or browse",
        "browse_without_dnd": "Select Markdown files",
        "drop_active": "Drop to add",
        "unsupported_drop": "Unsupported file type",
        "files_added_one": "1 file added.",
        "files_added_many": "{count} files added.",
        "files_add_summary": (
            "Added: {added}. Duplicates: {duplicates}. "
            "Unsupported: {unsupported}."
        ),
        "remove_file_a11y": "Remove {name}",
        "clear_files": "Clear list",
        "remove_file": "Remove",
        "themes_label": "Themes",
        "style_heading": "PDF style",
        "local_theme": "Local theme",
        "custom_css": "Custom CSS",
        "choose_css": "Choose CSS",
        "return_to_theme": "Use the selected theme",
        "custom_css_label": "Custom CSS",
        "use_theme": "Use selected theme",
        "css_style_label": "CSS style",
        "css_default_value": "style.css (default)",
        "css_from_theme_value": "CSS supplied by the selected theme",
        "change": "Change",
        "advanced_header_footer": "Header and footer (advanced)",
        "advanced_toggle": "Show or hide advanced options",
        "tokens_hint": "Tokens: {titre} {title} {date} {page} {total}",
        "tokens_help": "Tokens: {titre}, {title}, {date}, {page}, {total}",
        "header_label": "Header",
        "footer_label": "Footer",
        "position_left": "Left",
        "position_center": "Center",
        "position_right": "Right",
        "reset_header_footer": "Restore defaults",
        "render_date_label": "Date (YYYY-MM-DD)",
        "render_date": "Render date (YYYY-MM-DD)",
        "trusted_html_label": "Allow trusted static HTML",
        "trusted_html": "Allow trusted static HTML",
        "trusted_html_help": (
            "Use only for content you trust. Scripts, remote resources and "
            "active content remain blocked."
        ),
        "trusted_html_confirm_title": "Allow trusted HTML?",
        "trusted_html_confirm": (
            "This changes how raw HTML in the Markdown is interpreted. "
            "Continue only if you trust the file."
        ),
        "accordion_expanded": "▾ {title} — {summary} (expanded)",
        "accordion_collapsed": "▸ {title} — {summary} (collapsed)",
        "header_footer_heading": "Headers and footers",
        "other_advanced_heading": "Other advanced options",
        "settings_default": "Default",
        "settings_custom": "Custom",
        "other_date_summary": "Date: {date}",
        "other_trusted_summary": "Trusted HTML enabled",
        "left_placeholder": "Left",
        "center_placeholder": "Center",
        "right_placeholder": "Right",
        "refresh_preview": "Refresh preview",
        "preview_heading": "Preview",
        "refresh_preview_a11y": "Refresh preview",
        "preview_empty": "Add or select a file to preview it.",
        "preview_loading": "Updating preview…",
        "preview_unavailable": "Preview unavailable",
        "preview_retry": "Try again",
        "preview_conversion_possible": "You can still try to generate the PDF.",
        "copy_details": "Copy details",
        "zoom_out_a11y": "Zoom out",
        "zoom_in_a11y": "Zoom in",
        "zoom_value": "{percent}%",
        "keyboard_shortcuts_action": "Keyboard shortcuts",
        "keyboard_shortcuts_body": (
            "Add files: Ctrl+O\nRefresh preview: Ctrl+R\n"
            "Generate: Ctrl+G\nZoom in/out: Ctrl++ / Ctrl+-\n"
            "Reset zoom: Ctrl+0\nCancel active batch: Esc"
        ),
        "output_label": "Output",
        "destination_heading": "Destination",
        "output_default_value": "Next to each source file",
        "source_destination_one": "Next to the source file",
        "source_destination_many": "Next to each source file",
        "change_destination": "Change",
        "reset_destination": "Use source folders",
        "generate_button": "⚙ Generate PDF ({count} file(s))",
        "cancel_button": "Cancel",
        "status_ready": "Ready.",
        "status_generating": "Generating…",
        "status_generating_progress": "Generating… {current} / {total}",
        "status_cancelling": "Cancelling after the current file…",
        "status_cancelled": "Conversion cancelled before it started.",
        "status_closing": "Finishing the active operation before closing…",
        "status_done": "Done: {count} PDF(s) created.",
        "status_done_summary": (
            "Done: {ok} succeeded, {failed} failed, {cancelled} cancelled."
        ),
        "status_done_with_errors": "{ok} succeeded, {failed} failed. See details below.",
        "status_rendering_preview": "Rendering preview…",
        "status_preview_error": "Could not render preview: {error}",
        "status_generation_error": "Could not complete conversion: {error}",
        "status_theme_error": "Could not load installed themes: {error}",
        "error_title": "Error",
        "error_no_files": "Add at least one .md file first.",
        "error_generation": "Conversion failed: {error}",
        "css_filter_name": "CSS files",
        "markdown_filter_name": "Markdown files",
        "choose_output_folder_title": "Choose an output folder",
        "choose_css_title": "Choose a CSS file",
        "choose_markdown_title": "Choose one or more Markdown files",
        "collision_title": "Output collision",
        "collision_continue": (
            "These inputs cannot be written to their planned outputs and will "
            "be reported as failures:\n\n{details}\n\nContinue with independent files?"
        ),
        "overwrite_title": "Existing output files",
        "overwrite_question": (
            "{count} output file(s) already exist. Replace them only after each "
            "new PDF renders successfully?\n\nYes: replace. No: keep and report "
            "those items as failures. Cancel: do not start."
        ),
        "open_pdf": "Open PDF",
        "open_folder": "Open folder",
        "open_error": "Could not open the selected path: {error}",
    },
    "fr": {
        "app_title": "LibreMark PDF",
        "source_files_label": "Fichiers sources",
        "drop_hint": "Déposez un ou plusieurs fichiers .md ici",
        "browse_files": "Parcourir les fichiers",
        "files_heading": "Fichiers",
        "file_count_one": "1 fichier",
        "file_count_many": "{count} fichiers",
        "add_files": "Ajouter des fichiers",
        "drop_or_browse": (
            "Déposez des fichiers Markdown ici, ou parcourez vos fichiers"
        ),
        "browse_without_dnd": "Sélectionner des fichiers Markdown",
        "drop_active": "Déposer pour ajouter",
        "unsupported_drop": "Type de fichier non pris en charge",
        "files_added_one": "1 fichier ajouté.",
        "files_added_many": "{count} fichiers ajoutés.",
        "files_add_summary": (
            "Ajoutés : {added}. Doublons : {duplicates}. "
            "Non pris en charge : {unsupported}."
        ),
        "remove_file_a11y": "Retirer {name}",
        "clear_files": "Vider la liste",
        "remove_file": "Retirer",
        "themes_label": "Thèmes",
        "style_heading": "Style PDF",
        "local_theme": "Thème local",
        "custom_css": "CSS personnalisé",
        "choose_css": "Choisir un CSS",
        "return_to_theme": "Revenir au thème sélectionné",
        "custom_css_label": "CSS personnalisé",
        "use_theme": "Utiliser le thème sélectionné",
        "css_style_label": "Style CSS",
        "css_default_value": "style.css (par défaut)",
        "css_from_theme_value": "CSS fourni par le thème sélectionné",
        "change": "Changer",
        "advanced_header_footer": "En-tête et pied de page (avancé)",
        "advanced_toggle": "Afficher ou masquer les options avancées",
        "tokens_hint": "Jetons : {titre} {title} {date} {page} {total}",
        "tokens_help": "Jetons : {titre}, {title}, {date}, {page}, {total}",
        "header_label": "En-tête",
        "footer_label": "Pied de page",
        "position_left": "Gauche",
        "position_center": "Centre",
        "position_right": "Droite",
        "reset_header_footer": "Rétablir les valeurs par défaut",
        "render_date_label": "Date (AAAA-MM-JJ)",
        "render_date": "Date de rendu (AAAA-MM-JJ)",
        "trusted_html_label": "Autoriser le HTML statique de confiance",
        "trusted_html": "Autoriser le HTML statique de confiance",
        "trusted_html_help": (
            "À utiliser uniquement avec un contenu de confiance. Les scripts, "
            "ressources distantes et contenus actifs restent bloqués."
        ),
        "trusted_html_confirm_title": "Autoriser le HTML de confiance ?",
        "trusted_html_confirm": (
            "Cette option modifie l’interprétation du HTML brut dans le "
            "Markdown. Continuez uniquement si le fichier est fiable."
        ),
        "accordion_expanded": "▾ {title} — {summary} (ouvert)",
        "accordion_collapsed": "▸ {title} — {summary} (fermé)",
        "header_footer_heading": "En-têtes et pieds de page",
        "other_advanced_heading": "Autres options avancées",
        "settings_default": "Par défaut",
        "settings_custom": "Personnalisé",
        "other_date_summary": "Date : {date}",
        "other_trusted_summary": "HTML de confiance activé",
        "left_placeholder": "Gauche",
        "center_placeholder": "Centre",
        "right_placeholder": "Droite",
        "refresh_preview": "Actualiser l'aperçu",
        "preview_heading": "Aperçu",
        "refresh_preview_a11y": "Actualiser l’aperçu",
        "preview_empty": "Ajoutez ou sélectionnez un fichier pour le prévisualiser.",
        "preview_loading": "Mise à jour de l’aperçu…",
        "preview_unavailable": "Aperçu indisponible",
        "preview_retry": "Réessayer",
        "preview_conversion_possible": (
            "Vous pouvez tout de même essayer de générer le PDF."
        ),
        "copy_details": "Copier les détails",
        "zoom_out_a11y": "Réduire le zoom",
        "zoom_in_a11y": "Augmenter le zoom",
        "zoom_value": "{percent} %",
        "keyboard_shortcuts_action": "Raccourcis clavier",
        "keyboard_shortcuts_body": (
            "Ajouter des fichiers : Ctrl+O\nActualiser l’aperçu : Ctrl+R\n"
            "Générer : Ctrl+G\nZoom avant/arrière : Ctrl++ / Ctrl+-\n"
            "Réinitialiser le zoom : Ctrl+0\nAnnuler le lot actif : Échap"
        ),
        "output_label": "Sortie",
        "destination_heading": "Destination",
        "output_default_value": "À côté de chaque fichier source",
        "source_destination_one": "À côté du fichier source",
        "source_destination_many": "À côté de chaque fichier source",
        "change_destination": "Changer",
        "reset_destination": "Utiliser les dossiers sources",
        "generate_button": "⚙ Générer le PDF ({count} fichier(s))",
        "cancel_button": "Annuler",
        "status_ready": "Prêt.",
        "status_generating": "Génération en cours…",
        "status_generating_progress": "Génération en cours… {current} / {total}",
        "status_cancelling": "Annulation après le fichier en cours…",
        "status_cancelled": "Conversion annulée avant son démarrage.",
        "status_closing": "Fin de l’opération en cours avant la fermeture…",
        "status_done": "Terminé : {count} PDF généré(s).",
        "status_done_summary": (
            "Terminé : {ok} réussi(s), {failed} échoué(s), "
            "{cancelled} annulé(s)."
        ),
        "status_done_with_errors": (
            "{ok} réussi(s), {failed} échoué(s). Voir le détail ci-dessous."
        ),
        "status_rendering_preview": "Génération de l'aperçu…",
        "status_preview_error": "Impossible de générer l'aperçu : {error}",
        "status_generation_error": "Impossible de terminer la conversion : {error}",
        "status_theme_error": "Impossible de charger les thèmes installés : {error}",
        "error_title": "Erreur",
        "error_no_files": "Ajoutez d’abord au moins un fichier .md.",
        "error_generation": "Échec de la conversion : {error}",
        "css_filter_name": "Fichiers CSS",
        "markdown_filter_name": "Fichiers Markdown",
        "choose_output_folder_title": "Choisir un dossier de sortie",
        "choose_css_title": "Choisir un fichier CSS",
        "choose_markdown_title": "Choisir un ou plusieurs fichiers Markdown",
        "collision_title": "Collision de sortie",
        "collision_continue": (
            "Ces entrées ne peuvent pas être écrites vers les sorties prévues "
            "et seront signalées comme des échecs :\n\n{details}\n\nPoursuivre "
            "avec les fichiers indépendants ?"
        ),
        "overwrite_title": "Fichiers de sortie existants",
        "overwrite_question": (
            "{count} fichier(s) de sortie existent déjà. Les remplacer uniquement "
            "après le rendu réussi de chaque nouveau PDF ?\n\nOui : remplacer. "
            "Non : conserver et signaler ces éléments comme des échecs. "
            "Annuler : ne pas démarrer."
        ),
        "open_pdf": "Ouvrir le PDF",
        "open_folder": "Ouvrir le dossier",
        "open_error": "Impossible d’ouvrir le chemin sélectionné : {error}",
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
