# LibreMark PDF — G1 visual fixture

This representative document exercises the current theme without changing it.
It contains **bold text**, *emphasis*, [a local-only link](#table), and status
icons: ✅ ⚠️ 🟠 🔁 ⛔.

## Accents and scripts

English: The quick brown fox jumps over the lazy dog.

Français : À Noël, l’élève goûte un cœur d’artichaut — déjà prêt.

العربية: مرحبًا بالعالم — اختبار اتجاه الكتابة من اليمين إلى اليسار.

简体中文：本地文档转换与跨平台字体测试。

Emoji and symbols: 😀 🚀 ♥ ☀ ★ → ∑ ∞ ⌘ ⇪ ↯.

## Lists and code

1. First numbered item
2. Second numbered item
   - nested bullet
   - another bullet

```python
def stable_output(title: str) -> str:
    return f"PDF: {title}"
```

Inline code remains compact: `python -m libremark_pdf convert README.md`.

## Table

| Item | State | Description |
| --- | ---: | --- |
| Renderer | 1223 | Chromium is pinned by the G1 lock. |
| Network | 0 | External requests are denied. |
| Fonts | 6 | Candidate files cover Latin, Arabic, CJK, symbols, and emoji. |

## Long-form paragraph

LibreMark PDF keeps conversion local and deterministic. This paragraph is
repeated to exercise line wrapping, justification, punctuation, and page
transitions while retaining the approved stylesheet. Reliable output requires
the same Markdown interpretation, browser revision, resources, paper geometry,
and font files on every validated platform.

LibreMark PDF keeps conversion local and deterministic. This paragraph is
repeated to exercise line wrapping, justification, punctuation, and page
transitions while retaining the approved stylesheet. Reliable output requires
the same Markdown interpretation, browser revision, resources, paper geometry,
and font files on every validated platform.

LibreMark PDF keeps conversion local and deterministic. This paragraph is
repeated to exercise line wrapping, justification, punctuation, and page
transitions while retaining the approved stylesheet. Reliable output requires
the same Markdown interpretation, browser revision, resources, paper geometry,
and font files on every validated platform.

## Final section

The footer, page dimensions, extracted text, raster metrics, HTML fingerprint,
font hashes, and renderer revision are recorded by the G1 probe.
