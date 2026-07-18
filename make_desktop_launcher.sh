#!/bin/bash
# make_desktop_launcher.sh — creates a LibreMarkPDF.desktop launcher pointing
# at the executable built by build.sh, and installs it for the current
# user so it appears in the applications menu and can be double-clicked
# from a file manager.
#
# Run this AFTER build.sh has completed successfully.

set -e
cd "$(dirname "$0")"

EXE_PATH="$(pwd)/dist/LibreMarkPDF/LibreMarkPDF"
ICON_PATH="$(pwd)/assets/libremark-pdf-logo-256.png"
DESKTOP_DIR="$HOME/.local/share/applications"
DESKTOP_FILE="$DESKTOP_DIR/libremark-pdf.desktop"

if [ ! -x "$EXE_PATH" ]; then
  echo "ERROR: $EXE_PATH not found or not executable."
  echo "Run ./build.sh first."
  exit 1
fi

mkdir -p "$DESKTOP_DIR"

cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Type=Application
Name=LibreMark PDF
Comment=Convert Markdown files to styled PDF documents
Exec="$EXE_PATH"
Icon=$ICON_PATH
Terminal=false
Categories=Office;Utility;
EOF

chmod +x "$DESKTOP_FILE"

# Also drop a copy on the Desktop folder if it exists, for a direct
# double-click shortcut (some file managers require "Allow launching"
# to be enabled once via right-click properties, for security reasons).
if [ -d "$HOME/Desktop" ]; then
  cp "$DESKTOP_FILE" "$HOME/Desktop/LibreMarkPDF.desktop"
  chmod +x "$HOME/Desktop/LibreMarkPDF.desktop"
fi

echo "Launcher installed: $DESKTOP_FILE"
echo "LibreMark PDF should now appear in your applications menu."
echo ""
echo "If double-clicking the Desktop icon doesn't work immediately, right-click"
echo "it and choose 'Allow Launching' (or 'Trust') — a one-time confirmation"
echo "required by most Linux file managers for new executables."
