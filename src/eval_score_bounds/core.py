"""Strict, offline implementation of the eval-score-bounds input contract."""
import json
import re
from decimal import Decimal
from pathlib import Path

_DECIMAL = re.compile(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]{1,6})?\Z", re.ASCII)
_LIMIT = Decimal("1000000000")


class InvalidInput(Exception):
    """An input file does not satisfy the public format contract."""


def _pairs_no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InvalidInput
        result[key] = value
    return result


def _json_object(raw):
    try:
        value = json.loads(raw, object_pairs_hook=_pairs_no_duplicates)
    except (ValueError, RecursionError):
        raise InvalidInput from None
    if not isinstance(value, dict):
        raise InvalidInput
    return value


def _decimal(value):
    if not isinstance(value, str) or not _DECIMAL.fullmatch(value):
        raise InvalidInput
    try:
        number = Decimal(value)
    except Exception:
        raise InvalidInput from None
    if abs(number) > _LIMIT:
        raise InvalidInput
    return number


def _read_utf8(path):
    try:
        return Path(path).read_bytes().decode("utf-8", errors="strict")
    except (OSError, UnicodeError, ValueError):
        raise InvalidInput from None


def parse_policy(path):
    obj = _json_object(_read_utf8(path))
    if set(obj) != {"min", "max"}:
        raise InvalidInput
    low, high = _decimal(obj["min"]), _decimal(obj["max"])
    if low > high:
        raise InvalidInput
    return low, high


def parse_rows(path):
    text = _read_utf8(path)
    # Split only the contract delimiters. splitlines() would also split Unicode separators.
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    if lines and lines[-1] == "":
        lines.pop()  # one final LF (possibly preceded by CR) is permitted
    records = []
    seen = set()
    for number, line in enumerate(lines, 1):
        if not line:
            raise InvalidInput
        obj = _json_object(line)
        if set(obj) != {"id", "score"}:
            raise InvalidInput
        identifier = obj["id"]
        if not isinstance(identifier, str) or not identifier:
            raise InvalidInput
        if identifier in seen:
            raise InvalidInput
        seen.add(identifier)
        records.append((number, _decimal(obj["score"])))
    return records


def evaluate(rows_path, policy_path):
    rows = policy = None
    rows_error = policy_error = False
    try:
        rows = parse_rows(rows_path)
    except InvalidInput:
        rows_error = True
    try:
        policy = parse_policy(policy_path)
    except InvalidInput:
        policy_error = True
    if rows_error or policy_error:
        raise InvalidInput
    low, high = policy
    below = [line for line, score in rows if score < low]
    above = [line for line, score in rows if score > high]
    return {
        "status": "out_of_bounds" if below or above else "within_bounds",
        "record_count": len(rows), "below_lines": below, "above_lines": above,
    }
