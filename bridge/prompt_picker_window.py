#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")

from gi.repository import Gdk, GLib, Gtk  # noqa: E402


WINDOW_WIDTH = 520
WINDOW_HEIGHT = 260
WINDOW_OFFSET_Y = 0
WINDOW_MARGIN = 16


def _hyprctl_json(*args: str):
    try:
        proc = subprocess.run(
            ["hyprctl", *args, "-j"],
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(proc.stdout)
    except Exception:
        return None


def _hyprctl_text(*args: str) -> str | None:
    try:
        proc = subprocess.run(
            ["hyprctl", *args],
            capture_output=True,
            text=True,
            check=True,
        )
        return proc.stdout.strip()
    except Exception:
        return None


def hypr_client_for_pid(pid: int, title: str) -> dict | None:
    clients = _hyprctl_json("clients") or []
    for client in clients:
        if client.get("pid") != pid:
            continue
        if client.get("title") == title or client.get("initialTitle") == title:
            return client
    return None


class PromptPickerApp(Gtk.Application):
    def __init__(self, input_path: Path, result_path: Path):
        super().__init__(application_id="org.klor.PromptPicker")
        self.input_path = input_path
        self.result_path = result_path
        self.rows = [line.rstrip("\n") for line in input_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        self.filtered_rows = list(self.rows)
        self.selected_index = 0
        self.window_pid = os.getpid()
        self.window: Gtk.ApplicationWindow | None = None
        self.listbox: Gtk.ListBox | None = None
        self.entry: Gtk.Entry | None = None
        self._result_written = False
        self.test_query = os.environ.get("KLOR_PICKER_TEST_QUERY", "").strip().lower()
        self.test_accept_delay_ms = int(os.environ.get("KLOR_PICKER_TEST_ACCEPT_MS", "0") or "0")

    def do_activate(self) -> None:  # type: ignore[override]
        window = Gtk.ApplicationWindow(application=self)
        self.window = window
        window.set_title("Prompt snippets")
        window.set_modal(False)
        window.set_decorated(False)
        window.set_resizable(False)
        window.set_default_size(WINDOW_WIDTH, WINDOW_HEIGHT)
        window.set_hide_on_close(False)
        window.connect("close-request", self._on_close_request)
        window.set_visible(False)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        root.set_margin_top(12)
        root.set_margin_bottom(12)
        root.set_margin_start(12)
        root.set_margin_end(12)
        root.add_css_class("prompt-picker-root")

        entry = Gtk.Entry()
        self.entry = entry
        entry.set_placeholder_text("Type to filter prompts...")
        entry.connect("changed", self._on_search_changed)
        entry.connect("activate", self._on_activate)
        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self._on_key_pressed)
        entry.add_controller(key_controller)
        root.append(entry)

        scroller = Gtk.ScrolledWindow()
        scroller.set_hexpand(True)
        scroller.set_vexpand(True)
        scroller.set_min_content_height(5 * 36)

        listbox = Gtk.ListBox()
        self.listbox = listbox
        listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        listbox.connect("row-activated", self._on_row_activated)
        scroller.set_child(listbox)
        root.append(scroller)

        window.set_child(root)
        self._install_css()
        self._rebuild_list()
        window.present()
        GLib.idle_add(self._show_window)
        self._focus_entry()
        GLib.idle_add(self._focus_entry)
        GLib.timeout_add(120, self._focus_entry)
        if self.test_query:
            GLib.timeout_add(120, self._apply_test_query)
        GLib.timeout_add_seconds(20, self._timeout_close)

    def _install_css(self) -> None:
        css = b"""
        window {
          background: rgba(22, 22, 25, 0.96);
          color: #f3f4f6;
          border: 1px solid rgba(255, 255, 255, 0.08);
          border-radius: 12px;
          box-shadow: 0 18px 50px rgba(0, 0, 0, 0.35);
        }
        entry {
          min-height: 34px;
          font-size: 15px;
          padding: 8px 10px;
          border-radius: 8px;
          border: none;
          background: rgba(255, 255, 255, 0.06);
          color: #f3f4f6;
        }
        scrolledwindow {
          background: transparent;
        }
        list {
          background: transparent;
        }
        list row {
          min-height: 36px;
          padding: 8px 10px;
          border-radius: 8px;
          font-size: 14px;
          color: #f3f4f6;
        }
        list row:selected {
          background: rgba(110, 168, 254, 0.22);
        }
        label {
          color: #f3f4f6;
        }
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        display = Gdk.Display.get_default()
        if display is not None:
            Gtk.StyleContext.add_provider_for_display(display, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def _focus_entry(self) -> bool:
        if self.window is not None and self.entry is not None:
            self.window.set_focus(self.entry)
        if self.entry is not None:
            self.entry.grab_focus()
            self.entry.set_position(-1)
        if self.listbox is not None:
            row = self.listbox.get_selected_row()
            if row is not None:
                self.listbox.select_row(row)
        return False

    def _apply_test_query(self) -> bool:
        if self.entry is None:
            return False
        self.entry.set_text(self.test_query)
        self.entry.set_position(-1)
        if self.test_accept_delay_ms > 0:
            GLib.timeout_add(self.test_accept_delay_ms, self._accept_test_selection)
        return False

    def _accept_test_selection(self) -> bool:
        self._accept_selection()
        return False

    def _show_window(self) -> bool:
        if self.window is None:
            return False
        self.window.set_visible(True)
        return False

    def _on_key_pressed(
        self,
        _controller: Gtk.EventControllerKey,
        keyval: int,
        _keycode: int,
        _state: Gdk.ModifierType,
    ) -> bool:
        if keyval == Gdk.KEY_Down:
            self._move_selection(1)
            return True
        if keyval == Gdk.KEY_Up:
            self._move_selection(-1)
            return True
        if keyval == Gdk.KEY_Escape:
            self._clear_result()
            self.quit()
            return True
        return False

    def _move_selection(self, delta: int) -> None:
        if not self.filtered_rows or self.listbox is None:
            return
        self.selected_index = max(0, min(self.selected_index + delta, len(self.filtered_rows) - 1))
        row = self.listbox.get_row_at_index(self.selected_index)
        if row is not None:
            self.listbox.select_row(row)

    def _on_search_changed(self, entry: Gtk.Entry) -> None:
        query = entry.get_text().strip().lower()
        if not query:
            self.filtered_rows = list(self.rows)
        else:
            self.filtered_rows = [row for row in self.rows if query in row.lower()]
        self.selected_index = 0
        self._rebuild_list()

    def _clear_result(self) -> None:
        self._write_result(1, "", "cancelled")

    def _timeout_close(self) -> bool:
        if not self.result_path.exists():
            self._write_result(1, "", "timeout")
        self.quit()
        return False

    def _write_result(self, returncode: int, stdout: str, stderr: str) -> None:
        if self._result_written:
            return
        self.result_path.write_text(
            json.dumps({"returncode": returncode, "stdout": stdout, "stderr": stderr}),
            encoding="utf-8",
        )
        self._result_written = True

    def _accept_selection(self) -> None:
        if not self.filtered_rows:
            self._clear_result()
        else:
            selected = self.filtered_rows[self.selected_index]
            self._write_result(0, selected, "")
        self.quit()

    def _on_activate(self, _entry: Gtk.Entry) -> None:
        self._accept_selection()

    def _on_row_activated(self, _listbox: Gtk.ListBox, row: Gtk.ListBoxRow) -> None:
        self.selected_index = row.get_index()
        self._accept_selection()

    def _on_close_request(self, *_args) -> bool:
        self._clear_result()
        return False

    def _rebuild_list(self) -> None:
        if self.listbox is None:
            return
        while True:
            row = self.listbox.get_row_at_index(0)
            if row is None:
                break
            self.listbox.remove(row)

        for text in self.filtered_rows:
            row = Gtk.ListBoxRow()
            label = Gtk.Label(label=text)
            label.set_xalign(0.0)
            label.set_wrap(False)
            label.set_ellipsize(3)
            row.set_child(label)
            self.listbox.append(row)

        if self.filtered_rows:
            self.selected_index = max(0, min(self.selected_index, len(self.filtered_rows) - 1))
            row = self.listbox.get_row_at_index(self.selected_index)
            if row is not None:
                self.listbox.select_row(row)


def main() -> int:
    if len(sys.argv) != 3:
        return 2
    app = PromptPickerApp(Path(sys.argv[1]), Path(sys.argv[2]))
    return app.run(None)


if __name__ == "__main__":
    raise SystemExit(main())
