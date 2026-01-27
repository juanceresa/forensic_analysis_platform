"""LaTeX to PDF compiler for dossier generation.

Supports pdflatex and xelatex engines with dry-run mode for testing.
"""

import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


class CompilationError(Exception):
    """Raised when LaTeX compilation fails."""

    def __init__(self, message: str, log_content: str | None = None):
        super().__init__(message)
        self.log_content = log_content


class DossierCompiler:
    """Compiles LaTeX files to PDF using pdflatex or xelatex.

    Runs the engine twice to resolve cross-references and table of contents.
    """

    SUPPORTED_ENGINES = ("pdflatex", "xelatex")
    AUX_EXTENSIONS = (".aux", ".log", ".toc", ".out", ".fls", ".fdb_latexmk", ".synctex.gz")

    def __init__(self, engine: str = "xelatex", timeout: int = 120):
        """Initialize the compiler.

        Args:
            engine: LaTeX engine to use ("xelatex" or "pdflatex")
            timeout: Maximum time per compilation pass in seconds
        """
        if engine not in self.SUPPORTED_ENGINES:
            raise ValueError(f"Unsupported engine: {engine}. Use one of {self.SUPPORTED_ENGINES}")

        self.engine = engine
        self.timeout = timeout

    def is_available(self) -> bool:
        """Check if the LaTeX engine is available on the system.

        Returns:
            True if the engine is found in PATH
        """
        try:
            result = subprocess.run(
                [self.engine, "--version"],
                capture_output=True,
                timeout=10,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def compile(self, tex_path: Path, output_dir: Path | None = None) -> Path:
        """Compile a .tex file to PDF.

        Runs the LaTeX engine twice to resolve cross-references.

        Args:
            tex_path: Path to the .tex file
            output_dir: Output directory (defaults to tex_path's directory)

        Returns:
            Path to the generated PDF

        Raises:
            CompilationError: If compilation fails or engine not available
        """
        tex_path = Path(tex_path)
        output_dir = Path(output_dir) if output_dir else tex_path.parent

        # Verify engine is available
        if not self.is_available():
            raise CompilationError(
                f"{self.engine} not found. Install a TeX distribution "
                "(MacTeX on macOS, TeX Live on Linux) or use brew install basictex."
            )

        # Verify input file exists
        if not tex_path.exists():
            raise CompilationError(f"Input file not found: {tex_path}")

        # Verify style file exists
        self._assert_includes(tex_path, output_dir)

        # Run compilation twice (resolves TOC, cross-references)
        for pass_num in [1, 2]:
            logger.info(f"{self.engine} pass {pass_num}/2: {tex_path.name}")
            self._run_compilation(tex_path, output_dir, pass_num)

        # Verify PDF was generated
        pdf_path = output_dir / tex_path.with_suffix(".pdf").name
        if not pdf_path.exists():
            raise CompilationError(f"PDF not generated: {pdf_path}")

        # Clean up auxiliary files
        self._cleanup(output_dir, tex_path.stem)

        logger.info(f"PDF generated: {pdf_path}")
        return pdf_path

    def _run_compilation(self, tex_path: Path, output_dir: Path, pass_num: int) -> None:
        """Run a single compilation pass.

        Args:
            tex_path: Path to .tex file
            output_dir: Output directory
            pass_num: Pass number (for error messages)

        Raises:
            CompilationError: If compilation fails
        """
        try:
            result = subprocess.run(
                [
                    self.engine,
                    "-interaction=nonstopmode",
                    "-output-directory",
                    str(output_dir.resolve()),
                    tex_path.name,  # Just filename since cwd is tex_path.parent
                ],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=tex_path.parent.resolve(),  # Run from source dir for relative paths
            )

            if result.returncode != 0:
                # Read log file for details
                log_path = output_dir / tex_path.with_suffix(".log").name
                log_content = log_path.read_text() if log_path.exists() else None

                # Extract error from output
                error_lines = [
                    line for line in result.stdout.split("\n") if line.startswith("!")
                ]
                error_summary = "\n".join(error_lines[:5]) if error_lines else "Unknown error"

                raise CompilationError(
                    f"{self.engine} failed on pass {pass_num}: {error_summary}",
                    log_content=log_content,
                )

        except subprocess.TimeoutExpired:
            raise CompilationError(
                f"{self.engine} timed out after {self.timeout}s on pass {pass_num}"
            )

    def _assert_includes(self, tex_path: Path, output_dir: Path) -> None:
        """Verify required include files exist.

        Args:
            tex_path: Path to .tex file
            output_dir: Output directory where style files should be

        Raises:
            CompilationError: If required files are missing
        """
        style_path = output_dir / "civictable.sty"
        if not style_path.exists():
            # Try to find it in the source directory
            src_style = tex_path.parent / "civictable.sty"
            if not src_style.exists():
                raise CompilationError(
                    f"Missing style file: {style_path}. "
                    "Ensure renderer.render() was called first."
                )

    def _cleanup(self, output_dir: Path, stem: str) -> None:
        """Remove LaTeX auxiliary files.

        Args:
            output_dir: Directory containing auxiliary files
            stem: Base filename (without extension)
        """
        for ext in self.AUX_EXTENSIONS:
            aux_file = output_dir / f"{stem}{ext}"
            if aux_file.exists():
                try:
                    aux_file.unlink()
                    logger.debug(f"Removed {aux_file}")
                except OSError as e:
                    logger.warning(f"Failed to remove {aux_file}: {e}")


def check_latex_available(engine: str = "xelatex") -> tuple[bool, str]:
    """Check if LaTeX is available and return status message.

    Args:
        engine: LaTeX engine to check

    Returns:
        Tuple of (is_available, status_message)
    """
    compiler = DossierCompiler(engine=engine)

    if compiler.is_available():
        return True, f"{engine} is available"
    else:
        return False, (
            f"{engine} not found. To install:\n"
            "  macOS: brew install basictex  (minimal, ~100MB)\n"
            "         OR download MacTeX from https://tug.org/mactex/\n"
            "  Linux: sudo apt install texlive-xetex\n"
            "  Windows: Install MiKTeX from https://miktex.org/"
        )
