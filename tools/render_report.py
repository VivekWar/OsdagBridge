"""Re-render the design report from a stored payload (no GUI, no analysis).

``tools/report_demo.py --payload payload.pkl`` stores everything the report
generator receives from a real design run (inputs, results, captured figures).
This script feeds that payload back into ``generate_report`` so layout work on
the report can be checked in a few seconds::

    python tools/render_report.py payload.pkl --out out/Report.pdf

The rendered PDF is identical to what the desktop application produces for the
same design, because the same ``generate_report`` code path is used.
"""
from __future__ import annotations

import argparse
import copy
import os
import pickle
import sys


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("payload", help="Pickle written by report_demo.py --payload.")
    p.add_argument("--out", required=True, help="Path of the PDF to write.")
    p.add_argument("--no-figures", action="store_true",
                   help="Drop the captured CAD figures (shows the placeholders).")
    args = p.parse_args(argv)

    from osdagbridge.core.reports.report_generator import (
        ReportFigures, ReportPayload, ReportRequest, generate_report,
    )

    with open(args.payload, "rb") as fh:
        snap = pickle.load(fh)

    out_path = os.path.abspath(args.out)
    request = ReportRequest(
        metadata=snap["metadata"],
        options=snap["options"],
        output_dir=os.path.dirname(out_path),
        file_stem=os.path.splitext(os.path.basename(out_path))[0],
    )
    payload = ReportPayload(
        metadata=snap["metadata"],
        options=snap["options"],
        inputs=copy.deepcopy(snap["inputs"]),
        analysis_summary=snap["analysis_summary"],
        design_checks=snap["design_checks"],
        figures=ReportFigures(),
        log_entries=snap["log_entries"],
        output_dict=copy.deepcopy(snap["output_dict"]),
        figure_data={} if args.no_figures else dict(snap["figure_data"]),
    )
    result = generate_report(payload, request)
    if result.pdf_path:
        print(f"PDF written: {result.pdf_path}")
        return 0
    print(f"PDF was NOT produced (TeX source: {result.tex_path})")
    return 1


if __name__ == "__main__":
    sys.exit(main())
