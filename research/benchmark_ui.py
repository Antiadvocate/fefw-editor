"""Measure repeated Tk refreshes against private saves without changing them."""
import argparse
from pathlib import Path
import json
import shutil
import statistics
import sys
import tempfile
import time
from unittest.mock import patch


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('saves', nargs='+', type=Path)
    parser.add_argument('--source', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--repeat', type=int, default=7)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.repeat < 1:
        parser.error('--repeat must be positive')
    sys.path.insert(0, str(args.source.resolve()))
    import editor
    import fefw_layer as layer
    results = []
    for index, path in enumerate(args.saves):
        with tempfile.TemporaryDirectory() as folder, \
                patch.object(editor.App, '_load_settings', return_value={}), \
                patch.object(editor.App, '_save_settings'):
            shutil.copyfile(path, Path(folder)/'Auto')
            app = editor.App(folder)
            try:
                app.open_folder(folder)
                app.update()
                original = bytes(app.sv.payload)
                reference = layer.live_convoy(original)
                def refresh():
                    app.refresh_after_core()
                    app.update_idletasks()
                refresh()
                times = []
                for _ in range(args.repeat):
                    begin = time.perf_counter()
                    refresh()
                    times.append(time.perf_counter()-begin)
                assert bytes(app.sv.payload) == original
                expected = [(r.slot, r.iid, r.qty) for r in reference.rows if r.qty and r.iid] if reference else []
                assert [(r.slot, r.iid, r.qty) for r in app._conv_rows] == expected
                results.append({'sample': index, 'payload_bytes': len(original),
                                'median_seconds': statistics.median(times), 'seconds': times})
            finally:
                for job in app.tk.call('after', 'info'):
                    app.after_cancel(job)
                app.destroy()
    args.output.write_text(json.dumps({'note': 'Warm full-page refresh including idle Tk layout; not disk loading or game performance.',
                                      'results': results}, indent=2)+'\n')
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
