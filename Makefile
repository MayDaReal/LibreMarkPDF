# GNU Make is optional on Windows; bootstrap-windows.ps1 is the primary entry.
ifeq ($(OS),Windows_NT)
VERSION := $(shell type VERSION)
PYTHON ?= .venv-windows-py39\Scripts\python.exe
PLATFORM := windows-x64
BROWSER_DIR ?= $(CURDIR)/browser-win
else
VERSION := $(shell cat VERSION)
PYTHON ?= .venv-linux-py39/bin/python
PLATFORM := linux-x86_64
BROWSER_DIR ?= $(CURDIR)/browser-linux
endif
DIST_DIR ?= $(CURDIR)/dist/$(VERSION)/$(PLATFORM)

.PHONY: bootstrap test-pure test test-ui test-visual build-windows build-linux validate-windows validate-linux compare-platforms release-checklist clean-generated

bootstrap:
ifeq ($(OS),Windows_NT)
	powershell -NoProfile -ExecutionPolicy Bypass -File .\bootstrap-windows.ps1
else
	./bootstrap-linux.sh
endif

test-pure:
	$(PYTHON) tools/run_tests.py pure --browser-dir "$(BROWSER_DIR)"

test:
	$(PYTHON) tools/run_tests.py all --browser-dir "$(BROWSER_DIR)"

test-ui:
	$(PYTHON) tools/run_tests.py ui --browser-dir "$(BROWSER_DIR)"

test-visual:
	$(PYTHON) tools/run_tests.py visual --browser-dir "$(BROWSER_DIR)"

build-windows:
	cmd /c "set LIBREMARK_PDF_PYTHON=$(PYTHON)&& set LIBREMARK_PDF_DISTPATH=$(DIST_DIR)&& tools\build-windows-artifact.bat"

build-linux:
	LIBREMARK_PDF_PYTHON="$(PYTHON)" LIBREMARK_PDF_BROWSER_SOURCE="$(BROWSER_DIR)" LIBREMARK_PDF_DISTPATH="$(DIST_DIR)" ./tools/build-linux-artifact.sh

validate-windows:
	powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\validate-windows-artifact.ps1 -EvidenceRoot "$(DIST_DIR)" -Python "$(PYTHON)"

validate-linux:
	./tools/validate-linux-artifact.sh --evidence-root "$(DIST_DIR)" --python "$(PYTHON)" --browser-source "$(BROWSER_DIR)"

compare-platforms:
	@echo "Use the artifact comparison reports produced by validate-windows and validate-linux."

release-checklist:
	@echo "Complete the generated manual GUI checklist in the selected validation output."

clean-generated:
	@echo "Refusing automatic deletion. Remove only generated build, dist, browser, venv, and cache directories after review."
