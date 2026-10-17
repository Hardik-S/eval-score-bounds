import json

import pytest

from eval_score_bounds.core import InvalidInput, evaluate, parse_rows


def write(tmp_path, name, body):
    path = tmp_path / name
    path.write_bytes(body if isinstance(body, bytes) else body.encode("utf-8"))
    return path


def policy(tmp_path, low='"0"', high='"1"'):
    return write(tmp_path, "policy.json", '{"min":'+low+',"max":'+high+'}')


def test_inclusive_and_exact_decimal_precision(tmp_path):
    rows = write(tmp_path, "rows", '{"id":"é","score":"0"}\r\n{"id":"β","score":"1.000000"}\n')
    assert evaluate(rows, policy(tmp_path)) == {
        "status": "within_bounds", "record_count": 2, "below_lines": [], "above_lines": []}
    rows = write(tmp_path, "rows", '{"id":"tiny","score":"0.000001"}')
    assert evaluate(rows, policy(tmp_path, '"0.000002"', '"1"'))["below_lines"] == [1]


@pytest.mark.parametrize("value", ["+1", " 1", "1 ", "01", ".1", "1.", "1e0", "NaN", "Infinity", "١", "1.1234567", "1000000000.000001", "-1000000001"])
def test_decimal_domain_rejected(tmp_path, value):
    rows = write(tmp_path, "rows", json.dumps({"id":"x", "score":value}, ensure_ascii=False))
    with pytest.raises(InvalidInput):
        evaluate(rows, policy(tmp_path))


@pytest.mark.parametrize("body", [
    '{"id":"x","id":"y","score":"0"}', '{"id":"x","score":0}',
    '{"id":"x","score":"0","extra":1}', '{"id":"","score":"0"}',
    '{"id":"x","score":"0"}\n\n', '{"id":"x","score":"0"}\u2028{"id":"y","score":"0"}',
])
def test_rows_strictness(tmp_path, body):
    rows = write(tmp_path, "rows", body)
    with pytest.raises(InvalidInput):
        evaluate(rows, policy(tmp_path))


def test_empty_and_newlines(tmp_path):
    rows = write(tmp_path, "rows", b"")
    assert evaluate(rows, policy(tmp_path))["record_count"] == 0
    rows = write(tmp_path, "rows", b'{"id":"x","score":"-0"}\r')
    assert evaluate(rows, policy(tmp_path))["record_count"] == 1
    rows = write(tmp_path, "rows", b'{"id":"x","score":"0"}\r{"id":"y","score":"1"}')
    assert evaluate(rows, policy(tmp_path))["record_count"] == 2


def test_duplicate_ids_and_policy_order(tmp_path):
    rows = write(tmp_path, "rows", '{"id":"x","score":"0"}\n{"id":"x","score":"1"}')
    with pytest.raises(InvalidInput):
        evaluate(rows, policy(tmp_path))
    with pytest.raises(InvalidInput):
        evaluate(write(tmp_path, "empty", ""), policy(tmp_path, '"2"', '"1"'))


@pytest.mark.parametrize("body", [
    '{"min":"0","min":"0","max":"1"}', '{"min":"0"}',
    '{"min":"0","max":"1","extra":0}', '{"min":0,"max":"1"}',
    '{"min":"0","max":"1"} {}', '[]',
])
def test_policy_schema_and_json_are_strict(tmp_path, body):
    with pytest.raises(InvalidInput):
        evaluate(write(tmp_path, "rows", ""), write(tmp_path, "policy", body))


def test_both_parsers_attempted_after_bad_rows(tmp_path, monkeypatch):
    import eval_score_bounds.core as core
    calls = []
    original = core.parse_policy
    def observed(path):
        calls.append(path)
        return original(path)
    monkeypatch.setattr(core, "parse_policy", observed)
    with pytest.raises(InvalidInput):
        evaluate(write(tmp_path, "bad", "not-json"), policy(tmp_path))
    assert len(calls) == 1


def test_invalid_utf8(tmp_path):
    with pytest.raises(InvalidInput):
        parse_rows(write(tmp_path, "rows", b"\xff"))
