from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lensgraph.data.match_native import MatchNativeConfig, build_match_native_catalog


def _families(value: str):
    return ['SIS', 'PM'] if value.lower() == 'all' else [value.upper()]


def _modes(value: str):
    return ['pure', 'noisy'] if value.lower() == 'all' else [value.lower()]


def main() -> None:
    ap = argparse.ArgumentParser(description='Build gw-catalog HDF5/parquet catalogs from match-generated arrays.')
    ap.add_argument('--data-root', default='/root/autodl-tmp/qkzhang')
    ap.add_argument('--out-dir', default='catalogs/match_native')
    ap.add_argument('--family', choices=['SIS', 'PM', 'sis', 'pm', 'all'], default='all')
    ap.add_argument('--mode', choices=['pure', 'noisy', 'all'], default='all')
    ap.add_argument('--limit', type=int, default=None, help='number of lensed pairs')
    ap.add_argument('--unlensed-limit', type=int, default=None)
    ap.add_argument('--target-len', type=int, default=8192)
    ap.add_argument('--stride', type=int, default=2)
    ap.add_argument('--peak-start', type=int, default=3000)
    ap.add_argument('--peak-stop', type=int, default=3800)
    ap.add_argument('--chunk-size', type=int, default=64)
    args = ap.parse_args()

    for family in _families(args.family):
        for mode in _modes(args.mode):
            name = f'match_{family.lower()}_{mode}'
            cfg = MatchNativeConfig(
                data_root=Path(args.data_root),
                family=family,  # type: ignore[arg-type]
                mode=mode,  # type: ignore[arg-type]
                output_prefix=Path(args.out_dir) / name,
                n_lensed=args.limit,
                n_unlensed=args.unlensed_limit,
                target_len=args.target_len,
                stride=args.stride,
                peak_start=args.peak_start,
                peak_stop=args.peak_stop,
                chunk_size=args.chunk_size,
            )
            h5_path, meta_path = build_match_native_catalog(cfg)
            print(f'[done] {name}: h5={h5_path} metadata={meta_path}')


if __name__ == '__main__':
    main()
