"""arabic-itn CLI: one transcript per stdin line -> one JSON object per stdout line."""
import argparse
import json
import sys

from . import normalize


def main(argv=None):
    ap = argparse.ArgumentParser(prog="arabic-itn", description=__doc__)
    ap.add_argument("--country", choices=["SA", "AE"], default="SA",
                    help="calling code for local 05... mobile numbers (default SA)")
    args = ap.parse_args(argv)
    for line in sys.stdin:
        if line.strip():
            print(json.dumps(normalize(line.rstrip("\n"), args.country), ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
