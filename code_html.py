"""Code drawn as coloured HTML, with chosen lines lit up (for the web demo).

Pygments colours the code; highlighted lines get a cyan bar like an editor.
No Streamlit here, so it can be tested without a browser.
"""

from collections.abc import Iterable

from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import PythonLexer
from pygments.styles.gh_dark import GhDarkStyle
from pygments.token import Name


class _DemoStyle(GhDarkStyle):
    """GitHub's dark colours, but no purple: cyan for highlighted lines and names."""

    highlight_color = "#0f3442"
    styles = GhDarkStyle.styles | {
        Name.Function: "bold #7dd3fc",  # GitHub uses purple here
        Name.Decorator: "bold #7dd3fc",
    }


CODE_STYLE = """
<style>
.code pre {
  margin: 0; padding: 14px 16px; border: 1px solid #23272e; border-radius: 10px;
  overflow-x: auto; scrollbar-width: thin; scrollbar-color: #2f343e transparent;
  font: 12.5px/1.6 ui-monospace, "Cascadia Mono", Consolas, monospace;
}
.code pre > span[style*="background-color"] {
  display: block; margin: 0 -16px; padding: 0 16px 0 13px;
  border-left: 3px solid #38bdf8;
}
</style>
"""


def code_html(source: str, lit_lines: Iterable[int] = ()) -> str:
    """The source as coloured HTML; `lit_lines` (1 = first line) are highlighted."""
    formatter = HtmlFormatter(
        style=_DemoStyle, noclasses=True, hl_lines=list(lit_lines)
    )
    return f'{CODE_STYLE}<div class="code">{highlight(source, PythonLexer(), formatter)}</div>'
