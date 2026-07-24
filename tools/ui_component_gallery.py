"""Internal Windows gallery for the modern UI atomic components."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Optional

import customtkinter as ctk

from libremark_pdf.desktop.ctk.assets import ICON_NAMES, UiAssetRegistry
from libremark_pdf.desktop.ctk.components import (
    CardFrame,
    IconButton,
    PrimaryButton,
    SecondaryButton,
    SectionTitle,
    StatusBadge,
)
from libremark_pdf.desktop.ctk.theme import (
    COLORS,
    RADII,
    SPACING,
    SystemFontResolver,
    install_light_theme,
)
from libremark_pdf.i18n import LANGUAGES, t


class ComponentGallery(ctk.CTk):
    """Show all lot-1 foundations without connecting to product behavior."""

    def __init__(
        self,
        language: str,
        geometry: str,
        scale: float,
        initial_tab: str = "components",
        asset_root: Optional[Path] = None,
    ) -> None:
        install_light_theme()
        ctk.set_widget_scaling(scale)
        ctk.set_window_scaling(scale)
        super().__init__(fg_color=COLORS["app_bg"])
        self.language = language
        self.title(
            "LibreMark PDF — {0}".format(t("gallery_title", self.language))
        )
        self.geometry(geometry)
        self.minsize(820, 620)
        self.fonts = SystemFontResolver(self)
        self.assets = UiAssetRegistry(self, asset_root=asset_root)
        self._build()
        tab_key = (
            "gallery_icons_tab"
            if initial_tab == "icons"
            else "gallery_components_tab"
        )
        self.tabs.set(t(tab_key, self.language))

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(
            self,
            height=64,
            corner_radius=0,
            fg_color=COLORS["surface"],
            border_width=0,
        )
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(
            header,
            text=t("app_title", self.language),
            font=self.fonts.font("product"),
            text_color=COLORS["text"],
        ).grid(
            row=0,
            column=0,
            padx=(SPACING["lg"], SPACING["sm"]),
            pady=SPACING["lg"],
            sticky="w",
        )
        ctk.CTkLabel(
            header,
            text=t("gallery_foundations", self.language),
            font=self.fonts.font("secondary"),
            text_color=COLORS["text_secondary"],
        ).grid(
            row=0,
            column=1,
            padx=SPACING["sm"],
            pady=SPACING["lg"],
            sticky="w",
        )
        ctk.CTkLabel(
            header,
            text=self.language.upper(),
            width=38,
            height=24,
            corner_radius=RADII["pill"],
            fg_color=COLORS["primary_subtle"],
            text_color=COLORS["primary"],
            font=self.fonts.font("badge"),
        ).grid(
            row=0,
            column=2,
            padx=SPACING["lg"],
            pady=SPACING["lg"],
        )

        tabs = ctk.CTkTabview(
            self,
            corner_radius=RADII["card"],
            fg_color=COLORS["surface"],
            border_width=1,
            border_color=COLORS["border"],
            segmented_button_fg_color=COLORS["surface_subtle"],
            segmented_button_selected_color=COLORS["primary"],
            segmented_button_selected_hover_color=COLORS["primary_hover"],
            segmented_button_unselected_color=COLORS["surface_subtle"],
            segmented_button_unselected_hover_color=COLORS["surface_hover"],
            text_color=COLORS["text"],
        )
        self.tabs = tabs
        tabs.grid(
            row=1,
            column=0,
            padx=SPACING["lg"],
            pady=SPACING["lg"],
            sticky="nsew",
        )
        components_tab = tabs.add(t("gallery_components_tab", self.language))
        icons_tab = tabs.add(t("gallery_icons_tab", self.language))
        self._build_components(components_tab)
        self._build_icons(icons_tab)

    def _build_components(self, parent) -> None:
        parent.grid_columnconfigure((0, 1), weight=1)
        parent.grid_rowconfigure(1, weight=1)

        buttons = CardFrame(parent)
        buttons.grid(
            row=0,
            column=0,
            padx=(SPACING["md"], SPACING["sm"]),
            pady=SPACING["md"],
            sticky="nsew",
        )
        buttons.grid_columnconfigure((0, 1), weight=1)
        SectionTitle(
            buttons,
            t("gallery_buttons", self.language),
            self.fonts,
        ).grid(
            row=0,
            column=0,
            columnspan=2,
            padx=SPACING["md"],
            pady=(SPACING["md"], SPACING["sm"]),
            sticky="ew",
        )
        self.primary = PrimaryButton(
            buttons,
            text=t("gallery_primary", self.language),
            command=lambda: None,
            font=self.fonts.font("label"),
        )
        self.primary.grid(
            row=1,
            column=0,
            padx=SPACING["md"],
            pady=SPACING["sm"],
            sticky="ew",
        )
        self.secondary = SecondaryButton(
            buttons,
            text=t("gallery_secondary", self.language),
            command=lambda: None,
            font=self.fonts.font("label"),
        )
        self.secondary.grid(
            row=1,
            column=1,
            padx=SPACING["md"],
            pady=SPACING["sm"],
            sticky="ew",
        )
        self.after(
            250,
            self.secondary.focus_ring.show,
        )
        disabled_primary = PrimaryButton(
            buttons,
            text=t("gallery_disabled", self.language),
            command=lambda: None,
            font=self.fonts.font("label"),
            state="disabled",
        )
        disabled_primary.grid(
            row=2,
            column=0,
            padx=SPACING["md"],
            pady=SPACING["sm"],
            sticky="ew",
        )
        disabled_secondary = SecondaryButton(
            buttons,
            text=t("gallery_disabled", self.language),
            command=lambda: None,
            font=self.fonts.font("label"),
            state="disabled",
        )
        disabled_secondary.grid(
            row=2,
            column=1,
            padx=SPACING["md"],
            pady=SPACING["sm"],
            sticky="ew",
        )
        self.disabled_secondary = disabled_secondary
        hover_button = SecondaryButton(
            buttons,
            text=t("gallery_hover", self.language),
            command=lambda: None,
            font=self.fonts.font("label"),
        )
        hover_button.set_interaction_state("hover")
        hover_button.grid(
            row=3,
            column=0,
            padx=SPACING["md"],
            pady=SPACING["sm"],
            sticky="ew",
        )
        pressed_button = PrimaryButton(
            buttons,
            text=t("gallery_pressed", self.language),
            command=lambda: None,
            font=self.fonts.font("label"),
        )
        pressed_button.set_interaction_state("pressed")
        pressed_button.grid(
            row=3,
            column=1,
            padx=SPACING["md"],
            pady=SPACING["sm"],
            sticky="ew",
        )
        icon_row = ctk.CTkFrame(buttons, fg_color="transparent")
        icon_row.grid(
            row=4,
            column=0,
            columnspan=2,
            padx=SPACING["md"],
            pady=(SPACING["sm"], SPACING["md"]),
            sticky="w",
        )
        for column, name in enumerate(
            ("plus", "arrow-clockwise", "three-dots-vertical", "x-lg")
        ):
            button = IconButton(
                icon_row,
                image=self.assets.image(name, 20, "neutral"),
                accessible_name=t("gallery_icon_action", self.language),
                command=lambda: None,
            )
            button.grid(row=0, column=column, padx=(0, SPACING["sm"]))
            if column == 0:
                self.probe_icon_button = button

        badges = CardFrame(parent)
        badges.grid(
            row=0,
            column=1,
            padx=(SPACING["sm"], SPACING["md"]),
            pady=SPACING["md"],
            sticky="nsew",
        )
        SectionTitle(
            badges,
            t("gallery_badges", self.language),
            self.fonts,
        ).pack(
            padx=SPACING["md"],
            pady=(SPACING["md"], SPACING["sm"]),
            anchor="w",
        )
        badge_specs = (
            ("neutral", "gallery_neutral", None),
            ("success", "gallery_success", ("check-circle-fill", "success")),
            ("warning", "gallery_warning", None),
            ("error", "gallery_error", ("exclamation-circle-fill", "error")),
            ("info", "gallery_info", ("info-circle-fill", "accent")),
        )
        for tone, key, icon in badge_specs:
            image = (
                self.assets.image(icon[0], 16, icon[1])
                if icon is not None
                else None
            )
            StatusBadge(
                badges,
                text=t(key, self.language),
                tone=tone,
                image=image,
                font=self.fonts.font("badge"),
            ).pack(
                side="left",
                padx=(SPACING["md"], 0),
                pady=(SPACING["sm"], SPACING["md"]),
            )

        typography = CardFrame(parent)
        typography.grid(
            row=1,
            column=0,
            columnspan=2,
            padx=SPACING["md"],
            pady=(0, SPACING["md"]),
            sticky="nsew",
        )
        typography.grid_columnconfigure(0, weight=1)
        SectionTitle(
            typography,
            t("gallery_typography", self.language),
            self.fonts,
        ).grid(
            row=0,
            column=0,
            padx=SPACING["md"],
            pady=(SPACING["md"], SPACING["xs"]),
            sticky="w",
        )
        ctk.CTkLabel(
            typography,
            text=t("gallery_body", self.language),
            anchor="w",
            font=self.fonts.font("body"),
            text_color=COLORS["text"],
        ).grid(
            row=1,
            column=0,
            padx=SPACING["md"],
            pady=SPACING["xs"],
            sticky="ew",
        )
        ctk.CTkLabel(
            typography,
            text=t("gallery_secondary_text", self.language),
            anchor="w",
            font=self.fonts.font("secondary"),
            text_color=COLORS["text_secondary"],
        ).grid(
            row=2,
            column=0,
            padx=SPACING["md"],
            pady=SPACING["xs"],
            sticky="ew",
        )
        ctk.CTkLabel(
            typography,
            text=t("gallery_focus_hint", self.language),
            anchor="w",
            font=self.fonts.font("technical", monospace=True),
            text_color=COLORS["text_secondary"],
        ).grid(
            row=3,
            column=0,
            padx=SPACING["md"],
            pady=(SPACING["xs"], SPACING["md"]),
            sticky="ew",
        )

    def _build_icons(self, parent) -> None:
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(0, weight=1)
        scroll = ctk.CTkScrollableFrame(
            parent,
            corner_radius=0,
            fg_color=COLORS["surface"],
            label_text=t("gallery_icon_variants", self.language),
            label_fg_color=COLORS["surface_subtle"],
            label_text_color=COLORS["text_secondary"],
            scrollbar_fg_color=COLORS["surface"],
            scrollbar_button_color=COLORS["border_strong"],
            scrollbar_button_hover_color=COLORS["text_muted"],
        )
        scroll.grid(
            row=0,
            column=0,
            padx=SPACING["md"],
            pady=SPACING["md"],
            sticky="nsew",
        )
        scroll.grid_columnconfigure(1, weight=1)
        for row, name in enumerate(ICON_NAMES):
            ctk.CTkLabel(
                scroll,
                text=name,
                anchor="w",
                font=self.fonts.font("technical", monospace=True),
                text_color=COLORS["text_secondary"],
            ).grid(
                row=row,
                column=0,
                padx=SPACING["md"],
                pady=SPACING["xs"],
                sticky="w",
            )
            icon_row = ctk.CTkFrame(scroll, fg_color="transparent")
            icon_row.grid(row=row, column=1, sticky="w")
            for column, color in enumerate(
                ("neutral", "accent", "success", "error")
            ):
                IconButton(
                    icon_row,
                    image=self.assets.image(name, 20, color),
                    accessible_name=name,
                    command=lambda: None,
                ).grid(
                    row=0,
                    column=column,
                    padx=SPACING["xs"],
                )

    def public_probe(self) -> dict:
        """Return observable component state without product-service access."""
        self.update()
        self.secondary.focus_ring.show()
        self.update()
        focused_border = {
            "color": self.secondary.cget("border_color"),
            "width": self.secondary.cget("border_width"),
        }
        self.primary.set_interaction_state("pressed")
        pressed_color = self.primary.cget("fg_color")
        self.primary.set_interaction_state("normal")
        self.probe_icon_button.tooltip.schedule()
        deadline = time.perf_counter() + 0.75
        while (
            not self.probe_icon_button.tooltip.visible
            and time.perf_counter() < deadline
        ):
            self.update()
            time.sleep(0.01)
        tooltip_bounds = self.probe_icon_button.tooltip.bounds
        tooltip_visible = self.probe_icon_button.tooltip.visible
        self.probe_icon_button.event_generate("<Leave>")
        self.update()
        return {
            "assets_retained": self.assets.retained_image_count,
            "customtkinter": ctk.__version__,
            "disabled_state": self.disabled_secondary.cget("state"),
            "focus_border": focused_border,
            "font_interface": self.fonts.families.interface,
            "font_monospace": self.fonts.families.monospace,
            "icon_accessible_name": self.probe_icon_button.accessible_name,
            "icon_size": self.probe_icon_button.cget("width"),
            "language": self.language,
            "pressed_color": pressed_color,
            "primary_height": self.primary.cget("height"),
            "title": self.title(),
            "tooltip_bounds": tooltip_bounds,
            "tooltip_visible": tooltip_visible,
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", choices=LANGUAGES, default="fr")
    parser.add_argument("--geometry", default="1080x760+40+40")
    parser.add_argument("--scale", type=float, default=1.0)
    parser.add_argument(
        "--tab",
        choices=("components", "icons"),
        default="components",
    )
    parser.add_argument("--ready-file", type=Path)
    parser.add_argument("--asset-root", type=Path)
    parser.add_argument("--auto-close-ms", type=int)
    parser.add_argument("--probe", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    app = ComponentGallery(
        args.lang,
        args.geometry,
        args.scale,
        initial_tab=args.tab,
        asset_root=args.asset_root,
    )
    if args.probe:
        print(json.dumps(app.public_probe(), sort_keys=True))
        app.destroy()
        return 0
    if args.ready_file is not None:
        app.after(
            350,
            lambda: args.ready_file.write_text("ready", encoding="utf-8"),
        )
    if args.auto_close_ms is not None:
        app.after(args.auto_close_ms, app.destroy)
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
