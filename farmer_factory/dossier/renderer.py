"""LaTeX renderer for dossier generation.

Uses Jinja2 templates with custom delimiters to avoid LaTeX conflicts.
"""

import logging
import shutil
from pathlib import Path

import jinja2
from jinja2 import StrictUndefined

from .models import DossierData

logger = logging.getLogger(__name__)

# Template directory relative to this file
TEMPLATE_DIR = Path(__file__).parent / "templates"
STYLES_DIR = Path(__file__).parent / "styles"


class RenderError(Exception):
    """Raised when template rendering fails."""

    pass


class DossierRenderer:
    """Renders DossierData to LaTeX using Jinja2 templates.

    Uses custom delimiters to avoid conflicts with LaTeX syntax:
    - Block tags: <% ... %>
    - Variable tags: << ... >>
    - Comment tags: <# ... #>
    """

    def __init__(self, template_dir: Path | None = None):
        """Initialize the renderer with template directory.

        Args:
            template_dir: Custom template directory (defaults to package templates)
        """
        self.template_dir = template_dir or TEMPLATE_DIR

        # Configure Jinja2 environment with custom delimiters
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(self.template_dir),
            # Custom delimiters to avoid LaTeX conflicts
            block_start_string="<%",
            block_end_string="%>",
            variable_start_string="<<",
            variable_end_string=">>",
            comment_start_string="<#",
            comment_end_string="#>",
            # Strict mode - fail on undefined variables
            undefined=StrictUndefined,
            # Auto-escape disabled (we handle LaTeX escaping manually)
            autoescape=False,
            # Trim whitespace around blocks
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Register custom filters
        self._register_filters()

    def _register_filters(self) -> None:
        """Register custom Jinja2 filters for LaTeX."""
        self.env.filters["latex_escape"] = self._latex_escape
        self.env.filters["format_date"] = self._format_date
        self.env.filters["truncate"] = self._truncate

    @staticmethod
    def _latex_escape(text: str | None) -> str:
        """Escape LaTeX special characters.

        Args:
            text: Input text (may be None)

        Returns:
            LaTeX-safe string
        """
        if text is None:
            return ""

        if not isinstance(text, str):
            text = str(text)

        # Order matters - backslash first
        replacements = [
            ("\\", r"\textbackslash{}"),
            ("&", r"\&"),
            ("%", r"\%"),
            ("$", r"\$"),
            ("#", r"\#"),
            ("_", r"\_"),
            ("{", r"\{"),
            ("}", r"\}"),
            ("~", r"\textasciitilde{}"),
            ("^", r"\textasciicircum{}"),
            ('"', r"''"),
            ("'", r"'"),
        ]

        for char, replacement in replacements:
            text = text.replace(char, replacement)

        # Normalize newlines to LaTeX line breaks
        text = text.replace("\n", r" \\ ")

        return text

    @staticmethod
    def _format_date(date_str: str | None, fmt: str = "%B %d, %Y") -> str:
        """Format a date string for display.

        Args:
            date_str: ISO date string or None
            fmt: Output format (strftime)

        Returns:
            Formatted date or original string if parsing fails
        """
        if not date_str:
            return "Unknown"

        # Try to parse ISO format
        from datetime import datetime

        try:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return dt.strftime(fmt)
        except (ValueError, AttributeError):
            # Return as-is if not parseable (e.g., "circa 1950s")
            return date_str

    @staticmethod
    def _truncate(text: str | None, length: int = 50, suffix: str = "...") -> str:
        """Truncate text to specified length.

        Args:
            text: Input text
            length: Maximum length
            suffix: Suffix to append if truncated

        Returns:
            Truncated text
        """
        if not text:
            return ""

        if len(text) <= length:
            return text

        return text[: length - len(suffix)] + suffix

    def render(self, data: DossierData, output_dir: Path) -> Path:
        """Render DossierData to a .tex file.

        Args:
            data: Complete dossier data
            output_dir: Directory to write output files

        Returns:
            Path to the generated .tex file

        Raises:
            RenderError: If template rendering fails
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Load and render main template
            template = self.env.get_template("main.tex.j2")
            tex_content = template.render(d=data)

            # Write .tex file
            output_path = output_dir / f"{data.case_id}_dossier.tex"
            output_path.write_text(tex_content, encoding="utf-8")
            logger.info(f"Rendered LaTeX to {output_path}")

            # Copy style file
            self._copy_style_file(output_dir)

            return output_path

        except jinja2.TemplateError as e:
            raise RenderError(f"Template rendering failed: {e}") from e
        except IOError as e:
            raise RenderError(f"Failed to write output: {e}") from e

    def _copy_style_file(self, output_dir: Path) -> None:
        """Copy the civictable.sty style file to output directory.

        Args:
            output_dir: Directory to copy style file to
        """
        style_src = STYLES_DIR / "civictable.sty"
        style_dst = output_dir / "civictable.sty"

        if style_src.exists():
            shutil.copy(style_src, style_dst)
            logger.debug(f"Copied style file to {style_dst}")
        else:
            raise RenderError(f"Style file not found: {style_src}")
