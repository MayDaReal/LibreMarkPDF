"""Central ttk styles and layout metrics for the desktop interface."""

from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk
from typing import NamedTuple


SPACE_XS = 4
SPACE_SM = 8
SPACE_MD = 12
SPACE_LG = 16

SECTION_PADDING = SPACE_SM
SECTION_GAP = SPACE_MD
OUTER_PADDING = SPACE_LG
DROP_ZONE_HEIGHT = 96
FILE_LIST_HEIGHT = 96
FILE_ROW_HEIGHT = 44
PREVIEW_HEIGHT = 330
STATUS_WRAP_LENGTH = 720

TITLE_LABEL_STYLE = "App.Title.TLabel"
PRIMARY_BUTTON_STYLE = "App.Primary.TButton"
ACTIVE_FILE_ROW_STYLE = "App.ActiveFile.TRadiobutton"
ICON_BUTTON_STYLE = "App.Icon.TButton"
STATUS_LABEL_STYLE = "App.Status.TLabel"
ERROR_STATUS_LABEL_STYLE = "App.Error.Status.TLabel"
SUCCESS_STATUS_LABEL_STYLE = "App.Success.Status.TLabel"

ERROR_STATUS_KEYS = frozenset((
    "status_preview_error",
    "status_generation_error",
    "status_theme_error",
))
SUCCESS_STATUS_KEYS = frozenset((
    "status_done",
    "status_done_summary",
))


class UiStyleResources(NamedTuple):
    """Theme-derived resources needed by classic Tk canvas widgets."""

    drop_background: str
    drop_border: str
    preview_background: str
    title_font: tkfont.Font
    emphasis_font: tkfont.Font


def _theme_color(style: ttk.Style, style_name: str, option: str) -> str:
    value = style.lookup(style_name, option)
    if value:
        return value
    return style.lookup("TFrame", "background")


def install_ui_styles(root: tk.Misc) -> UiStyleResources:
    """Install application styles while retaining the active native palette."""
    style = ttk.Style(root)
    default_font = tkfont.Font(
        root=root,
        name="TkDefaultFont",
        exists=True,
    )
    title_font = default_font.copy()
    title_font.configure(
        size=int(default_font.cget("size")) + 2,
        weight="bold",
    )
    emphasis_font = default_font.copy()
    emphasis_font.configure(weight="bold")

    style.configure(TITLE_LABEL_STYLE, font=title_font)
    style.configure(
        PRIMARY_BUTTON_STYLE,
        padding=(SPACE_MD, SPACE_MD),
    )
    style.configure(
        ACTIVE_FILE_ROW_STYLE,
        font=emphasis_font,
        anchor="w",
    )
    style.configure(
        ICON_BUTTON_STYLE,
        padding=(SPACE_SM, SPACE_SM),
    )
    style.configure(
        STATUS_LABEL_STYLE,
        padding=(0, SPACE_XS),
    )
    style.configure(
        ERROR_STATUS_LABEL_STYLE,
        font=emphasis_font,
        padding=(0, SPACE_XS),
    )
    style.configure(
        SUCCESS_STATUS_LABEL_STYLE,
        font=emphasis_font,
        padding=(0, SPACE_XS),
    )

    frame_background = _theme_color(style, "TFrame", "background")
    field_background = (
        _theme_color(style, "TEntry", "fieldbackground")
        or frame_background
    )
    border = (
        style.lookup("TEntry", "bordercolor")
        or _theme_color(style, "TLabel", "foreground")
    )
    return UiStyleResources(
        drop_background=field_background,
        drop_border=border,
        preview_background=frame_background,
        title_font=title_font,
        emphasis_font=emphasis_font,
    )


def status_label_style(status_key: str) -> str:
    """Return the semantic label style for an application status."""
    if status_key in ERROR_STATUS_KEYS:
        return ERROR_STATUS_LABEL_STYLE
    if status_key in SUCCESS_STATUS_KEYS:
        return SUCCESS_STATUS_LABEL_STYLE
    return STATUS_LABEL_STYLE
