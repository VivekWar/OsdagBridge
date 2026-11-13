"""Drive the OsdagBridge desktop application end-to-end and save a design report.

The script performs — on the real GUI, through the real widgets — the same
sequence a user follows to test report generation:

    1. open OsdagBridge,
    2. enter the basic inputs (project location, span, carriageway width),
    3. click **Design** and wait for the analysis / design run,
    4. click **Generate Report**, fill the report dialog and save the PDF.

It exists so the "before" and "after" reports can be reproduced with exactly
the same inputs, and it is also what the demonstration video shows.

Usage (from the repository root, inside the ``osdagbridge-env`` environment)::

    python tools/report_demo.py --out Report_After.pdf
    python tools/report_demo.py --out out/r.pdf --span 30 --carriageway 10.5 \
        --state Maharashtra --district Mumbai --payload out/payload.pkl

``--payload`` additionally stores the exact report payload (inputs, design
results, captured figures) so the report can be re-rendered in seconds with
``tools/render_report.py`` while working on the report layout.
"""
from __future__ import annotations

import argparse
import os
import pickle
import sys
import time


def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--out", required=True, help="Path of the PDF report to write.")
    p.add_argument("--span", default="30", help="Span in metres (default: 30).")
    p.add_argument("--carriageway", default="10.5", help="Carriageway width in metres.")
    p.add_argument("--footpath", default=None, help="Footpath option text (e.g. 'Both').")
    p.add_argument("--state", default="Maharashtra")
    p.add_argument("--district", default="Mumbai")
    p.add_argument("--project-name", default="Sample Plate Girder Bridge")
    p.add_argument("--designer", default="")
    p.add_argument("--reviewer", default="")
    p.add_argument("--organization", default="")
    p.add_argument("--client", default="")
    p.add_argument("--job-number", default="OB-2026-001")
    p.add_argument("--version", default="Rev 0")
    p.add_argument("--payload", default=None,
                   help="Optional path: pickle the report payload for fast re-rendering.")
    p.add_argument("--frames", default=None,
                   help="Optional directory: save screen frames of the run (for a screencast).")
    p.add_argument("--frame-interval", type=float, default=0.25,
                   help="Seconds between two saved frames (default: 0.25).")
    p.add_argument("--step-delay", type=float, default=1.2,
                   help="Pause between GUI steps in seconds (larger = easier to follow).")
    p.add_argument("--hold", type=float, default=3.0,
                   help="Seconds to keep the window open after the report is saved.")
    p.add_argument("--timeout", type=float, default=1800.0,
                   help="Abort if the design run takes longer than this (seconds).")
    return p.parse_args(argv)


def _install_payload_recorder(path: str) -> None:
    """Store the payload handed to ``generate_report`` (before it is consumed)."""
    from osdagbridge.core.reports import report_generator as rg

    original = rg.generate_report

    def recording_generate_report(payload, request):
        try:
            snapshot = {
                "metadata": payload.metadata,
                "options": payload.options,
                "inputs": dict(payload.inputs),
                "analysis_summary": payload.analysis_summary,
                "design_checks": payload.design_checks,
                "log_entries": list(payload.log_entries or []),
                "output_dict": _picklable(dict(payload.output_dict)),
                "figure_data": dict(payload.figure_data),
            }
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            with open(path, "wb") as fh:
                pickle.dump(snapshot, fh)
            print(f"[report-demo] payload stored: {path}")
        except Exception as exc:  # never break report generation
            print(f"[report-demo] could not store payload: {exc}")
        return original(payload, request)

    rg.generate_report = recording_generate_report


def _picklable(obj, _depth=0):
    """Deep-copy ``obj`` keeping only data that survives pickling."""
    if _depth > 40:
        return repr(obj)
    if isinstance(obj, dict):
        return {k: _picklable(v, _depth + 1) for k, v in obj.items()
                if isinstance(k, (str, int, float, bool, tuple, type(None)))}
    if isinstance(obj, (list, tuple, set)):
        seq = [_picklable(v, _depth + 1) for v in obj]
        return seq if not isinstance(obj, tuple) else tuple(seq)
    if isinstance(obj, (str, int, float, bool, bytes, type(None))):
        return obj
    try:
        import numpy as np
        if isinstance(obj, np.generic):
            return obj.item()
        if isinstance(obj, np.ndarray):
            return obj.tolist()
    except Exception:
        pass
    try:
        pickle.dumps(obj)
        return obj
    except Exception:
        return repr(obj)


