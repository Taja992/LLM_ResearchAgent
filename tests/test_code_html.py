"""Tests for code_html.py: code becomes coloured HTML with chosen lines lit up."""

from code_html import code_html

SOURCE = "a = 1\nb = 2\nc = 3\n"
LIT_LINE = '<span style="background-color'  # how Pygments marks a highlighted line


def test_only_the_chosen_line_is_lit_up() -> None:
    html = code_html(SOURCE, [2])

    assert html.count(LIT_LINE) == 1
    lit_line = html.split(LIT_LINE, 1)[1].split("\n", 1)[0]
    assert ">b<" in lit_line


def test_no_lines_lit_up_by_default() -> None:
    assert LIT_LINE not in code_html(SOURCE)


def test_no_purple_in_the_colours() -> None:
    html = code_html("@classmethod\ndef find_paper():\n    pass\n").lower()

    assert "#d2a8ff" not in html  # GitHub's purple for function names
