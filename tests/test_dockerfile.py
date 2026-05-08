"""Static sanity checks for the Dockerfile.

Locks in the dependency-install hygiene fixes:
- Uses ``pip install ".[test]"`` (project-aware) rather than ad-hoc
  ``pip install colorama pytest``.
- Passes ``--root-user-action=ignore`` so the build log no longer prints
  the ``Running pip as the 'root' user`` warning on every build.

A live ``docker build`` test would be the gold standard backstop but is
too slow for unit tests; CI's docker job (in .github/workflows/ci.yml) is
the live integration check.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCKERFILE = REPO_ROOT / "Dockerfile"


def test_dockerfile_uses_project_install() -> None:
    text = DOCKERFILE.read_text()
    assert 'pip install --no-cache-dir' in text
    assert '".[test]"' in text, (
        "Dockerfile should install via the project's [test] extra "
        "to keep deps aligned with pyproject.toml"
    )


def test_dockerfile_suppresses_root_user_warning() -> None:
    """Each ``pip install`` line must opt out of the root-user-action warning."""

    text = DOCKERFILE.read_text()
    pip_lines = [
        line for line in text.splitlines()
        if "pip install" in line and not line.lstrip().startswith("#")
    ]
    assert pip_lines, "expected at least one pip install command in Dockerfile"
    for line in pip_lines:
        assert "--root-user-action=ignore" in line, (
            f"pip install line missing --root-user-action=ignore: {line.strip()}"
        )


def test_dockerfile_pins_python_base_to_3_13() -> None:
    text = DOCKERFILE.read_text()
    assert "FROM python:3.13-slim" in text, (
        "Base image should be python:3.13-slim to match the project's "
        "requires-python floor"
    )


def test_dockerfile_does_not_install_analysis_libs_at_runtime() -> None:
    """The runtime image is intentionally lean — heavy analysis libs
    (pandas/numpy/scipy/matplotlib/seaborn) are NOT installed in the
    runtime container; they live behind the ``[analysis]`` extra for
    local-dev use only."""

    text = DOCKERFILE.read_text()
    for lib in ("pandas", "numpy", "scipy", "matplotlib", "seaborn"):
        # Allow the lib name in comments, just not in an actual install line.
        for line in text.splitlines():
            if line.lstrip().startswith("#"):
                continue
            assert lib not in line, (
                f"runtime Dockerfile should not install {lib!r}: {line.strip()}"
            )
