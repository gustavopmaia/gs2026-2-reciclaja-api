"""Gate de regressão no CI: o conjunto de avaliação roda com o fake e precisa bater as metas."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_evals_com_fake_aprovam_todas_as_metas(tmp_path):
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(ROOT / "evals" / "run_evals.py")],
        capture_output=True,
        text=True,
        env={"LLM_PROVIDER": "fake", "PATH": ""},
        check=False,
    )
    assert result.returncode == 0, result.stdout[-2000:]
    assert '"fase_liberada": "publico"' in result.stdout
