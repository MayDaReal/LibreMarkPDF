"""Modern application header backed by reliable native menus."""

from __future__ import annotations

import os
import tkinter as tk
from typing import Callable, Dict, Optional, Tuple

import customtkinter as ctk

from ..components import FocusRing, IconButton
from ..theme import COLORS, RADII, SIZES, SPACING, SystemFontResolver


if os.name == "nt":
    WINDOW_CONTROL_GLYPHS = {
        "minimize": "\ue921",
        "maximize": "\ue922",
        "restore": "\ue923",
        "close": "\ue8bb",
    }
    WINDOW_CONTROL_FONT = ("Segoe MDL2 Assets", 10)
else:
    WINDOW_CONTROL_GLYPHS = {
        "minimize": "−",
        "maximize": "□",
        "restore": "❐",
        "close": "×",
    }
    WINDOW_CONTROL_FONT = ("TkDefaultFont", 12)


class MenuAction:
    """Expose a native menu command through stable UI automation."""

    def __init__(self, command: Callable[[], None]) -> None:
        self.command = command
        self.accessible_name = ""

    def invoke(self) -> None:
        """Invoke the same command as the corresponding native menu entry."""
        self.command()


class WindowChrome:
    """Provide controls, dragging, and resizing for a borderless root."""

    _RESIZE_BORDER = SIZES["window_resize_border"]
    _RESIZE_CORNER = 10
    _RESIZE_FRAME_MS = 16

    def __init__(self, root: tk.Misc) -> None:
        self.root = root
        self.maximize_button = None
        self._normal_geometry = None  # type: Optional[Tuple[int, int, int, int]]
        self._drag_origin = None  # type: Optional[Tuple[int, int]]
        self._maximized_drag_ratio = None  # type: Optional[float]
        self._resize_origin = None
        self._pending_resize_geometry = None
        self._resize_after_id = None  # type: Optional[str]
        self._maximized = False
        self._restore_override_after_map = False
        self._taskbar_registered = False
        self._resize_surfaces = []
        self.root.bind("<Map>", self._on_root_map, add="+")
        self._create_resize_surfaces()
        self.root.after_idle(self._enable_custom_chrome)

    def attach_maximize_button(self, button: ctk.CTkButton) -> None:
        """Retain the control whose glyph reflects maximize state."""
        self.maximize_button = button

    def bind_drag_surface(self, widget: tk.Misc) -> None:
        """Make a non-interactive title-bar surface draggable."""
        widget.bind("<ButtonPress-1>", self._start_drag, add="+")
        widget.bind("<B1-Motion>", self._drag, add="+")
        widget.bind("<ButtonRelease-1>", self._stop_drag, add="+")
        widget.bind("<Double-Button-1>", self.toggle_maximize, add="+")

    def _enable_custom_chrome(self) -> None:
        self.root.overrideredirect(True)
        self._configure_windows_taskbar()
        self._raise_resize_surfaces()

    def _window_handle(self) -> Optional[int]:
        if os.name == "nt":
            try:
                import ctypes
                from ctypes import wintypes

                get_parent = ctypes.windll.user32.GetParent
                get_parent.argtypes = (wintypes.HWND,)
                get_parent.restype = wintypes.HWND
                child = int(self.root.winfo_id())
                return int(get_parent(child) or child)
            except (
                AttributeError,
                OSError,
                TypeError,
                ValueError,
                ctypes.ArgumentError,
                tk.TclError,
            ):
                pass
        try:
            return int(str(self.root.frame()), 0)
        except (AttributeError, TypeError, ValueError, tk.TclError):
            try:
                return int(self.root.winfo_id())
            except (AttributeError, TypeError, ValueError, tk.TclError):
                return None

    def _configure_windows_taskbar(self) -> None:
        if os.name != "nt":
            return
        handle = self._window_handle()
        if handle is None:
            return
        try:
            import ctypes
            from ctypes import wintypes

            user32 = ctypes.windll.user32
            get_window_long = user32.GetWindowLongW
            get_window_long.argtypes = (wintypes.HWND, ctypes.c_int)
            get_window_long.restype = ctypes.c_long
            set_window_long = user32.SetWindowLongW
            set_window_long.argtypes = (
                wintypes.HWND,
                ctypes.c_int,
                ctypes.c_long,
            )
            set_window_long.restype = ctypes.c_long
            set_window_position = user32.SetWindowPos
            set_window_position.argtypes = (
                wintypes.HWND,
                wintypes.HWND,
                ctypes.c_int,
                ctypes.c_int,
                ctypes.c_int,
                ctypes.c_int,
                wintypes.UINT,
            )
            set_window_position.restype = wintypes.BOOL
            extended_style = get_window_long(handle, -20)
            extended_style &= ~0x00000080  # WS_EX_TOOLWINDOW
            extended_style |= 0x00040000  # WS_EX_APPWINDOW
            set_window_long(handle, -20, extended_style)
            set_window_position(
                handle,
                0,
                0,
                0,
                0,
                0,
                0x0001 | 0x0002 | 0x0004 | 0x0010 | 0x0020,
            )
            self._schedule_windows_taskbar_refresh()
        except (AttributeError, OSError, ctypes.ArgumentError):
            return

    def _schedule_windows_taskbar_refresh(self) -> None:
        if self._taskbar_registered:
            return
        self._taskbar_registered = True
        self.root.withdraw()
        self.root.after(10, self._restore_windows_taskbar_window)

    def _restore_windows_taskbar_window(self) -> None:
        try:
            self.root.deiconify()
            self._raise_resize_surfaces()
            self.root.after_idle(self._configure_windows_taskbar)
        except tk.TclError:
            return

    def _create_resize_surfaces(self) -> None:
        border = self._RESIZE_BORDER
        corner = self._RESIZE_CORNER
        surface_specs = (
            (
                "n",
                "size_ns",
                {
                    "x": corner,
                    "y": 0,
                    "relwidth": 1,
                    "width": -2 * corner,
                    "height": border,
                },
            ),
            (
                "s",
                "size_ns",
                {
                    "x": corner,
                    "rely": 1,
                    "y": -border,
                    "relwidth": 1,
                    "width": -2 * corner,
                    "height": border,
                },
            ),
            (
                "w",
                "size_we",
                {
                    "x": 0,
                    "y": corner,
                    "width": border,
                    "relheight": 1,
                    "height": -2 * corner,
                },
            ),
            (
                "e",
                "size_we",
                {
                    "relx": 1,
                    "x": -border,
                    "y": corner,
                    "width": border,
                    "relheight": 1,
                    "height": -2 * corner,
                },
            ),
            (
                "nw",
                "size_nw_se",
                {"x": 0, "y": 0, "width": corner, "height": border},
            ),
            (
                "nw",
                "size_nw_se",
                {
                    "x": 0,
                    "y": border,
                    "width": border,
                    "height": corner - border,
                },
            ),
            (
                "ne",
                "size_ne_sw",
                {
                    "relx": 1,
                    "x": -corner,
                    "y": 0,
                    "width": corner,
                    "height": border,
                },
            ),
            (
                "ne",
                "size_ne_sw",
                {
                    "relx": 1,
                    "x": -border,
                    "y": border,
                    "width": border,
                    "height": corner - border,
                },
            ),
            (
                "sw",
                "size_ne_sw",
                {
                    "x": 0,
                    "rely": 1,
                    "y": -border,
                    "width": corner,
                    "height": border,
                },
            ),
            (
                "sw",
                "size_ne_sw",
                {
                    "x": 0,
                    "rely": 1,
                    "y": -corner,
                    "width": border,
                    "height": corner - border,
                },
            ),
            (
                "se",
                "size_nw_se",
                {
                    "relx": 1,
                    "rely": 1,
                    "x": -corner,
                    "y": -border,
                    "width": corner,
                    "height": border,
                },
            ),
            (
                "se",
                "size_nw_se",
                {
                    "relx": 1,
                    "rely": 1,
                    "x": -border,
                    "y": -corner,
                    "width": border,
                    "height": corner - border,
                },
            ),
        )
        for edge, cursor, placement in surface_specs:
            surface = tk.Frame(
                self.root,
                background=COLORS["app_bg"],
                borderwidth=0,
                cursor=cursor,
                takefocus=False,
            )
            surface.place(**placement)
            surface.bind(
                "<ButtonPress-1>",
                lambda event, active_edge=edge: self._start_resize(
                    event,
                    active_edge,
                ),
            )
            surface.bind("<B1-Motion>", self._resize)
            surface.bind("<ButtonRelease-1>", self._stop_resize)
            self._resize_surfaces.append(surface)

    def _raise_resize_surfaces(self) -> None:
        for surface in self._resize_surfaces:
            surface.lift()

    def _start_resize(self, event, edge: str):
        if self._maximized:
            return "break"
        self.root.update_idletasks()
        self._resize_origin = (
            edge,
            event.x_root,
            event.y_root,
            self.root.winfo_width(),
            self.root.winfo_height(),
            self.root.winfo_x(),
            self.root.winfo_y(),
        )
        return "break"

    def _resize(self, event):
        if self._resize_origin is None:
            return "break"
        edge, pointer_x, pointer_y, width, height, x, y = self._resize_origin
        delta_x = event.x_root - pointer_x
        delta_y = event.y_root - pointer_y
        minimum_width, minimum_height = self.root.minsize()

        if "w" in edge:
            resized_width = max(minimum_width, width - delta_x)
            x += width - resized_width
            width = resized_width
        elif "e" in edge:
            width = max(minimum_width, width + delta_x)

        if "n" in edge:
            resized_height = max(minimum_height, height - delta_y)
            y += height - resized_height
            height = resized_height
        elif "s" in edge:
            height = max(minimum_height, height + delta_y)

        self._pending_resize_geometry = (width, height, x, y)
        self._resize_origin = (
            edge,
            event.x_root,
            event.y_root,
            width,
            height,
            x,
            y,
        )
        if self._resize_after_id is None:
            self._resize_after_id = self.root.after(
                self._RESIZE_FRAME_MS,
                self._apply_pending_resize,
            )
        return "break"

    def _stop_resize(self, _event=None):
        if self._resize_after_id is not None:
            try:
                self.root.after_cancel(self._resize_after_id)
            except tk.TclError:
                pass
            self._resize_after_id = None
        self._apply_pending_resize()
        self._resize_origin = None
        return "break"

    def _apply_pending_resize(self) -> None:
        self._resize_after_id = None
        geometry = self._pending_resize_geometry
        self._pending_resize_geometry = None
        if geometry is None:
            return
        width, height, x, y = geometry
        self._set_window_rectangle(width, height, x, y)

    def _set_window_rectangle(
        self,
        width: int,
        height: int,
        x: int,
        y: int,
    ) -> None:
        if self._move_window_on_windows(width, height, x, y):
            return
        self.root.geometry(
            "{0}x{1}{2:+d}{3:+d}".format(width, height, x, y)
        )

    def _move_window_on_windows(
        self,
        width: int,
        height: int,
        x: int,
        y: int,
    ) -> bool:
        if os.name != "nt":
            return False
        handle = self._window_handle()
        if handle is None:
            return False
        try:
            import ctypes
            from ctypes import wintypes

            move_window = ctypes.windll.user32.MoveWindow
            move_window.argtypes = (
                wintypes.HWND,
                ctypes.c_int,
                ctypes.c_int,
                ctypes.c_int,
                ctypes.c_int,
                wintypes.BOOL,
            )
            move_window.restype = wintypes.BOOL
            return bool(move_window(handle, x, y, width, height, True))
        except (AttributeError, OSError, ctypes.ArgumentError):
            return False

    def minimize(self) -> None:
        """Minimize while retaining a taskbar-restorable root."""
        self._restore_override_after_map = True
        self.root.overrideredirect(False)
        self.root.iconify()

    def _on_root_map(self, _event=None) -> None:
        if not self._restore_override_after_map:
            return
        if self.root.state() == "normal":
            self._restore_override_after_map = False
            self.root.after_idle(self._enable_custom_chrome)

    def toggle_maximize(self, _event=None):
        """Maximize to the available work area or restore prior geometry."""
        if self._maximized:
            self.restore()
        else:
            self.maximize()
        return "break"

    def maximize(self) -> None:
        """Fill the desktop work area without covering the Windows taskbar."""
        self.root.update_idletasks()
        self._maximized_drag_ratio = None
        self._normal_geometry = (
            self.root.winfo_width(),
            self.root.winfo_height(),
            self.root.winfo_x(),
            self.root.winfo_y(),
        )
        x, y, width, height = self._work_area()
        self._set_window_rectangle(width, height, x, y)
        self._maximized = True
        self._update_maximize_glyph()

    def restore(self) -> None:
        """Restore the last normal window rectangle."""
        self._maximized_drag_ratio = None
        if self._normal_geometry is not None:
            width, height, x, y = self._normal_geometry
            self._set_window_rectangle(width, height, x, y)
        self._maximized = False
        self._update_maximize_glyph()

    def close(self) -> None:
        """Route closure through the existing application protocol."""
        self.root.event_generate("<<CustomTitlebarClose>>")

    def _start_drag(self, event) -> None:
        if self._maximized:
            local_pointer_x = event.x_root - self.root.winfo_x()
            self._maximized_drag_ratio = max(
                0.0,
                min(
                    1.0,
                    local_pointer_x / max(1, self.root.winfo_width()),
                ),
            )
            self._drag_origin = None
            return
        self._maximized_drag_ratio = None
        self._drag_origin = (
            event.x_root - self.root.winfo_x(),
            event.y_root - self.root.winfo_y(),
        )

    def _drag(self, event) -> None:
        if self._maximized and self._maximized_drag_ratio is not None:
            pointer_ratio = self._maximized_drag_ratio
            normal_geometry = self._normal_geometry
            _work_x, work_y, _work_width, _work_height = self._work_area()
            self.restore()
            if normal_geometry is None:
                return
            width, height, _normal_x, _normal_y = normal_geometry
            x = int(event.x_root - width * pointer_ratio)
            y = max(work_y, event.y_root - SIZES["header"] // 2)
            self._set_window_rectangle(width, height, x, y)
            self._drag_origin = (event.x_root - x, event.y_root - y)
            return
        if self._drag_origin is None:
            return
        offset_x, offset_y = self._drag_origin
        self._set_window_rectangle(
            self.root.winfo_width(),
            self.root.winfo_height(),
            event.x_root - offset_x,
            event.y_root - offset_y,
        )

    def _stop_drag(self, _event=None) -> None:
        self._drag_origin = None
        self._maximized_drag_ratio = None

    def _update_maximize_glyph(self) -> None:
        if self.maximize_button is not None:
            self.maximize_button.configure(
                text=(
                    WINDOW_CONTROL_GLYPHS["restore"]
                    if self._maximized
                    else WINDOW_CONTROL_GLYPHS["maximize"]
                )
            )

    def _work_area(self) -> Tuple[int, int, int, int]:
        if os.name == "nt":
            try:
                import ctypes
                from ctypes import wintypes

                class MonitorInfo(ctypes.Structure):
                    _fields_ = (
                        ("cbSize", wintypes.DWORD),
                        ("rcMonitor", wintypes.RECT),
                        ("rcWork", wintypes.RECT),
                        ("dwFlags", wintypes.DWORD),
                    )

                handle = self._window_handle()
                monitor_from_window = (
                    ctypes.windll.user32.MonitorFromWindow
                )
                monitor_from_window.argtypes = (
                    wintypes.HWND,
                    wintypes.DWORD,
                )
                monitor_from_window.restype = wintypes.HANDLE
                get_monitor_info = ctypes.windll.user32.GetMonitorInfoW
                get_monitor_info.argtypes = (
                    wintypes.HANDLE,
                    ctypes.POINTER(MonitorInfo),
                )
                get_monitor_info.restype = wintypes.BOOL
                monitor = monitor_from_window(
                    handle or 0,
                    2,
                )
                information = MonitorInfo()
                information.cbSize = ctypes.sizeof(MonitorInfo)
                if monitor and get_monitor_info(
                    monitor,
                    ctypes.byref(information),
                ):
                    rectangle = information.rcWork
                    return (
                        rectangle.left,
                        rectangle.top,
                        rectangle.right - rectangle.left,
                        rectangle.bottom - rectangle.top,
                    )
            except (AttributeError, OSError, ctypes.ArgumentError):
                pass
        return (
            0,
            0,
            self.root.winfo_screenwidth(),
            self.root.winfo_screenheight(),
        )


class AppHeader(ctk.CTkFrame):
    """Display product identity, Help, and immediate language selection."""

    def __init__(
        self,
        master,
        root: tk.Misc,
        logo,
        version: str,
        language: str,
        fonts: SystemFontResolver,
        on_shortcuts: Callable[[], None],
        on_manual: Callable[[], None],
        on_report: Callable[[], None],
        on_about: Callable[[], None],
        on_language: Callable[[str], None],
        compact_menu_icon=None,
    ) -> None:
        super().__init__(
            master,
            height=SIZES["header"],
            corner_radius=0,
            fg_color=COLORS["surface"],
            border_color=COLORS["border"],
            border_width=1,
        )
        self.grid_columnconfigure(2, weight=1)
        self.grid_propagate(False)
        self.window_chrome = WindowChrome(root)
        self._language = language
        self._on_language = on_language
        self._language_var = tk.StringVar(master=root, value=language)

        self.logo_label = ctk.CTkLabel(self, text="", image=logo, width=32)
        self.logo_label.grid(
            row=0,
            column=0,
            padx=(SPACING["lg"], SPACING["sm"]),
            pady=SPACING["md"],
        )
        self.product_label = ctk.CTkLabel(
            self,
            text="LibreMark PDF",
            font=fonts.font("product"),
            text_color=COLORS["text"],
            anchor="w",
        )
        self.product_label.grid(row=0, column=1, sticky="w")

        self.version_button = ctk.CTkButton(
            self,
            text="v{0}".format(version),
            command=on_about,
            width=96,
            height=28,
            corner_radius=RADII["pill"],
            fg_color=COLORS["surface_subtle"],
            hover_color=COLORS["surface_hover"],
            border_color=COLORS["border"],
            border_width=1,
            text_color=COLORS["text_secondary"],
            font=fonts.font("secondary"),
        )
        tk.Frame.configure(self.version_button, takefocus=True)
        self.version_focus = FocusRing(
            self.version_button,
            normal_color=COLORS["border"],
            normal_width=1,
            focus_color=COLORS["primary"],
        )
        self.version_button.grid(
            row=0,
            column=2,
            sticky="w",
            padx=(SPACING["md"], 0),
        )
        self.version_button.bind(
            "<Return>",
            lambda _event: self.version_button.invoke(),
            add="+",
        )
        self.version_button.bind(
            "<space>",
            lambda _event: self.version_button.invoke(),
            add="+",
        )

        self.help_menu = tk.Menu(root, tearoff=False)
        self.help_menu.add_command(command=on_shortcuts)
        self.help_menu.add_command(command=on_manual)
        self.help_menu.add_command(command=on_report)
        self.help_menu.add_separator()
        self.help_menu.add_command(command=on_about)
        self.help_button = self._menu_button(
            text="",
            command=lambda: self._post_menu(self.help_button, self.help_menu),
            fonts=fonts,
            width=68,
        )
        self.help_button.grid(
            row=0,
            column=3,
            padx=(0, 0),
            pady=SPACING["sm"],
        )

        self.language_menu = tk.Menu(root, tearoff=False)
        self.language_menu.add_radiobutton(
            label="Français",
            value="fr",
            variable=self._language_var,
            command=lambda: on_language("fr"),
        )
        self.language_menu.add_radiobutton(
            label="English",
            value="en",
            variable=self._language_var,
            command=lambda: on_language("en"),
        )
        self.language_button = self._menu_button(
            text="",
            command=lambda: self._post_menu(
                self.language_button,
                self.language_menu,
            ),
            fonts=fonts,
            width=88,
        )
        self.language_button.grid(
            row=0,
            column=4,
            padx=(0, SPACING["xs"]),
            pady=SPACING["sm"],
        )
        self.compact_menu = tk.Menu(root, tearoff=False)
        self.compact_menu.add_command(command=on_manual)
        self.compact_menu.add_command(command=on_shortcuts)
        self.compact_menu.add_cascade(menu=self.language_menu)
        self.compact_menu.add_command(command=on_report)
        self.compact_menu.add_separator()
        self.compact_menu.add_command(command=on_about)
        self.compact_menu.add_command(command=on_about)
        self.compact_menu_button = IconButton(
            self,
            image=compact_menu_icon,
            accessible_name="",
            command=lambda: self._post_menu(
                self.compact_menu_button,
                self.compact_menu,
            ),
            width=36,
            height=36,
        )
        self.compact_menu_button.grid(
            row=0,
            column=2,
            sticky="w",
            padx=(SPACING["xs"], 0),
            pady=SPACING["sm"],
        )
        self.compact_menu_button.grid_remove()
        self.minimize_button = self._window_button(
            text=WINDOW_CONTROL_GLYPHS["minimize"],
            command=self.window_chrome.minimize,
        )
        self.minimize_button.grid(
            row=0,
            column=5,
            padx=(0, SPACING["xs"]),
            pady=SPACING["sm"],
        )
        self.maximize_button = self._window_button(
            text=WINDOW_CONTROL_GLYPHS["maximize"],
            command=self.window_chrome.toggle_maximize,
        )
        self.maximize_button.grid(
            row=0,
            column=6,
            padx=(0, SPACING["xs"]),
            pady=SPACING["sm"],
        )
        self.window_chrome.attach_maximize_button(self.maximize_button)
        self.close_button = self._window_button(
            text=WINDOW_CONTROL_GLYPHS["close"],
            command=self.window_chrome.close,
            close=True,
        )
        self.close_button.grid(
            row=0,
            column=7,
            padx=(0, SPACING["sm"]),
            pady=SPACING["sm"],
        )
        for drag_surface in (self, self.logo_label, self.product_label):
            self.window_chrome.bind_drag_surface(drag_surface)
        self.language_actions = {
            "en": MenuAction(lambda: on_language("en")),
            "fr": MenuAction(lambda: on_language("fr")),
        }  # type: Dict[str, MenuAction]

    def _menu_button(
        self,
        text: str,
        command: Callable[[], None],
        fonts: SystemFontResolver,
        width: int,
    ) -> ctk.CTkButton:
        button = ctk.CTkButton(
            self,
            text=text,
            command=command,
            width=width,
            height=36,
            corner_radius=RADII["control"],
            fg_color="transparent",
            hover_color=COLORS["surface_hover"],
            border_color=COLORS["surface"],
            border_width=1,
            text_color=COLORS["text"],
            font=fonts.font("body"),
        )
        tk.Frame.configure(button, takefocus=True)
        FocusRing(
            button,
            normal_color=COLORS["surface"],
            normal_width=1,
            focus_color=COLORS["primary"],
        )
        button.bind("<Return>", lambda _event: button.invoke(), add="+")
        button.bind("<space>", lambda _event: button.invoke(), add="+")
        button.bind("<Down>", lambda _event: button.invoke(), add="+")
        return button

    def _window_button(
        self,
        text: str,
        command: Callable[[], None],
        close: bool = False,
    ) -> ctk.CTkButton:
        button = ctk.CTkButton(
            self,
            text=text,
            command=command,
            width=36,
            height=36,
            corner_radius=RADII["control"],
            fg_color="transparent",
            hover_color=COLORS["surface_hover"],
            hover=not close,
            border_width=0,
            text_color=COLORS["text"],
            font=WINDOW_CONTROL_FONT,
        )
        tk.Frame.configure(button, takefocus=True)
        button.bind("<Return>", lambda _event: button.invoke(), add="+")
        button.bind("<space>", lambda _event: button.invoke(), add="+")
        if close:
            button.bind(
                "<Enter>",
                lambda _event: button.configure(
                    fg_color="#C42B1C",
                    text_color="#FFFFFF",
                ),
                add="+",
            )
            button.bind(
                "<Leave>",
                lambda _event: button.configure(
                    fg_color="transparent",
                    text_color=COLORS["text"],
                ),
                add="+",
            )
        return button

    def _post_menu(self, button: ctk.CTkButton, menu: tk.Menu) -> None:
        tooltip = getattr(button, "tooltip", None)
        if tooltip is not None:
            tooltip.hide()
        menu.update_idletasks()
        work_x, work_y, work_width, work_height = (
            self.window_chrome._work_area()
        )
        menu_width = max(220, menu.winfo_reqwidth())
        menu_height = max(120, menu.winfo_reqheight())
        desired_x = button.winfo_rootx()
        desired_y = button.winfo_rooty() + button.winfo_height()
        x = max(work_x, min(desired_x, work_x + work_width - menu_width))
        y = max(work_y, min(desired_y, work_y + work_height - menu_height))
        try:
            menu.tk_popup(x, y)
        finally:
            menu.grab_release()

    def retranslate(self, labels: dict, version: str, language: str) -> None:
        """Refresh visible copy and native menus without rebuilding controls."""
        self._language = language
        self._language_var.set(language)
        self.product_label.configure(text=labels["app_title"])
        self.version_button.configure(
            text=labels["app_version_compact"].format(version=version)
        )
        self.help_button.configure(text="{0} ▾".format(labels["help_menu"]))
        language_name = "Français" if language == "fr" else "English"
        self.language_button.configure(text="{0} ▾".format(language_name))
        self.help_menu.entryconfigure(
            0,
            label=labels["keyboard_shortcuts_action"],
        )
        self.help_menu.entryconfigure(1, label=labels["manual_action"])
        self.help_menu.entryconfigure(2, label=labels["report_issue_action"])
        self.help_menu.entryconfigure(4, label=labels["about_action"])
        self.compact_menu.entryconfigure(0, label=labels["manual_action"])
        self.compact_menu.entryconfigure(
            1,
            label=labels["keyboard_shortcuts_action"],
        )
        self.compact_menu.entryconfigure(
            2,
            label=labels.get("language_menu", "Language"),
        )
        self.compact_menu.entryconfigure(3, label=labels["report_issue_action"])
        self.compact_menu.entryconfigure(5, label=labels["about_action"])
        self.compact_menu.entryconfigure(
            6,
            label=labels.get(
                "version_information", "Version {version}"
            ).format(version=version),
        )
        self.compact_menu_button.update_accessible_name(
            labels.get("compact_menu_a11y", "Application menu")
        )

    @property
    def active_language(self) -> str:
        """Return the language currently checked in the native menu."""
        return self._language_var.get()

    def set_layout_mode(self, mode: str) -> None:
        """Use compact header spacing without activating compact navigation."""
        if mode == "compact":
            self.version_button.grid_remove()
            self.help_button.grid_remove()
            self.language_button.grid_remove()
            self.compact_menu_button.grid()
            self.logo_label.grid_configure(padx=(SPACING["md"], SPACING["sm"]))
        else:
            self.compact_menu_button.grid_remove()
            self.version_button.grid()
            self.help_button.grid()
            self.language_button.grid()
            self.logo_label.grid_configure(padx=(SPACING["lg"], SPACING["sm"]))
            self.language_button.grid_configure(
                padx=(0, SPACING["xs"])
            )
