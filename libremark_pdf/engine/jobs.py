"""Single-file and batch conversion orchestration."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable, Optional, Sequence, Union

from . import chromium, document
from .contracts import BatchPlan, ConversionError, HeaderFooterConfig, MAX_MARKDOWN_BYTES

_PathInput = Union[str, os.PathLike]
_error_code = None  # type: Optional[Callable[[BaseException], str]]


def configure_job_dependencies(error_code: Callable[[BaseException], str]) -> None:
    """Provide the stable public diagnostic-code helper from the facade."""
    global _error_code
    _error_code = error_code


def _diagnostic_code(exc: BaseException) -> str:
    if _error_code is None:
        raise RuntimeError("Conversion job dependencies have not been configured")
    return _error_code(exc)


def _path_key(path: _PathInput) -> str:
    candidate = Path(path)
    try:
        return str(candidate.resolve())
    except OSError:
        return str(candidate.absolute())


def convert_markdown_text_to_pdf(
    markdown_text: str,
    output_path: _PathInput,
    css_path: Optional[_PathInput] = None,
    header_footer: Optional[HeaderFooterConfig] = None,
    render_date: Optional[str] = None,
    trusted_html: bool = False,
    overwrite: bool = False,
    resource_root: Optional[_PathInput] = None,
    theme: Optional[str] = None,
    theme_root: Optional[_PathInput] = None,
    _renderer: Optional[chromium.BrowserRenderer] = None,
    _cancel_event: Optional[Any] = None,
) -> Path:
    """Convert Markdown text to a PDF and return its output path."""
    if _cancel_event is not None and _cancel_event.is_set():
        raise ConversionError("CANCELLED: conversion cancelled before preparation")
    output_path = Path(output_path)
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise ConversionError(
            "OUTPUT_UNAVAILABLE: cannot create destination directory: {0}".format(output_path.parent)
        ) from exc
    if output_path.exists() and not overwrite:
        raise ConversionError(f"OUTPUT_EXISTS: refusing to overwrite: {output_path}")

    hf = header_footer if header_footer is not None else HeaderFooterConfig()
    rendered_document = document.prepare_render_document(
        markdown_text,
        css_path=css_path,
        render_date=render_date,
        trusted_html=trusted_html,
        resource_root=resource_root,
        header_footer=hf,
        theme=theme,
        theme_root=theme_root,
    )
    if _cancel_event is not None and _cancel_event.is_set():
        raise ConversionError("CANCELLED: conversion cancelled before rendering")
    stage_callback = getattr(_renderer, "stage_callback", None)
    if stage_callback is not None:
        stage_callback("rendering")
    chromium.atomic_render_pdf(
        rendered_document.full_html,
        output_path,
        hf,
        rendered_document.render_date,
        renderer=_renderer,
        cancel_event=_cancel_event,
    )
    return output_path


def convert_markdown_to_pdf(
    input_path: _PathInput,
    output_path: Optional[_PathInput] = None,
    css_path: Optional[_PathInput] = None,
    header_footer: Optional[HeaderFooterConfig] = None,
    render_date: Optional[str] = None,
    trusted_html: bool = False,
    overwrite: bool = False,
    theme: Optional[str] = None,
    theme_root: Optional[_PathInput] = None,
    _renderer: Optional[chromium.BrowserRenderer] = None,
    _cancel_event: Optional[Any] = None,
) -> Path:
    """Convert one Markdown file, defaulting to a sibling `.pdf` output."""
    if _cancel_event is not None and _cancel_event.is_set():
        raise ConversionError("CANCELLED: conversion cancelled before reading input")
    input_path = Path(input_path)
    if not input_path.exists():
        raise ConversionError(f"INPUT_NOT_FOUND: input file not found: {input_path}")
    try:
        if input_path.stat().st_size > MAX_MARKDOWN_BYTES:
            raise ConversionError("INPUT_TOO_LARGE: Markdown exceeds configured size limit")
    except OSError as exc:
        raise ConversionError(f"INPUT_UNREADABLE: cannot inspect input: {input_path}") from exc
    try:
        markdown_text = input_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ConversionError("INVALID_UTF8: Markdown input must be UTF-8") from exc
    except OSError as exc:
        raise ConversionError(f"INPUT_UNREADABLE: cannot read input: {input_path}") from exc
    if _cancel_event is not None and _cancel_event.is_set():
        raise ConversionError("CANCELLED: conversion cancelled after reading input")
    resolved_output = Path(output_path) if output_path else input_path.with_suffix(".pdf")
    try:
        same_path = input_path.resolve() == resolved_output.resolve()
    except OSError:
        same_path = input_path.absolute() == resolved_output.absolute()
    if same_path:
        raise ConversionError("INPUT_OUTPUT_COLLISION: input and output paths are identical")
    return convert_markdown_text_to_pdf(
        markdown_text, resolved_output, css_path=css_path, header_footer=header_footer,
        render_date=render_date, trusted_html=trusted_html, overwrite=overwrite,
        resource_root=input_path.resolve().parent, theme=theme,
        theme_root=theme_root, _renderer=_renderer,
        _cancel_event=_cancel_event,
    )


def plan_batch_outputs(
    input_paths: Sequence[_PathInput],
    output_dir: Optional[_PathInput] = None,
    overwrite: bool = False,
    overwrite_targets: Optional[Sequence[_PathInput]] = None,
) -> list:
    """Preflight batch paths without launching a browser or writing output."""
    selected_overwrites = {
        _path_key(path) for path in (overwrite_targets or ())
    }
    provisional = []
    duplicate_targets = set()
    seen_targets = set()
    for raw_path in input_paths:
        input_path = Path(raw_path)
        target = Path(output_dir) / (input_path.stem + ".pdf") if output_dir else input_path.with_suffix(".pdf")
        key = _path_key(target)
        if key in seen_targets:
            duplicate_targets.add(key)
        seen_targets.add(key)
        provisional.append((input_path, target, key))
    plans = []
    for input_path, target, key in provisional:
        message = None
        if key in duplicate_targets:
            message = "DUPLICATE_OUTPUT: batch contains duplicate destinations"
        elif not input_path.exists():
            message = "INPUT_NOT_FOUND: input file not found: {0}".format(input_path)
        else:
            try:
                same_path = input_path.resolve() == target.resolve()
            except OSError:
                same_path = input_path.absolute() == target.absolute()
            if same_path:
                message = "INPUT_OUTPUT_COLLISION: input and output paths are identical"
            elif target.exists() and not (overwrite or key in selected_overwrites):
                message = "OUTPUT_EXISTS: refusing to overwrite: {0}".format(target)
        plans.append(BatchPlan(input_path, target, message))
    return plans


def convert_batch(
    input_paths: Sequence[_PathInput],
    output_dir: Optional[_PathInput] = None,
    css_path: Optional[_PathInput] = None,
    header_footer: Optional[HeaderFooterConfig] = None,
    render_date: Optional[str] = None,
    trusted_html: bool = False,
    overwrite: bool = False,
    theme: Optional[str] = None,
    theme_root: Optional[_PathInput] = None,
    cancel_event: Optional[Any] = None,
    progress_callback: Optional[Callable[[int, int, dict], None]] = None,
    cancel_current_event: Optional[Any] = None,
    stage_callback: Optional[Callable[[int, int, Path, str], None]] = None,
    overwrite_targets: Optional[Sequence[_PathInput]] = None,
) -> list[dict[str, Optional[str]]]:
    """Convert every input independently and return one result per input.

    ``overwrite_targets`` permits only the named batch destinations in addition
    to the all-or-nothing ``overwrite`` switch.
    """
    try:
        resolved_date = document.resolve_render_date(render_date)
        date_error = None
    except ConversionError as exc:
        resolved_date = render_date
        date_error = str(exc)
    selected_overwrites = {
        _path_key(path) for path in (overwrite_targets or ())
    }
    planned = plan_batch_outputs(
        input_paths, output_dir, overwrite, overwrite_targets
    )
    renderer = None
    renderer_manager = None
    renderer_error = None
    initially_cancelled = (
        (cancel_event is not None and cancel_event.is_set())
        or (cancel_current_event is not None and cancel_current_event.is_set())
    )
    last_stage = None

    def notify_stage(index: int, input_path: Path, stage: str) -> None:
        nonlocal last_stage
        marker = (index, stage)
        if marker == last_stage:
            return
        last_stage = marker
        if stage_callback is not None:
            try:
                stage_callback(index, len(planned), input_path, stage)
            except Exception:
                pass

    if not initially_cancelled and any(plan.error is None and date_error is None for plan in planned):
        first_renderable = next(
            plan for plan in planned if plan.error is None and date_error is None
        )
        notify_stage(planned.index(first_renderable) + 1, first_renderable.input_path, "preparing")
        try:
            renderer_manager = chromium.BrowserRenderer()
            renderer = renderer_manager.__enter__()
        except Exception as exc:
            renderer_error = exc
    results = []
    try:
        for index, plan in enumerate(planned, start=1):
            input_path = plan.input_path
            target = plan.output_path
            try:
                if (
                    (cancel_event is not None and cancel_event.is_set())
                    or (
                        cancel_current_event is not None
                        and cancel_current_event.is_set()
                    )
                ):
                    result = {"input": str(input_path), "output": None, "status": "cancelled", "error": "CANCELLED: conversion cancelled before this item", "error_code": "CANCELLED"}
                    results.append(result)
                    if progress_callback is not None:
                        try:
                            progress_callback(index, len(planned), result)
                        except Exception:
                            pass
                    continue
                if date_error is not None:
                    raise ConversionError(date_error)
                if plan.error is not None:
                    raise ConversionError(plan.error)
                if renderer_error is not None:
                    raise renderer_error
                notify_stage(index, input_path, "preparing")
                renderer.stage_callback = (
                    lambda stage, item=index, path=input_path:
                    notify_stage(item, path, stage)
                )
                item_overwrite = overwrite or _path_key(target) in selected_overwrites
                result_path = convert_markdown_to_pdf(input_path, target, css_path=css_path, header_footer=header_footer, render_date=resolved_date, trusted_html=trusted_html, overwrite=item_overwrite, theme=theme, theme_root=theme_root, _renderer=renderer, _cancel_event=cancel_current_event)
                result = {"input": str(input_path), "output": str(result_path), "status": "ok", "error": None, "error_code": None}
                results.append(result)
            except Exception as exc:
                code = _diagnostic_code(exc)
                status = "cancelled" if code == "CANCELLED" else "error"
                result = {"input": str(input_path), "output": None, "status": status, "error": str(exc), "error_code": code}
                results.append(result)
            if progress_callback is not None:
                try:
                    progress_callback(index, len(planned), result)
                except Exception:
                    pass
    finally:
        if renderer_manager is not None and renderer is not None:
            renderer_manager.__exit__(None, None, None)
    return results