def main(argv=None) -> int:
    args = parse_args(argv)
    out_path = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    # Importing the desktop entry module prepares the section databases exactly
    # as a normal start of the application does.
    import osdagbridge.desktop.__main__ as desktop_main
    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication, QDialog, QLineEdit, QComboBox, QWidget

    from osdagbridge.core.bridge_types.plate_girder.plategirderbridge import PlateGirderBridge
    from osdagbridge.core.utils.common import KEY_SPAN, KEY_CARRIAGEWAY_WIDTH, KEY_FOOTPATH
    from osdagbridge.desktop.ui.template_page import CustomWindow

    if args.payload:
        _install_payload_recorder(os.path.abspath(args.payload))

    app = QApplication.instance() or QApplication(sys.argv[:1])
    icon = desktop_main._app_icon()
    if not icon.isNull():
        app.setWindowIcon(icon)
    stylesheet = desktop_main.load_stylesheet()
    if stylesheet:
        app.setStyleSheet(stylesheet)

    window = CustomWindow("OsdagBridge", PlateGirderBridge)
    window.showMaximized()
    window.show()

    state = {"step": "start", "t0": time.time(), "result": 1, "frame": 0}
    delay_ms = int(args.step_delay * 1000)

    # ---- optional: record the run as numbered frames ------------------------
    if args.frames:
        frames_dir = os.path.abspath(args.frames)
        os.makedirs(frames_dir, exist_ok=True)

        def grab_frame():
            screen = window.screen() or QApplication.primaryScreen()
            pixmap = screen.grabWindow(0)
            if pixmap.isNull():
                return
            if pixmap.width() > 1920:
                pixmap = pixmap.scaledToWidth(1920, Qt.SmoothTransformation)
            state["frame"] += 1
            pixmap.save(os.path.join(frames_dir, "frame_%05d.jpg" % state["frame"]), "JPG", 88)

        frame_timer = QTimer(window)
        frame_timer.timeout.connect(grab_frame)
        frame_timer.start(int(args.frame_interval * 1000))

    def log(msg):
        print(f"[report-demo] {msg}", flush=True)

    def later(fn, ms=None):
        QTimer.singleShot(delay_ms if ms is None else ms, fn)

    def close_message_boxes():
        """Accept any information box left open by the application."""
        w = QApplication.activeModalWidget()
        if isinstance(w, QDialog) and w.__class__.__name__ == "CustomMessageBox":
            w.accept()
            return True
        return False

    # ---- step 1: project location ------------------------------------------
    def fill_location_dialog():
        dlg = QApplication.activeModalWidget()
        if dlg is None or dlg.__class__.__name__ != "ProjectLocationDialog":
            later(fill_location_dialog, 300)
            return
        dlg.method_radio_location.setChecked(True)
        dlg.state_combo.setCurrentText(args.state)
        QApplication.processEvents()
        if dlg.district_combo.findText(args.district) >= 0:
            dlg.district_combo.setCurrentText(args.district)
        elif dlg.district_combo.count() > 1:
            dlg.district_combo.setCurrentIndex(1)
        log(f"location: {dlg.district_combo.currentText()}, {dlg.state_combo.currentText()}")
        later(dlg.validate_and_save)

    def step_location():
        log("selecting project location")
        later(fill_location_dialog, 600)
        window.input_dock.show_project_location_dialog()   # modal; returns when saved
        later(step_basic_inputs)

    # ---- step 2: span / carriageway ----------------------------------------
    def type_into(key, text):
        widget = window.input_dock.input_widget.findChild(QWidget, key)
        if isinstance(widget, QLineEdit):
            widget.setFocus()
            widget.clear()
            QTest.keyClicks(widget, str(text), delay=40)
            widget.editingFinished.emit()
        elif isinstance(widget, QComboBox):
            widget.setCurrentText(str(text))
        QApplication.processEvents()

    def step_basic_inputs():
        log(f"span = {args.span} m, carriageway width = {args.carriageway} m")
        type_into(KEY_SPAN, args.span)
        type_into(KEY_CARRIAGEWAY_WIDTH, args.carriageway)
        if args.footpath:
            type_into(KEY_FOOTPATH, args.footpath)
        later(step_design)

    # ---- step 3: design -----------------------------------------------------
    def step_design():
        log("clicking Design")
        state["t_design"] = time.time()
        window.input_dock.design_btn.click()
        later(wait_design, 1500)

    def wait_design():
        if time.time() - state["t_design"] > args.timeout:
            log("design timed out")
            app.exit(2)
            return
        if getattr(window, "_design_running", False):
            later(wait_design, 1000)
            return
        if close_message_boxes():
            later(wait_design, 500)
            return
        if not getattr(window.backend, "output_dict", None):
            log("design did not produce results (see the log dock)")
            app.exit(3)
            return
        log(f"design finished in {time.time() - state['t_design']:.0f} s")
        later(step_report, max(delay_ms, 2500))

    # ---- step 4: report -----------------------------------------------------
    def fill_report_dialog():
        dlg = QApplication.activeModalWidget()
        if dlg is None or dlg.__class__.__name__ != "ReportOptionsDialog":
            if close_message_boxes():
                pass
            later(fill_report_dialog, 300)
            return
        for widget, text in ((dlg.project_name, args.project_name),
                             (dlg.designer, args.designer),
                             (dlg.reviewer, args.reviewer),
                             (dlg.group_name, args.organization),
                             (dlg.client, args.client),
                             (dlg.job_number, args.job_number),
                             (dlg.report_version, args.version)):
            if text:
                widget.setText(text)
        QApplication.processEvents()

        def to_page2():
            dlg.go_next()
            later(save)

        def save():
            # Same as the "Save PDF" button, without the native file chooser.
            dlg.request = dlg.build_request(out_path)
            dlg.is_preview = False
            log(f"saving report to {out_path}")
            state["t_report"] = time.time()
            dlg.accept()
            later(wait_report, 1000)

        later(to_page2)

    def step_report():
        log("clicking Generate Report")
        later(fill_report_dialog, 600)
        window.output_dock._on_report_clicked()   # modal dialog; returns after accept

    def wait_report():
        thread = getattr(window, "_report_thread", None)
        running = False
        try:
            running = thread is not None and thread.isRunning()
        except RuntimeError:
            running = False
        if running and time.time() - state["t_report"] < args.timeout:
            later(wait_report, 500)
            return
        QApplication.processEvents()
        ok = os.path.exists(out_path)
        log(("report written: " if ok else "report NOT written: ") + out_path)
        state["result"] = 0 if ok else 4
        later(finish, 1200)

    def finish():
        close_message_boxes()
        QTimer.singleShot(int(args.hold * 1000), lambda: app.exit(state["result"]))

    later(step_location, 2500)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
