#!/usr/bin/env bash
# Run the same checks as hosted CI locally (see .github/workflows/ci.yml).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHON_VERSION="${PYTHON_VERSION:-3.13}"
RUN_UNIT_TESTS="${RUN_UNIT_TESTS:-1}"
RUN_INTEGRATION="${RUN_INTEGRATION:-0}"
RUN_DOCKER="${RUN_DOCKER:-0}"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required; install from https://docs.astral.sh/uv/" >&2
  exit 1
fi

if [[ "$RUN_UNIT_TESTS" == "1" ]]; then
  uv python install "$PYTHON_VERSION"
  uv sync --all-extras --python "$PYTHON_VERSION"
  uv run --python "$PYTHON_VERSION" pytest -v
fi

if [[ "$RUN_INTEGRATION" == "1" ]]; then
  uv python install 3.13
  uv sync --all-extras
  export PATH="${ROOT}/.venv/bin:${PATH}"
  make test
fi

if [[ "$RUN_DOCKER" == "1" ]]; then
  if ! command -v docker >/dev/null 2>&1; then
    echo "docker is required for RUN_DOCKER=1" >&2
    exit 1
  fi
  docker build -t ants-strategy-agent:ci .
  docker run --rm ants-strategy-agent:ci make test
fi
