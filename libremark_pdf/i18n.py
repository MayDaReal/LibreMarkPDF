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
        "app_version_compact": "v{version}",
        "gallery_title": "Modern UI component gallery",
        "gallery_foundations": "Visual foundations",
        "gallery_components_tab": "Components",
        "gallery_icons_tab": "Icons",
        "gallery_buttons": "Buttons and states",
        "gallery_primary": "Primary action",
        "gallery_secondary": "Secondary action",
        "gallery_disabled": "Disabled",
        "gallery_hover": "Hover",
        "gallery_pressed": "Pressed",
        "gallery_icon_action": "Refresh preview",
        "gallery_badges": "Status badges",
        "gallery_neutral": "Pending",
        "gallery_success": "Succeeded",
        "gallery_warning": "Attention",
        "gallery_error": "Failed",
        "gallery_info": "Information",
        "gallery_typography": "Typography and cards",
        "gallery_body": "Clear body text on a calm office-style surface.",
        "gallery_secondary_text": "Secondary information remains readable.",
        "gallery_focus_hint": (
            "Use Tab to inspect focus. Hover icon buttons for localized help."
        ),
        "gallery_icon_variants": "Neutral · accent · success · error",
        "help_menu": "Help",
        "language_menu": "Language",
        "language_english_name": "English",
        "language_french_name": "French",
        "compact_menu_a11y": "Application menu",
        "window_minimize_a11y": "Minimize window",
        "window_maximize_a11y": "Maximize window",
        "window_restore_a11y": "Restore window",
        "window_close_a11y": "Close window",
        "manual_action": "User manual",
        "manual_open_error": "Could not open the user manual: {error}",
        "notices_open_error": (
            "Could not open the third-party notices: {error}"
        ),
        "about_action": "About LibreMark PDF",
        "about_version": "LibreMark PDF {version}",
        "about_local_conversion": "Local Markdown-to-PDF conversion",
        "about_no_network": "No data is sent over the network",
        "third_party_notices_action": "Third-party notices",
        "technical_information": "Technical information",
        "copy_technical_information": "Copy technical information",
        "technical_information_copied": "Technical information copied.",
        "close_action": "Close",
        "technical_app_version": "LibreMark PDF",
        "technical_render_profile": "Render profile",
        "technical_playwright": "Playwright",
        "technical_chromium": "Chromium",
        "technical_chromium_revision": "Chromium revision",
        "technical_python": "Python",
        "technical_system": "System",
        "technical_architecture": "Architecture",
        "technical_execution_mode": "Execution mode",
        "execution_mode_source": "Source",
        "execution_mode_artifact": "Artifact",
        "report_issue_action": "Report a problem",
        "report_title": "Report a problem",
        "report_intro": (
            "Describe the problem, then review the complete local report. "
            "Nothing is sent automatically."
        ),
        "report_document_title": "LibreMark PDF problem report",
        "report_summary": "What happened?",
        "report_summary_placeholder": "Briefly describe the problem…",
        "report_summary_required": "Describe what happened before reviewing the report.",
        "report_steps": "Steps to reproduce (optional)",
        "report_expected": "Expected result (optional)",
        "report_error_code": "Error code",
        "report_error_context": "Error context",
        "include_diagnostics": "Include anonymized technical diagnostics",
        "diagnostics_consent": (
            "Nothing is sent automatically. Review the report before copying "
            "or saving it."
        ),
        "report_local_help": (
            "Copy or save this report, review it for private information, then "
            "share it through an official support channel. Do not include "
            "confidential Markdown, PDF, CSS or personal data."
        ),
        "preview_report": "Review report",
        "report_preview": "Editable report",
        "report_preview_help": (
            "Review and edit this complete report before copying or saving it."
        ),
        "report_preview_expand": "Show editable report",
        "report_preview_collapse": "Hide editable report",
        "report_preview_edited": (
            "Your report edits are preserved. Select Review report to rebuild it."
        ),
        "report_diagnostics_heading": "Anonymized technical diagnostics (JSON)",
        "copy_report": "Copy report",
        "save_report": "Save report…",
        "open_support_channel": "Open support page",
        "support_not_configured": (
            "No support page is configured. Copy or save the report instead."
        ),
        "report_copied": "Report copied.",
        "report_saved": "Report saved.",
        "report_copy_error": "Could not copy the report: {error}",
        "report_save_error": "Could not save the report: {error}",
        "support_open_error": "Could not open the support page: {error}",
        "report_text_filter": "Text reports",
        "report_save_title": "Save the problem report",
        "source_files_label": "Source files",
        "drop_hint": "Drop one or more .md files here",
        "browse_files": "Browse files",
        "files_heading": "Files",
        "compact_tab_files": "Files",
        "compact_tab_preview": "Preview",
        "compact_tab_settings": "Settings",
        "compact_tab_results": "Results",
        "file_count_one": "1 file",
        "file_count_many": "{count} files",
        "add_files": "Add files",
        "drop_or_browse": "Drop Markdown files here, or browse",
        "browse_without_dnd": "Select Markdown files",
        "drop_active": "Drop to add",
        "unsupported_drop": "Unsupported file type",
        "files_added_one": "1 file added.",
        "files_added_many": "{count} files added.",
        "files_add_summary": "{summary}",
        "file_feedback_added_one": "1 file added",
        "file_feedback_added_many": "{count} files added",
        "file_feedback_duplicate_one": "1 duplicate",
        "file_feedback_duplicate_many": "{count} duplicates",
        "file_feedback_unsupported_one": "1 unsupported type",
        "file_feedback_unsupported_many": "{count} unsupported types",
        "files_ignored_one": "1 item ignored: {reason}",
        "files_ignored_many": "{count} items ignored: {reason}",
        "duplicate_reason": "already in the list",
        "unsupported_reason": "only .md and .markdown files are supported",
        "remove_file_a11y": "Remove {name}",
        "clear_files": "Clear list",
        "remove_file": "Remove",
        "active_preview_badge": "Active preview",
        "reveal_source": "Show in source folder",
        "copy_path": "Copy path",
        "remove_from_batch": "Remove from list",
        "all_remove_action": "Remove all",
        "file_mutation_disabled": (
            "File list changes are unavailable during conversion."
        ),
        "conversion_pending": "Pending",
        "conversion_running": "In progress",
        "conversion_ok": "Succeeded",
        "conversion_error": "Failed",
        "conversion_kept": "Kept",
        "conversion_cancelled": "Cancelled",
        "themes_label": "Themes",
        "style_heading": "PDF style",
        "settings_heading": "Settings",
        "cancel_settings": "Cancel",
        "save_settings": "Save",
        "back_settings": "Back",
        "style_editor_title": "PDF style",
        "style_editor_description": (
            "Choose one local theme or a custom CSS file for this session."
        ),
        "style_theme_technical": "Theme identifier: {reference}",
        "css_empty_state": "No CSS file selected",
        "css_validation_required": "Choose a CSS file to use Custom CSS.",
        "css_validation_invalid": (
            "This CSS cannot be used. Choose another local CSS file."
        ),
        "destination_editor_title": "Destination",
        "destination_editor_description": (
            "Choose where generated PDFs are saved. This does not change the preview."
        ),
        "destination_source_option": "Same folder as each source file",
        "destination_custom_option": "Single folder",
        "destination_choose_folder": "Browse",
        "destination_no_folder_selected": "No folder selected",
        "destination_validation_required": (
            "Choose a folder to use a single destination."
        ),
        "header_footer_editor_title": "Headers and footers",
        "header_footer_editor_description": (
            "Add optional text to six positions. An empty field displays nothing."
        ),
        "header_footer_tokens_label": "Insert a variable",
        "header_footer_token_help": (
            "{titre} or {title}: document title · {date}: render date · "
            "{page}: current page · {total}: total pages"
        ),
        "restore_header_footer_title": "Restore header and footer defaults?",
        "restore_header_footer_question": (
            "Customized header or footer values will be replaced. "
            "Other PDF settings will not change."
        ),
        "advanced_options_heading": "Advanced options",
        "advanced_editor_title": "Advanced options",
        "advanced_editor_description": (
            "Choose the render date and whether trusted static HTML is allowed."
        ),
        "settings_default_theme": "Default theme",
        "settings_css_summary": "Custom CSS · {path}",
        "settings_none": "None",
        "header_left_summary": "Left header: {value}",
        "header_center_summary": "Center header: {value}",
        "header_right_summary": "Right header: {value}",
        "footer_left_summary": "Left footer: {value}",
        "footer_center_summary": "Center footer: {value}",
        "footer_right_summary": "Right footer: {value}",
        "other_automatic_summary": "Automatic date · Safe HTML",
        "other_date_trusted_summary": "Date: {date} · Trusted HTML enabled",
        "local_theme": "Local theme",
        "custom_css": "Custom CSS",
        "choose_css": "Choose CSS",
        "use_theme": "Use selected theme",
        "css_style_label": "CSS style",
        "css_default_value": "style.css (default)",
        "change": "Change",
        "advanced_header_footer": "Header and footer (advanced)",
        "tokens_hint": "Tokens: {titre} {title} {date} {page} {total}",
        "header_label": "Header",
        "footer_label": "Footer",
        "position_left": "Left",
        "position_center": "Center",
        "position_right": "Right",
        "reset_header_footer": "Restore defaults",
        "render_date": "Render date (YYYY-MM-DD)",
        "render_date_automatic_help": (
            "Leave this field empty to use the current date automatically."
        ),
        "render_date_validation_invalid": (
            "Enter a valid date in YYYY-MM-DD format, or leave the field empty."
        ),
        "trusted_html": "Allow trusted static HTML",
        "trusted_html_help": (
            "Use only for content you trust. Scripts, remote resources and "
            "active content remain blocked."
        ),
        "trusted_html_confirm_title": "Allow trusted HTML?",
        "trusted_html_allow": "Allow",
        "trusted_html_confirm": (
            "This changes how raw HTML in the Markdown is interpreted. "
            "Continue only if you trust the file."
        ),
        "header_footer_heading": "Headers and footers",
        "settings_default": "Default",
        "settings_custom": "Custom",
        "other_date_summary": "Date: {date}",
        "other_trusted_summary": "Trusted HTML enabled",
        "left_placeholder": "Left",
        "center_placeholder": "Center",
        "right_placeholder": "Right",
        "refresh_preview": "Reset preview and fit page",
        "preview_heading": "Preview",
        "refresh_preview_a11y": "Reset preview and fit page",
        "preview_empty": "Add or select a file to preview it.",
        "preview_loading": "Updating preview…",
        "preview_scheduled": "Preview update scheduled…",
        "preview_rendering": "Updating preview…",
        "preview_error_title": "Could not generate preview",
        "preview_unavailable": "Preview unavailable",
        "preview_retry": "Try again",
        "preview_conversion_possible": "You can still try to generate the PDF.",
        "copy_details": "Copy details",
        "preview_page": "Page {current} of {total}",
        "previous_page_a11y": "Previous page",
        "next_page_a11y": "Next page",
        "zoom_out_a11y": "Zoom out",
        "zoom_in_a11y": "Zoom in",
        "zoom_value": "{percent}%",
        "fit_page": "Fit page",
        "fit_width": "Fit width",
        "preview_more_a11y": "More preview actions",
        "preview_canvas_a11y": "Document preview",
        "keyboard_shortcuts_action": "Keyboard shortcuts",
        "language_english_a11y": "Change language to English",
        "language_french_a11y": "Change language to French",
        "shortcut_add_files": "Add files",
        "shortcut_refresh_preview": "Refresh preview",
        "shortcut_generate": "Generate",
        "shortcut_zoom_in": "Zoom in",
        "shortcut_zoom_out": "Zoom out",
        "shortcut_reset_zoom": "Reset zoom",
        "shortcut_previous_page": "Previous page",
        "shortcut_next_page": "Next page",
        "shortcut_cancel_batch": "Cancel active batch",
        "output_label": "Output",
        "destination_heading": "Destination",
        "source_destination_one": "Next to the source file",
        "source_destination_many": "Next to each source file",
        "generate_one": "Generate PDF",
        "generate_many": "Generate {count} PDFs",
        "action_blocked_no_files": "Add at least one Markdown file to generate a PDF.",
        "action_blocked_validating": "Generation is unavailable while outputs are checked.",
        "action_progress_completed": "{current} of {total} completed · {percent}%",
        "action_active_stage": "File {current} of {total} · {name} — {stage}",
        "action_running_one": "1 file in progress · Destination: {destination}",
        "action_running_many": "{count} files in progress · Destination: {destination}",
        "applied_options": "Applied options ⓘ",
        "conversion_stage_preparing": "Preparing document…",
        "conversion_stage_rendering": "Rendering with Chromium…",
        "conversion_stage_finalizing": "Finalizing PDF…",
        "conversion_stage_publishing": "Publishing safely…",
        "stop_after_current": "Stop after this file",
        "cancel_now": "Cancel now",
        "status_cancelling_now": "Cancelling at the next safe point — this may take a few seconds.",
        "cancel_button": "Cancel after this file",
        "cancel_button_short": "Cancel",
        "status_ready": "Ready.",
        "action_ready_one": "1 file ready · Destination: {destination}",
        "action_ready_many": (
            "{count} files ready · Destination: {destination}"
        ),
        "status_generating": "Generating…",
        "status_validating": "… Validating outputs…",
        "status_generating_progress": "{current} of {total}",
        "status_generating_file": "→ Converting {current} of {total} — {name}",
        "status_cancelling": "Cancelling after the current file…",
        "status_cancelling_file": "! Stop requested — {name} may finish.",
        "status_cancelled": "Conversion cancelled before it started.",
        "status_closing": "Finishing the active operation before closing…",
        "status_done_summary": "{summary}",
        "summary_succeeded_one": "{count} succeeded",
        "summary_succeeded_many": "{count} succeeded",
        "summary_failed_one": "{count} failed",
        "summary_failed_many": "{count} failed",
        "summary_kept_one": "{count} kept",
        "summary_kept_many": "{count} kept",
        "summary_cancelled_one": "{count} cancelled",
        "summary_cancelled_many": "{count} cancelled",
        "status_rendering_preview": "Rendering preview…",
        "status_preview_error": "Could not render preview: {error}",
        "status_generation_error": "Could not complete conversion: {error}",
        "status_details_copied": "Error details copied.",
        "status_theme_error": "Could not load installed themes: {error}",
        "error_title": "Error",
        "error_no_files": "Add at least one .md file first.",
        "error_generation": "Conversion failed: {error}",
        "css_filter_name": "CSS files",
        "markdown_filter_name": "Markdown files",
        "choose_output_folder_title": "Choose an output folder",
        "choose_css_title": "Choose a CSS file",
        "choose_markdown_title": "Choose one or more Markdown files",
        "collision_title": "Output conflicts",
        "collision_continue": (
            "These inputs cannot be written to their planned outputs and will "
            "be reported as failures:\n\n{details}\n\nContinue with independent files?"
        ),
        "continue_with_others": "Continue with other files",
        "overwrite_title": "Existing PDFs",
        "decision_required_title": "Decision required",
        "decision_conflict_one": "{count} conflict",
        "decision_conflict_many": "{count} conflicts",
        "decision_existing_one": "{count} existing PDF",
        "decision_existing_many": "{count} existing PDFs",
        "decision_replace_instruction": (
            "Check the PDFs to replace. Unchecked PDFs will be kept."
        ),
        "decision_blocked_instruction": (
            "Blocked files cannot be generated and will be reported."
        ),
        "decision_source_heading": "Source",
        "decision_destination_heading": "Destination",
        "decision_issue_heading": "Issue",
        "decision_replace_heading": "Replace?",
        "decision_blocked": "Blocked",
        "decision_replace_help": (
            "Checked: replace only after successful conversion. "
            "Unchecked: keep the existing PDF."
        ),
        "decision_blocked_help": (
            "This destination is blocked and cannot be selected for replacement."
        ),
        "decision_replaced_one": "{count} will be replaced",
        "decision_replaced_many": "{count} will be replaced",
        "decision_kept_one": "{count} kept",
        "decision_kept_many": "{count} kept",
        "decision_issue_duplicate": "Same destination",
        "decision_issue_same_path": "Source = destination",
        "decision_issue_missing_input": "Source unavailable",
        "decision_issue_existing": "PDF already exists",
        "decision_issue_other": "Output unavailable",
        "continue_generation": "Continue",
        "back_action": "Back",
        "overwrite_question_one": (
            "1 output PDF already exists. Choose whether to replace it only "
            "after successful rendering, or keep it and report a failure."
        ),
        "overwrite_question_many": (
            "{count} output PDFs already exist. Choose whether to replace each "
            "one only after successful rendering, or keep them and report failures."
        ),
        "close_conversion_title": "Conversion in progress",
        "close_conversion_question": (
            "A conversion is still running. Continuing is the safe choice. "
            "If you cancel and close, the active file may finish and remaining "
            "files will be cancelled."
        ),
        "continue_conversion": "Continue conversion",
        "cancel_conversion_and_close": "Cancel conversion and close",
        "results_heading": "Results",
        "results_empty": "No conversion results yet.",
        "result_file_heading": "File",
        "result_status_heading": "Status",
        "result_output_heading": "Output",
        "result_actions_heading": "Actions",
        "result_status_ok": "Succeeded",
        "result_status_error": "Failed",
        "result_status_kept": "Kept",
        "result_status_cancelled": "Cancelled",
        "result_output_value": "Output: {output}",
        "result_kept_summary": "Existing PDF kept: {output}",
        "result_cancelled_summary": "Conversion was cancelled.",
        "result_error_code": "Technical code: {code}",
        "show_details": "Show details",
        "hide_details": "Hide details",
        "expand_results": "Expand",
        "collapse_results": "Collapse",
        "clear_results": "Clear results",
        "batch_error": "Batch error",
        "open_pdf": "Open PDF",
        "open_folder": "Open folder",
        "open_error": "Could not open the selected path: {error}",
    },
    "fr": {
        "app_title": "LibreMark PDF",
        "app_version_compact": "v{version}",
        "gallery_title": "Galerie des composants de l’IHM moderne",
        "gallery_foundations": "Fondations visuelles",
        "gallery_components_tab": "Composants",
        "gallery_icons_tab": "Icônes",
        "gallery_buttons": "Boutons et états",
        "gallery_primary": "Action principale",
        "gallery_secondary": "Action secondaire",
        "gallery_disabled": "Désactivé",
        "gallery_hover": "Survol",
        "gallery_pressed": "Pressé",
        "gallery_icon_action": "Actualiser l’aperçu",
        "gallery_badges": "Badges d’état",
        "gallery_neutral": "En attente",
        "gallery_success": "Réussi",
        "gallery_warning": "Attention",
        "gallery_error": "Échec",
        "gallery_info": "Information",
        "gallery_typography": "Typographie et cartes",
        "gallery_body": (
            "Texte courant lisible sur une surface bureautique sobre."
        ),
        "gallery_secondary_text": (
            "Les informations secondaires restent lisibles."
        ),
        "gallery_focus_hint": (
            "Utilisez Tab pour vérifier le focus. Survolez les boutons icônes "
            "pour afficher leur aide localisée."
        ),
        "gallery_icon_variants": "Neutre · accent · succès · erreur",
        "help_menu": "Aide",
        "language_menu": "Langue",
        "language_english_name": "Anglais",
        "language_french_name": "Français",
        "compact_menu_a11y": "Menu de l’application",
        "window_minimize_a11y": "Réduire la fenêtre",
        "window_maximize_a11y": "Agrandir la fenêtre",
        "window_restore_a11y": "Restaurer la fenêtre",
        "window_close_a11y": "Fermer la fenêtre",
        "manual_action": "Manuel utilisateur",
        "manual_open_error": (
            "Impossible d’ouvrir le manuel utilisateur : {error}"
        ),
        "notices_open_error": (
            "Impossible d’ouvrir les mentions des composants tiers : {error}"
        ),
        "about_action": "À propos de LibreMark PDF",
        "about_version": "LibreMark PDF {version}",
        "about_local_conversion": "Conversion locale de Markdown en PDF",
        "about_no_network": "Aucune donnée envoyée sur le réseau",
        "third_party_notices_action": "Mentions des composants tiers",
        "technical_information": "Informations techniques",
        "copy_technical_information": "Copier les informations techniques",
        "technical_information_copied": "Informations techniques copiées.",
        "close_action": "Fermer",
        "technical_app_version": "LibreMark PDF",
        "technical_render_profile": "Profil de rendu",
        "technical_playwright": "Playwright",
        "technical_chromium": "Chromium",
        "technical_chromium_revision": "Révision Chromium",
        "technical_python": "Python",
        "technical_system": "Système",
        "technical_architecture": "Architecture",
        "technical_execution_mode": "Mode d’exécution",
        "execution_mode_source": "Sources",
        "execution_mode_artifact": "Artefact",
        "report_issue_action": "Signaler un problème",
        "report_title": "Signaler un problème",
        "report_intro": (
            "Décrivez le problème, puis vérifiez le rapport local complet. "
            "Rien n’est envoyé automatiquement."
        ),
        "report_document_title": "Rapport de problème LibreMark PDF",
        "report_summary": "Que s’est-il passé ?",
        "report_summary_placeholder": "Décrivez brièvement le problème…",
        "report_summary_required": (
            "Décrivez ce qui s’est passé avant de vérifier le rapport."
        ),
        "report_steps": "Étapes pour reproduire le problème (facultatif)",
        "report_expected": "Résultat attendu (facultatif)",
        "report_error_code": "Code d’erreur",
        "report_error_context": "Contexte de l’erreur",
        "include_diagnostics": "Inclure un diagnostic technique anonymisé",
        "diagnostics_consent": (
            "Rien n’est envoyé automatiquement. Vérifiez le rapport avant de "
            "le copier ou de l’enregistrer."
        ),
        "report_local_help": (
            "Copiez ou enregistrez ce rapport, vérifiez qu’il ne contient pas "
            "d’informations privées, puis partagez-le par un canal d’assistance "
            "officiel. N’incluez aucun Markdown, PDF ou CSS confidentiel ni "
            "aucune donnée personnelle."
        ),
        "preview_report": "Vérifier le rapport",
        "report_preview": "Rapport modifiable",
        "report_preview_help": (
            "Vérifiez et modifiez ce rapport complet avant de le copier ou de "
            "l’enregistrer."
        ),
        "report_preview_expand": "Afficher le rapport modifiable",
        "report_preview_collapse": "Masquer le rapport modifiable",
        "report_preview_edited": (
            "Vos modifications sont conservées. Sélectionnez Vérifier le "
            "rapport pour le reconstruire."
        ),
        "report_diagnostics_heading": "Diagnostic technique anonymisé (JSON)",
        "copy_report": "Copier le rapport",
        "save_report": "Enregistrer le rapport…",
        "open_support_channel": "Ouvrir la page d’assistance",
        "support_not_configured": (
            "Aucune page d’assistance n’est configurée. Copiez ou enregistrez "
            "le rapport."
        ),
        "report_copied": "Rapport copié.",
        "report_saved": "Rapport enregistré.",
        "report_copy_error": "Impossible de copier le rapport : {error}",
        "report_save_error": "Impossible d’enregistrer le rapport : {error}",
        "support_open_error": (
            "Impossible d’ouvrir la page d’assistance : {error}"
        ),
        "report_text_filter": "Rapports texte",
        "report_save_title": "Enregistrer le rapport de problème",
        "source_files_label": "Fichiers sources",
        "drop_hint": "Déposez un ou plusieurs fichiers .md ici",
        "browse_files": "Parcourir les fichiers",
        "files_heading": "Fichiers",
        "compact_tab_files": "Fichiers",
        "compact_tab_preview": "Aperçu",
        "compact_tab_settings": "Réglages",
        "compact_tab_results": "Résultats",
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
        "files_add_summary": "{summary}",
        "file_feedback_added_one": "1 fichier ajouté",
        "file_feedback_added_many": "{count} fichiers ajoutés",
        "file_feedback_duplicate_one": "1 doublon",
        "file_feedback_duplicate_many": "{count} doublons",
        "file_feedback_unsupported_one": "1 type non pris en charge",
        "file_feedback_unsupported_many": (
            "{count} types non pris en charge"
        ),
        "files_ignored_one": "1 élément ignoré : {reason}",
        "files_ignored_many": "{count} éléments ignorés : {reason}",
        "duplicate_reason": "déjà présent dans la liste",
        "unsupported_reason": "seuls les fichiers .md et .markdown sont acceptés",
        "remove_file_a11y": "Retirer {name}",
        "clear_files": "Vider la liste",
        "remove_file": "Retirer",
        "active_preview_badge": "Aperçu actif",
        "reveal_source": "Afficher dans le dossier source",
        "copy_path": "Copier le chemin",
        "remove_from_batch": "Retirer de la liste",
        "all_remove_action": "Tout retirer",
        "file_mutation_disabled": (
            "Les modifications de la liste sont indisponibles pendant la "
            "conversion."
        ),
        "conversion_pending": "En attente",
        "conversion_running": "En cours",
        "conversion_ok": "Réussi",
        "conversion_error": "Échec",
        "conversion_kept": "Conservé",
        "conversion_cancelled": "Annulé",
        "themes_label": "Thèmes",
        "style_heading": "Style PDF",
        "settings_heading": "Réglages",
        "cancel_settings": "Annuler",
        "save_settings": "Enregistrer",
        "back_settings": "Retour",
        "style_editor_title": "Style PDF",
        "style_editor_description": (
            "Choisissez un thème local ou un fichier CSS personnalisé pour "
            "cette session."
        ),
        "style_theme_technical": "Identifiant du thème : {reference}",
        "css_empty_state": "Aucun fichier CSS sélectionné",
        "css_validation_required": (
            "Choisissez un fichier CSS pour utiliser le CSS personnalisé."
        ),
        "css_validation_invalid": (
            "Ce CSS ne peut pas être utilisé. Choisissez un autre fichier CSS local."
        ),
        "destination_editor_title": "Destination",
        "destination_editor_description": (
            "Choisissez où enregistrer les PDF générés. Cela ne modifie pas l’aperçu."
        ),
        "destination_source_option": (
            "Même dossier que chaque fichier source"
        ),
        "destination_custom_option": "Dossier unique",
        "destination_choose_folder": "Parcourir",
        "destination_no_folder_selected": "Aucun dossier sélectionné",
        "destination_validation_required": (
            "Choisissez un dossier pour utiliser une destination unique."
        ),
        "header_footer_editor_title": "En-têtes et pieds de page",
        "header_footer_editor_description": (
            "Ajoutez du texte facultatif à six positions. Un champ vide "
            "n’affiche aucun contenu."
        ),
        "header_footer_tokens_label": "Insérer une variable",
        "header_footer_token_help": (
            "{titre} ou {title} : titre du document · {date} : date du rendu · "
            "{page} : page courante · {total} : nombre total de pages"
        ),
        "restore_header_footer_title": (
            "Rétablir les en-têtes et pieds de page par défaut ?"
        ),
        "restore_header_footer_question": (
            "Les valeurs personnalisées des en-têtes ou pieds de page seront "
            "remplacées. Les autres réglages PDF ne changeront pas."
        ),
        "advanced_options_heading": "Options avancées",
        "advanced_editor_title": "Options avancées",
        "advanced_editor_description": (
            "Choisissez la date de rendu et si le HTML statique de confiance "
            "est autorisé."
        ),
        "settings_default_theme": "Thème par défaut",
        "settings_css_summary": "CSS personnalisé · {path}",
        "settings_none": "Aucun",
        "header_left_summary": "En-tête gauche : {value}",
        "header_center_summary": "En-tête central : {value}",
        "header_right_summary": "En-tête droit : {value}",
        "footer_left_summary": "Pied gauche : {value}",
        "footer_center_summary": "Pied central : {value}",
        "footer_right_summary": "Pied droit : {value}",
        "other_automatic_summary": "Date automatique · HTML sécurisé",
        "other_date_trusted_summary": (
            "Date : {date} · HTML de confiance activé"
        ),
        "local_theme": "Thème local",
        "custom_css": "CSS personnalisé",
        "choose_css": "Choisir un CSS",
        "use_theme": "Utiliser le thème sélectionné",
        "css_style_label": "Style CSS",
        "css_default_value": "style.css (par défaut)",
        "change": "Changer",
        "advanced_header_footer": "En-tête et pied de page (avancé)",
        "tokens_hint": "Jetons : {titre} {title} {date} {page} {total}",
        "header_label": "En-tête",
        "footer_label": "Pied de page",
        "position_left": "Gauche",
        "position_center": "Centre",
        "position_right": "Droite",
        "reset_header_footer": "Rétablir les valeurs par défaut",
        "render_date": "Date de rendu (AAAA-MM-JJ)",
        "render_date_automatic_help": (
            "Laissez ce champ vide pour utiliser automatiquement la date du jour."
        ),
        "render_date_validation_invalid": (
            "Saisissez une date valide au format AAAA-MM-JJ ou laissez le champ vide."
        ),
        "trusted_html": "Autoriser le HTML statique de confiance",
        "trusted_html_help": (
            "À utiliser uniquement avec un contenu de confiance. Les scripts, "
            "ressources distantes et contenus actifs restent bloqués."
        ),
        "trusted_html_confirm_title": "Autoriser le HTML de confiance ?",
        "trusted_html_allow": "Autoriser",
        "trusted_html_confirm": (
            "Cette option modifie l’interprétation du HTML brut dans le "
            "Markdown. Continuez uniquement si le fichier est fiable."
        ),
        "header_footer_heading": "En-têtes et pieds de page",
        "settings_default": "Par défaut",
        "settings_custom": "Personnalisé",
        "other_date_summary": "Date : {date}",
        "other_trusted_summary": "HTML de confiance activé",
        "left_placeholder": "Gauche",
        "center_placeholder": "Centre",
        "right_placeholder": "Droite",
        "refresh_preview": "Réinitialiser l'aperçu et ajuster à la page",
        "preview_heading": "Aperçu",
        "refresh_preview_a11y": "Réinitialiser l’aperçu et ajuster à la page",
        "preview_empty": "Ajoutez ou sélectionnez un fichier pour le prévisualiser.",
        "preview_loading": "Mise à jour de l’aperçu…",
        "preview_scheduled": "Mise à jour de l’aperçu programmée…",
        "preview_rendering": "Mise à jour de l’aperçu…",
        "preview_error_title": "Impossible de générer l’aperçu",
        "preview_unavailable": "Aperçu indisponible",
        "preview_retry": "Réessayer",
        "preview_conversion_possible": (
            "Vous pouvez tout de même essayer de générer le PDF."
        ),
        "copy_details": "Copier les détails",
        "preview_page": "Page {current} sur {total}",
        "previous_page_a11y": "Page précédente",
        "next_page_a11y": "Page suivante",
        "zoom_out_a11y": "Réduire le zoom",
        "zoom_in_a11y": "Augmenter le zoom",
        "zoom_value": "{percent} %",
        "fit_page": "Ajuster à la page",
        "fit_width": "Ajuster à la largeur",
        "preview_more_a11y": "Autres actions d’aperçu",
        "preview_canvas_a11y": "Aperçu du document",
        "keyboard_shortcuts_action": "Raccourcis clavier",
        "language_english_a11y": "Passer l’interface en anglais",
        "language_french_a11y": "Passer l’interface en français",
        "shortcut_add_files": "Ajouter des fichiers",
        "shortcut_refresh_preview": "Actualiser l’aperçu",
        "shortcut_generate": "Générer",
        "shortcut_zoom_in": "Zoom avant",
        "shortcut_zoom_out": "Zoom arrière",
        "shortcut_reset_zoom": "Réinitialiser le zoom",
        "shortcut_previous_page": "Page précédente",
        "shortcut_next_page": "Page suivante",
        "shortcut_cancel_batch": "Annuler le lot actif",
        "output_label": "Sortie",
        "destination_heading": "Destination",
        "source_destination_one": "À côté du fichier source",
        "source_destination_many": "À côté de chaque fichier source",
        "generate_one": "Générer le PDF",
        "generate_many": "Générer {count} PDF",
        "action_blocked_no_files": "Ajoutez au moins un fichier Markdown pour générer un PDF.",
        "action_blocked_validating": "La génération est indisponible pendant la vérification des sorties.",
        "action_progress_completed": "{current} sur {total} terminés · {percent} %",
        "action_active_stage": "Fichier {current} sur {total} · {name} — {stage}",
        "action_running_one": "1 fichier en cours · Destination : {destination}",
        "action_running_many": "{count} fichiers en cours · Destination : {destination}",
        "applied_options": "Options appliquées ⓘ",
        "conversion_stage_preparing": "Préparation du document…",
        "conversion_stage_rendering": "Rendu avec Chromium…",
        "conversion_stage_finalizing": "Finalisation du PDF…",
        "conversion_stage_publishing": "Publication sécurisée…",
        "stop_after_current": "Arrêter après ce fichier",
        "cancel_now": "Annuler maintenant",
        "status_cancelling_now": "Annulation au prochain point sûr — cela peut prendre quelques secondes.",
        "cancel_button": "Annuler après ce fichier",
        "cancel_button_short": "Annuler",
        "status_ready": "Prêt.",
        "action_ready_one": "1 fichier prêt · Destination : {destination}",
        "action_ready_many": (
            "{count} fichiers prêts · Destination : {destination}"
        ),
        "status_generating": "Génération en cours…",
        "status_validating": "… Vérification des sorties…",
        "status_generating_progress": "{current} sur {total}",
        "status_generating_file": "→ Conversion {current} sur {total} — {name}",
        "status_cancelling": "Annulation après le fichier en cours…",
        "status_cancelling_file": "! Arrêt demandé — {name} peut se terminer.",
        "status_cancelled": "Conversion annulée avant son démarrage.",
        "status_closing": "Fin de l’opération en cours avant la fermeture…",
        "status_done_summary": "{summary}",
        "summary_succeeded_one": "{count} réussi",
        "summary_succeeded_many": "{count} réussis",
        "summary_failed_one": "{count} échec",
        "summary_failed_many": "{count} échecs",
        "summary_kept_one": "{count} conservé",
        "summary_kept_many": "{count} conservés",
        "summary_cancelled_one": "{count} annulé",
        "summary_cancelled_many": "{count} annulés",
        "status_rendering_preview": "Génération de l'aperçu…",
        "status_preview_error": "Impossible de générer l'aperçu : {error}",
        "status_generation_error": "Impossible de terminer la conversion : {error}",
        "status_details_copied": "Détails de l’erreur copiés.",
        "status_theme_error": "Impossible de charger les thèmes installés : {error}",
        "error_title": "Erreur",
        "error_no_files": "Ajoutez d’abord au moins un fichier .md.",
        "error_generation": "Échec de la conversion : {error}",
        "css_filter_name": "Fichiers CSS",
        "markdown_filter_name": "Fichiers Markdown",
        "choose_output_folder_title": "Choisir un dossier de sortie",
        "choose_css_title": "Choisir un fichier CSS",
        "choose_markdown_title": "Choisir un ou plusieurs fichiers Markdown",
        "collision_title": "Conflits de sortie",
        "collision_continue": (
            "Ces entrées ne peuvent pas être écrites vers les sorties prévues "
            "et seront signalées comme des échecs :\n\n{details}\n\nPoursuivre "
            "avec les fichiers indépendants ?"
        ),
        "continue_with_others": "Continuer avec les autres fichiers",
        "overwrite_title": "PDF existants",
        "decision_required_title": "Décision requise",
        "decision_conflict_one": "{count} conflit",
        "decision_conflict_many": "{count} conflits",
        "decision_existing_one": "{count} PDF existant",
        "decision_existing_many": "{count} PDF existants",
        "decision_replace_instruction": (
            "Cochez les PDF à remplacer. Les autres seront conservés."
        ),
        "decision_blocked_instruction": (
            "Les fichiers bloqués ne peuvent pas être générés et seront signalés."
        ),
        "decision_source_heading": "Source",
        "decision_destination_heading": "Destination",
        "decision_issue_heading": "Problème",
        "decision_replace_heading": "Remplacer ?",
        "decision_blocked": "Bloqué",
        "decision_replace_help": (
            "Coché : remplacer uniquement après une conversion réussie. "
            "Non coché : conserver le PDF existant."
        ),
        "decision_blocked_help": (
            "Cette destination est bloquée et ne peut pas être sélectionnée "
            "pour remplacement."
        ),
        "decision_replaced_one": "{count} sera remplacé",
        "decision_replaced_many": "{count} seront remplacés",
        "decision_kept_one": "{count} conservé",
        "decision_kept_many": "{count} conservés",
        "decision_issue_duplicate": "Même destination",
        "decision_issue_same_path": "Source = destination",
        "decision_issue_missing_input": "Source indisponible",
        "decision_issue_existing": "PDF déjà présent",
        "decision_issue_other": "Sortie indisponible",
        "continue_generation": "Continuer",
        "back_action": "Retour",
        "overwrite_question_one": (
            "1 PDF de sortie existe déjà. Choisissez de le remplacer uniquement "
            "après un rendu réussi, ou de le conserver et de signaler un échec."
        ),
        "overwrite_question_many": (
            "{count} PDF de sortie existent déjà. Choisissez de les remplacer "
            "uniquement après un rendu réussi, ou de les conserver et de "
            "signaler des échecs."
        ),
        "close_conversion_title": "Conversion en cours",
        "close_conversion_question": (
            "Une conversion est toujours en cours. La poursuivre est le choix "
            "sûr. Si vous annulez et fermez, le fichier actif peut se terminer "
            "et les fichiers restants seront annulés."
        ),
        "continue_conversion": "Continuer la conversion",
        "cancel_conversion_and_close": "Annuler la conversion et fermer",
        "results_heading": "Résultats",
        "results_empty": "Aucun résultat de conversion pour le moment.",
        "result_file_heading": "Fichier",
        "result_status_heading": "État",
        "result_output_heading": "Sortie",
        "result_actions_heading": "Actions",
        "result_status_ok": "Réussi",
        "result_status_error": "Échec",
        "result_status_kept": "Conservé",
        "result_status_cancelled": "Annulé",
        "result_output_value": "Sortie : {output}",
        "result_kept_summary": "PDF existant conservé : {output}",
        "result_cancelled_summary": "La conversion a été annulée.",
        "result_error_code": "Code technique : {code}",
        "show_details": "Afficher les détails",
        "hide_details": "Masquer les détails",
        "expand_results": "Déployer",
        "collapse_results": "Replier",
        "clear_results": "Effacer les résultats",
        "batch_error": "Erreur globale du lot",
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


def plural_key(one_key: str, many_key: str, count: int) -> str:
    """Return the one or many key for the supported two-form rule."""
    return one_key if count == 1 else many_key
