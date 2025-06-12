.PHONY: build test package clean

build:
	poetry install
	# if macOS, build swift
	if [ "$(shell uname)" = "Darwin" ]; then \
		make build-swift; \
	fi

build-swift: aw_watcher_virtualdesktop/aw-watcher-virtualdesktop-macos

aw_watcher_virtualdesktop/aw-watcher-virtualdesktop-macos: aw_watcher_virtualdesktop/macos.swift
	swiftc $^ -o $@

test:
        aw-watcher-virtualdesktop --help

typecheck:
        poetry run mypy aw_watcher_virtualdesktop/ --ignore-missing-imports

package:
        pyinstaller aw-watcher-window.spec --clean --noconfirm

clean:
	rm -rf build dist
        rm -rf aw_watcher_virtualdesktop/__pycache__
        rm aw_watcher_virtualdesktop/aw-watcher-virtualdesktop-macos
