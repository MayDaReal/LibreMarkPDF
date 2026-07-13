"""Tk desktop front end for the shared conversion engine."""

from __future__ import annotations

import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Optional

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    _HAS_DND = True
except ImportError:  # Drag-and-drop is optional; file browsing remains usable.
    _HAS_DND = False

from . import core, i18n

LOGO_ICON_CACHE: dict[int, tk.PhotoImage] = {}


def _load_logo(size: int) -> tk.PhotoImage:
    if size not in LOGO_ICON_CACHE:
        path = core.resource_path(f"assets/libremark-pdf-logo-{size}.png")
        LOGO_ICON_CACHE[size] = tk.PhotoImage(file=str(path))
    return LOGO_ICON_CACHE[size]


SAMPLE_MARKDOWN = """# {title}

{body}

| Status | Description |
|---|---|
| Done | Everything works |
| Pending | Waiting on review |
"""

PREVIEW_DPI = 60


class LibreMarkPdfApp:
    """Coordinate desktop widgets and background conversion work."""

    def __init__(self, root: tk.Misc) -> None:
        self.root = root
        self.lang = i18n.load_language()

        self.files: list[Path] = []
        self.css_path: Optional[str] = None
        self.output_dir: Optional[str] = None
        # Tk discards images that have no live Python reference.
        self.preview_photo: Optional[tk.PhotoImage] = None

        self.hf_vars = {
            "header_left": tk.StringVar(), "header_center": tk.StringVar(),
            "header_right": tk.StringVar(), "footer_left": tk.StringVar(),
            "footer_center": tk.StringVar(value="Page {page} / {total}"),
            "footer_right": tk.StringVar(),
        }
        self.advanced_open = tk.BooleanVar(value=False)

        self._result_queue: "queue.Queue" = queue.Queue()

        self._build_ui()
        self._retranslate()

    def _build_ui(self) -> None:
        self.root.geometry("560x760")
        self.root.minsize(480, 640)

        top = tk.Frame(self.root, padx=14, pady=10)
        top.pack(fill="x")

        logo_img = _load_logo(32)
        logo_label = tk.Label(top, image=logo_img)
        logo_label.image = logo_img
        logo_label.pack(side="left")

        try:
            self.root.iconphoto(True, _load_logo(64))
        except Exception:
            # Window icons are platform-dependent and not required to launch.
            pass

        self.title_label = tk.Label(top, font=("Helvetica", 12, "bold"))
        self.title_label.pack(side="left", padx=10)

        lang_frame = tk.Frame(top)
        lang_frame.pack(side="right")
        self.btn_en = tk.Button(
            lang_frame, text="EN", width=3, command=lambda: self._set_lang("en")
        )
        self.btn_fr = tk.Button(
            lang_frame, text="FR", width=3, command=lambda: self._set_lang("fr")
        )
        self.btn_en.pack(side="left")
        self.btn_fr.pack(side="left")

        body = tk.Frame(self.root, padx=14, pady=6)
        body.pack(fill="both", expand=True)

        self.drop_canvas = tk.Canvas(
            body, height=100, bg="#f6f8fa", highlightthickness=0
        )
        self.drop_canvas.pack(fill="x", pady=(0, 10))
        self.drop_canvas.bind("<Configure>", self._redraw_drop_zone)
        self.drop_canvas.bind("<Button-1>", lambda e: self._browse_files())

        if _HAS_DND:
            self.drop_canvas.drop_target_register(DND_FILES)
            self.drop_canvas.dnd_bind("<<Drop>>", self._on_drop)

        self.file_list_frame = tk.Frame(body)
        self.file_list_frame.pack(fill="x", pady=(0, 10))

        css_row = tk.Frame(body)
        css_row.pack(fill="x", pady=(0, 10))
        self.css_label = tk.Label(css_row, width=12, anchor="w")
        self.css_label.pack(side="left")
        self.css_entry = tk.Entry(css_row, state="readonly")
        self.css_entry.pack(side="left", fill="x", expand=True, padx=6)
        self.css_button = tk.Button(css_row, command=self._choose_css)
        self.css_button.pack(side="left")

        adv_frame = tk.Frame(
            body, highlightbackground="#d1d9e0", highlightthickness=1
        )
        adv_frame.pack(fill="x", pady=(0, 10))

        self.adv_toggle_btn = tk.Button(
            adv_frame, anchor="w", relief="flat", command=self._toggle_advanced
        )
        self.adv_toggle_btn.pack(fill="x")

        self.adv_content = tk.Frame(adv_frame, padx=10, pady=8)
        # The advanced section starts collapsed, so it is packed on demand.

        self.tokens_hint_label = tk.Label(
            self.adv_content, fg="#59636e", font=("Helvetica", 9)
        )
        self.tokens_hint_label.pack(anchor="w", pady=(0, 8))

        self.header_group_label = tk.Label(self.adv_content, font=("Helvetica", 9, "bold"))
        self.header_group_label.pack(anchor="w")
        header_row = tk.Frame(self.adv_content)
        header_row.pack(fill="x", pady=(2, 8))
        self.header_left_entry = tk.Entry(
            header_row, textvariable=self.hf_vars["header_left"]
        )
        self.header_center_entry = tk.Entry(
            header_row, textvariable=self.hf_vars["header_center"]
        )
        self.header_right_entry = tk.Entry(
            header_row, textvariable=self.hf_vars["header_right"]
        )
        for entry in (
            self.header_left_entry,
            self.header_center_entry,
            self.header_right_entry,
        ):
            entry.pack(side="left", fill="x", expand=True, padx=2)

        self.footer_group_label = tk.Label(
            self.adv_content, font=("Helvetica", 9, "bold")
        )
        self.footer_group_label.pack(anchor="w")
        footer_row = tk.Frame(self.adv_content)
        footer_row.pack(fill="x", pady=(2, 0))
        self.footer_left_entry = tk.Entry(
            footer_row, textvariable=self.hf_vars["footer_left"]
        )
        self.footer_center_entry = tk.Entry(
            footer_row, textvariable=self.hf_vars["footer_center"]
        )
        self.footer_right_entry = tk.Entry(
            footer_row, textvariable=self.hf_vars["footer_right"]
        )
        for entry in (
            self.footer_left_entry,
            self.footer_center_entry,
            self.footer_right_entry,
        ):
            entry.pack(side="left", fill="x", expand=True, padx=2)

        preview_frame = tk.Frame(
            body,
            highlightbackground="#d1d9e0",
            highlightthickness=1,
            padx=10,
            pady=8,
        )
        preview_frame.pack(fill="x", pady=(0, 10))

        preview_header = tk.Frame(preview_frame)
        preview_header.pack(fill="x")
        self.preview_label = tk.Label(preview_header, font=("Helvetica", 9, "bold"))
        self.preview_label.pack(side="left")
        self.refresh_preview_btn = tk.Button(
            preview_header, command=self._refresh_preview
        )
        self.refresh_preview_btn.pack(side="right")

        self.preview_image_label = tk.Label(preview_frame, bg="#78828c")
        self.preview_image_label.pack(pady=(8, 0))

        output_row = tk.Frame(body)
        output_row.pack(fill="x", pady=(0, 10))
        self.output_label = tk.Label(output_row, width=12, anchor="w")
        self.output_label.pack(side="left")
        self.output_entry = tk.Entry(output_row, state="readonly")
        self.output_entry.pack(side="left", fill="x", expand=True, padx=6)
        self.output_button = tk.Button(output_row, command=self._choose_output_dir)
        self.output_button.pack(side="left")

        self.generate_button = tk.Button(
            body, bg="#0969da", fg="white", font=("Helvetica", 11, "bold"),
            command=self._on_generate_clicked,
        )
        self.generate_button.pack(fill="x", ipady=6, pady=(4, 6))

        self.status_label = tk.Label(body, fg="#59636e")
        self.status_label.pack()

    def _redraw_drop_zone(self, event=None):
        c = self.drop_canvas
        c.delete("all")
        w = c.winfo_width() or 500
        h = int(c["height"])
        c.create_rectangle(
            4, 4, w - 4, h - 4, outline="#8c959f", dash=(4, 3), width=2
        )
        c.create_text(
            w // 2,
            h // 2,
            text=self._drop_zone_text,
            fill="#59636e",
            font=("Helvetica", 10),
        )

    # Language and labels

    def _set_lang(self, lang: str) -> None:
        self.lang = lang
        i18n.save_language(lang)
        self._retranslate()

    def _t(self, key, **kwargs):
        return i18n.t(key, self.lang, **kwargs)

    def _retranslate(self):
        self.root.title(self._t("app_title"))
        self.title_label.config(text=self._t("app_title"))
        self._drop_zone_text = self._t("drop_hint") + "\n(" + self._t("browse_files") + ")"
        self._redraw_drop_zone()

        self.css_label.config(text=self._t("css_style_label"))
        self.css_button.config(text=self._t("change"))
        self._refresh_css_entry()

        self.adv_toggle_btn.config(
            text=("\u25be " if self.advanced_open.get() else "\u25b8 ")
            + self._t("advanced_header_footer")
        )
        self.tokens_hint_label.config(text=self._t("tokens_hint"))
        self.header_group_label.config(text=self._t("header_label"))
        self.footer_group_label.config(text=self._t("footer_label"))
        self.preview_label.config(text=self._t("preview_label"))
        self.refresh_preview_btn.config(text=self._t("refresh_preview"))

        self.output_label.config(text=self._t("output_label"))
        self.output_button.config(text=self._t("choose_folder"))
        self._refresh_output_entry()

        self._refresh_generate_button()
        self.status_label.config(text=self._t("status_ready"))

        for btn, active in ((self.btn_en, self.lang == "en"), (self.btn_fr, self.lang == "fr")):
            btn.config(relief="sunken" if active else "raised")

        self._render_file_list()

    # Source files

    def _on_drop(self, event):
        paths = self.root.tk.splitlist(event.data)
        self._add_files(paths)

    def _browse_files(self):
        paths = filedialog.askopenfilenames(
            title=self._t("choose_markdown_title"),
            filetypes=[(self._t("markdown_filter_name"), "*.md *.markdown")],
        )
        if paths:
            self._add_files(paths)

    def _add_files(self, paths):
        for p in paths:
            path = Path(p)
            if path.suffix.lower() in (".md", ".markdown") and path not in self.files:
                self.files.append(path)
        self._render_file_list()
        self._refresh_generate_button()

    def _remove_file(self, path: Path) -> None:
        self.files = [f for f in self.files if f != path]
        self._render_file_list()
        self._refresh_generate_button()

    def _render_file_list(self):
        for child in self.file_list_frame.winfo_children():
            child.destroy()
        for path in self.files:
            row = tk.Frame(
                self.file_list_frame,
                highlightbackground="#d1d9e0",
                highlightthickness=1,
            )
            row.pack(fill="x", pady=2)
            tk.Label(row, text=path.name, anchor="w").pack(side="left", padx=8, pady=4)
            tk.Button(
                row, text="\u2715", relief="flat", command=lambda p=path: self._remove_file(p)
            ).pack(side="right", padx=6)

    # CSS and output selection

    def _choose_css(self):
        path = filedialog.askopenfilename(
            title=self._t("choose_css_title"),
            filetypes=[(self._t("css_filter_name"), "*.css")],
        )
        if path:
            self.css_path = path
            self._refresh_css_entry()

    def _refresh_css_entry(self):
        value = self.css_path if self.css_path else self._t("css_default_value")
        self.css_entry.config(state="normal")
        self.css_entry.delete(0, "end")
        self.css_entry.insert(0, value)
        self.css_entry.config(state="readonly")

    def _choose_output_dir(self):
        path = filedialog.askdirectory(title=self._t("choose_output_folder_title"))
        if path:
            self.output_dir = path
            self._refresh_output_entry()

    def _refresh_output_entry(self):
        value = self.output_dir if self.output_dir else self._t("output_default_value")
        self.output_entry.config(state="normal")
        self.output_entry.delete(0, "end")
        self.output_entry.insert(0, value)
        self.output_entry.config(state="readonly")

    def _toggle_advanced(self):
        self.advanced_open.set(not self.advanced_open.get())
        if self.advanced_open.get():
            self.adv_content.pack(fill="x")
        else:
            self.adv_content.pack_forget()
        self.adv_toggle_btn.config(
            text=("\u25be " if self.advanced_open.get() else "\u25b8 ")
            + self._t("advanced_header_footer")
        )

    def _current_header_footer(self) -> core.HeaderFooterConfig:
        return core.HeaderFooterConfig(
            top_left=self.hf_vars["header_left"].get(),
            top_center=self.hf_vars["header_center"].get(),
            top_right=self.hf_vars["header_right"].get(),
            bottom_left=self.hf_vars["footer_left"].get(),
            bottom_center=self.hf_vars["footer_center"].get(),
            bottom_right=self.hf_vars["footer_right"].get(),
        )

    # Preview

    def _refresh_preview(self):
        self.status_label.config(text=self._t("status_rendering_preview"))
        self.root.update_idletasks()

        if self.files:
            try:
                markdown_text = self.files[0].read_text(encoding="utf-8")
            except Exception as exc:
                self.status_label.config(
                    text=self._t("status_preview_error", error=str(exc))
                )
                return
        else:
            markdown_text = SAMPLE_MARKDOWN.format(
                title=self._t("sample_preview_title"), body=self._t("sample_preview_body")
            )

        css_path = self.css_path or None
        hf = self._current_header_footer()

        def work():
            try:
                png_bytes = core.render_preview_png(
                    markdown_text, css_path=css_path, header_footer=hf, dpi=PREVIEW_DPI
                )
                self._result_queue.put(("preview_ok", png_bytes))
            except Exception as exc:
                # Worker exceptions cross the queue as displayable text; Tk
                # updates remain on the main thread.
                self._result_queue.put(("preview_error", str(exc)))

        threading.Thread(target=work, daemon=True).start()
        self.root.after(100, self._poll_queue)

    def _apply_preview_image(self, png_bytes: bytes):
        self.preview_photo = tk.PhotoImage(data=png_bytes)
        self.preview_image_label.config(image=self.preview_photo)
        self.status_label.config(text=self._t("status_ready"))

    # Conversion

    def _refresh_generate_button(self):
        self.generate_button.config(text=self._t("generate_button", count=len(self.files)))

    def _on_generate_clicked(self):
        if not self.files:
            messagebox.showerror(self._t("error_title"), self._t("error_no_files"))
            return

        self.status_label.config(text=self._t("status_generating"))
        self.generate_button.config(state="disabled")

        css_path = self.css_path or None
        out_dir = self.output_dir or None
        hf = self._current_header_footer()
        files = list(self.files)

        def work():
            results = core.convert_batch(
                files,
                output_dir=out_dir,
                css_path=css_path,
                header_footer=hf,
            )
            self._result_queue.put(("generate_done", results))

        threading.Thread(target=work, daemon=True).start()
        self.root.after(100, self._poll_queue)

    def _handle_generate_done(self, results):
        self.generate_button.config(state="normal")
        ok = [r for r in results if r["status"] == "ok"]
        failed = [r for r in results if r["status"] != "ok"]
        if failed:
            self.status_label.config(
                text=self._t("status_done_with_errors", ok=len(ok), failed=len(failed))
            )
            details = "\n".join(f"{r['input']}: {r['error']}" for r in failed)
            messagebox.showerror(self._t("error_title"), details)
        else:
            self.status_label.config(text=self._t("status_done", count=len(ok)))

    # All worker results are applied here on Tk's main thread.

    def _poll_queue(self):
        try:
            kind, payload = self._result_queue.get_nowait()
        except queue.Empty:
            self.root.after(100, self._poll_queue)
            return

        if kind == "preview_ok":
            self._apply_preview_image(payload)
        elif kind == "preview_error":
            self.status_label.config(text=self._t("status_preview_error", error=payload))
        elif kind == "generate_done":
            self._handle_generate_done(payload)


def launch() -> None:
    """Create the best available Tk root and run the desktop event loop."""
    root = TkinterDnD.Tk() if _HAS_DND else tk.Tk()
    LibreMarkPdfApp(root)
    root.mainloop()


if __name__ == "__main__":
    launch()
