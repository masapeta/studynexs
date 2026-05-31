"""Sample process RSS during soak tests. Usage: python scripts/memory_sampler.py --interval 60 --duration 21600"""
from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone

try:
    import psutil
except ImportError:
    raise SystemExit("Install psutil: pip install psutil") from None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--interval", type=int, default=60, help="Seconds between samples")
    parser.add_argument("--duration", type=int, default=3600, help="Total run seconds")
    parser.add_argument("--output", type=str, default="memory_samples.jsonl")
    args = parser.parse_args()

    proc = psutil.Process()
    end = time.time() + args.duration

    with open(args.output, "a", encoding="utf-8") as fh:
        while time.time() < end:
            mem = proc.memory_info()
            record = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "rss_mb": round(mem.rss / (1024 * 1024), 2),
                "vms_mb": round(mem.vms / (1024 * 1024), 2),
            }
            fh.write(json.dumps(record) + "\n")
            fh.flush()
            print(json.dumps(record))
            time.sleep(args.interval)


if __name__ == "__main__":
    main()
