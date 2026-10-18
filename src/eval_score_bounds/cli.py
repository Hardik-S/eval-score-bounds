"""Command line interface."""
import json
import sys

from .core import InvalidInput, evaluate

_HELP = "Usage: eval-score-bounds ROWS.jsonl POLICY.json\nValidate decimal score fixtures against inclusive bounds.\n"


def main(argv=None):
    args = sys.argv[1:] if argv is None else list(argv)
    if args in (["-h"], ["--help"]):
        sys.stdout.write(_HELP)
        return 0
    if len(args) != 2:
        sys.stdout.write('{"status":"invalid_input"}\n')
        return 2
    try:
        result = evaluate(args[0], args[1])
    except InvalidInput:
        sys.stdout.write('{"status":"invalid_input"}\n')
        return 2
    sys.stdout.write(json.dumps(result, separators=(",", ":")) + "\n")
    return 1 if result["status"] == "out_of_bounds" else 0


if __name__ == "__main__":
    raise SystemExit(main())
