"""Behavior-level tests for the sssp CLI."""

from __future__ import annotations

import io
import json
import math
import textwrap

import pytest

from sssp.main import main


def _run(argv, monkeypatch, capsys, stdin_text=""):
    monkeypatch.setattr("sys.stdin", io.StringIO(stdin_text))
    rc = main(argv)
    out = capsys.readouterr()
    return rc, out.out, out.err


def test_text_output_from_stdin(monkeypatch, capsys):
    graph_text = textwrap.dedent(
        """\
        3 0
        0 1 2.0
        1 2 3.0
        """
    )
    rc, stdout, stderr = _run(["-"], monkeypatch, capsys, stdin_text=graph_text)
    assert rc == 0, stderr
    lines = stdout.strip().splitlines()
    # Format: "vertex\tdistance\tpredecessor"
    assert lines[0].split("\t") == ["0", "0", "-"]
    assert lines[1].split("\t") == ["1", "2", "0"]
    assert lines[2].split("\t") == ["2", "5", "1"]


def test_json_output_marks_unreachable_as_inf(monkeypatch, capsys):
    graph_text = "3 0\n0 1 1.5\n"  # vertex 2 unreachable
    rc, stdout, _ = _run(
        ["-", "--format", "json"], monkeypatch, capsys, stdin_text=graph_text
    )
    assert rc == 0
    payload = json.loads(stdout)
    assert payload["source"] == 0
    assert payload["distances"][0] == 0
    assert payload["distances"][1] == 1.5
    assert payload["distances"][2] == "inf"
    assert payload["predecessors"] == [None, 0, None]


def test_invalid_header_returns_error_code(monkeypatch, capsys):
    rc, _, stderr = _run(["-"], monkeypatch, capsys, stdin_text="garbage line\n")
    assert rc == 2
    assert "error" in stderr.lower()


def test_negative_weight_in_input_reports_error(monkeypatch, capsys):
    rc, _, stderr = _run(["-"], monkeypatch, capsys, stdin_text="2 0\n0 1 -3.0\n")
    assert rc == 2
    assert "non-negative" in stderr


def test_missing_file_reports_error(monkeypatch, capsys):
    rc, _, stderr = _run(
        ["/nonexistent/path/that/does/not/exist.txt"],
        monkeypatch,
        capsys,
    )
    assert rc == 2
    assert "error" in stderr.lower()


def test_reads_from_file(tmp_path, monkeypatch, capsys):
    p = tmp_path / "graph.txt"
    p.write_text("# leading comment\n2 0\n\n0 1 7\n")
    rc, stdout, stderr = _run([str(p)], monkeypatch, capsys)
    assert rc == 0, stderr
    lines = stdout.strip().splitlines()
    assert lines[0].split("\t") == ["0", "0", "-"]
    assert lines[1].split("\t") == ["1", "7", "0"]


def test_invalid_source_reports_error(monkeypatch, capsys):
    rc, _, stderr = _run(["-"], monkeypatch, capsys, stdin_text="2 5\n0 1 1\n")
    assert rc == 2
    assert "source" in stderr.lower()
