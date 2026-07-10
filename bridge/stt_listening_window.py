#!/usr/bin/env python3
"""Slim Wayland overlay that visualizes live KLOR microphone input."""

from __future__ import annotations

import json
import math
import sys
from collections import deque

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
gi.require_version("Gtk4LayerShell", "1.0")

from gi.repository import Gdk, Gio, GLib, Gtk, Gtk4LayerShell  # noqa: E402


WINDOW_WIDTH = 568
WINDOW_HEIGHT = 52
HISTORY_SIZE = 140


class ListeningApp(Gtk.Application):
    def __init__(self) -> None:
        super().__init__(
            application_id="org.klor.Listening",
            flags=Gio.ApplicationFlags.NON_UNIQUE,
        )
        self.waveform: Gtk.DrawingArea | None = None
        self.status: Gtk.Box | None = None
        self.status_title: Gtk.Label | None = None
        self.status_body: Gtk.Label | None = None
        self.mode = "listening"
        self.samples: deque[float] = deque([0.0] * HISTORY_SIZE, maxlen=HISTORY_SIZE)

    def do_activate(self) -> None:  # type: ignore[override]
        window = Gtk.ApplicationWindow(application=self)
        window.set_title("KLOR Listening")
        window.set_decorated(False)
        window.set_resizable(False)
        window.set_default_size(WINDOW_WIDTH, WINDOW_HEIGHT)

        Gtk4LayerShell.init_for_window(window)
        Gtk4LayerShell.set_namespace(window, "klor-listening")
        Gtk4LayerShell.set_layer(window, Gtk4LayerShell.Layer.OVERLAY)
        Gtk4LayerShell.set_anchor(window, Gtk4LayerShell.Edge.TOP, True)
        Gtk4LayerShell.set_margin(window, Gtk4LayerShell.Edge.TOP, 20)
        Gtk4LayerShell.set_keyboard_mode(window, Gtk4LayerShell.KeyboardMode.NONE)
        Gtk4LayerShell.set_exclusive_zone(window, 0)

        overlay = Gtk.Overlay()
        waveform = Gtk.DrawingArea()
        self.waveform = waveform
        waveform.set_content_width(WINDOW_WIDTH)
        waveform.set_content_height(WINDOW_HEIGHT)
        waveform.set_draw_func(self._draw_waveform)
        overlay.set_child(waveform)

        status = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
        self.status = status
        status.set_margin_top(7)
        status.set_margin_bottom(7)
        status.set_margin_start(16)
        status.set_margin_end(16)
        status.set_valign(Gtk.Align.CENTER)
        status.set_visible(False)

        title = Gtk.Label()
        self.status_title = title
        title.set_halign(Gtk.Align.CENTER)
        title.set_justify(Gtk.Justification.CENTER)
        title.add_css_class("status-title")
        body = Gtk.Label()
        self.status_body = body
        body.set_halign(Gtk.Align.CENTER)
        body.set_justify(Gtk.Justification.CENTER)
        body.set_ellipsize(3)
        body.add_css_class("status-body")
        status.append(title)
        status.append(body)
        overlay.add_overlay(status)
        window.set_child(overlay)
        self._install_css()

        GLib.io_add_watch(
            sys.stdin,
            GLib.IO_IN | GLib.IO_HUP | GLib.IO_ERR,
            self._on_stdin,
        )
        window.present()

    def _on_stdin(self, _source, condition: GLib.IOCondition) -> bool:
        if condition & (GLib.IO_HUP | GLib.IO_ERR):
            self.quit()
            return False

        line = sys.stdin.readline()
        if not line:
            self.quit()
            return False

        try:
            message = json.loads(line)
        except (TypeError, ValueError, json.JSONDecodeError):
            return True

        if message.get("type") == "level":
            try:
                fraction = max(0.0, min(1.0, float(message.get("value", 0.0))))
            except (TypeError, ValueError):
                return True
            self.mode = "listening"
            self.samples.append(fraction)
            if self.status is not None:
                self.status.set_visible(False)
        elif message.get("type") == "state":
            self.mode = str(message.get("state", "processing"))
            if self.status_title is not None:
                self.status_title.set_text(str(message.get("title", "")))
            if self.status_body is not None:
                self.status_body.set_text(str(message.get("body", "")))
            if self.status is not None:
                self.status.set_visible(True)

        if self.waveform is not None:
            self.waveform.queue_draw()
        return True

    def _draw_waveform(self, _area, cr, width: int, height: int) -> None:
        radius = 7.0
        self._rounded_rectangle(cr, 0.5, 0.5, width - 1.0, height - 1.0, radius)
        cr.set_source_rgba(0.16, 0.16, 0.17, 0.98)
        cr.fill_preserve()
        cr.set_source_rgba(1.0, 1.0, 1.0, 0.10)
        cr.set_line_width(1.0)
        cr.stroke()

        if self.mode != "listening":
            return

        center_y = height / 2.0
        cr.set_source_rgba(1.0, 1.0, 1.0, 0.18)
        cr.set_line_width(1.0)
        cr.set_dash([1.0, 3.0])
        cr.move_to(12.0, center_y)
        cr.line_to(width - 12.0, center_y)
        cr.stroke()
        cr.set_dash([])

        samples = tuple(self.samples)
        if len(samples) < 2:
            return
        x_step = (width - 24.0) / (len(samples) - 1)
        max_height = height - 13.0
        cr.set_source_rgba(0.94, 0.95, 0.97, 0.96)
        cr.set_line_width(2.0)
        cr.set_line_cap(1)

        for index, sample in enumerate(samples):
            if sample < 0.018 or not math.isfinite(sample):
                continue
            bar_height = min(max_height, 2.0 + sample * max_height)
            x = 12.0 + index * x_step
            cr.move_to(x, center_y - bar_height / 2.0)
            cr.line_to(x, center_y + bar_height / 2.0)
        cr.stroke()

    @staticmethod
    def _install_css() -> None:
        provider = Gtk.CssProvider()
        provider.load_from_data(b"""
        .status-title {
          color: #f0f2f5;
          font-size: 16px;
          font-weight: 700;
        }
        .status-body {
          color: #aeb4bd;
          font-size: 13px;
        }
        """)
        display = Gdk.Display.get_default()
        if display is not None:
            Gtk.StyleContext.add_provider_for_display(
                display, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
            )

    @staticmethod
    def _rounded_rectangle(cr, x: float, y: float, width: float, height: float, radius: float) -> None:
        cr.new_sub_path()
        cr.arc(x + width - radius, y + radius, radius, -math.pi / 2, 0)
        cr.arc(x + width - radius, y + height - radius, radius, 0, math.pi / 2)
        cr.arc(x + radius, y + height - radius, radius, math.pi / 2, math.pi)
        cr.arc(x + radius, y + radius, radius, math.pi, 3 * math.pi / 2)
        cr.close_path()


def main() -> int:
    return ListeningApp().run([])


if __name__ == "__main__":
    raise SystemExit(main())
