import csv
import io
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "solve.py"


@pytest.fixture
def cli_files(tmp_path):
    """Создать входные CSV для проверки полного запуска программы."""
    entities_path = tmp_path / "entities.csv"
    edges_path = tmp_path / "edges.csv"

    entities_path.write_text(
        "id,type,name\n"
        'P1,person,"Иванов, ""Иван"""\n'
        "P2,person,Петров\n"
        "P3,person,Сидоров\n"
        "P4,person,Орлов\n"
        "C1,company,Альфа\n"
        "C2,company,Цель\n"
        "C3,company,Другая компания\n",
        encoding="utf-8",
    )

    edges_path.write_text(
        "owner_id,owned_id,share\n"
        "P1,C1,0.5\n"
        "C1,C2,0.4\n"
        "P1,C2,0.1\n"
        "P2,C2,0.35\n"
        "P3,C2,0.05\n"
        "P4,C2,0.04999999999999\n"
        "P1,C3,0.9\n"
        "P4,C2,1.2\n",
        encoding="utf-8",
    )

    return entities_path, edges_path


def run_cli(entities_path, edges_path, *, target="C2"):
    """Запустить CLI тем же Python, которым запущен pytest."""
    return subprocess.run(
        [
            sys.executable,
            "-B",
            str(SCRIPT),
            "--entities",
            str(entities_path),
            "--edges",
            str(edges_path),
            "--target",
            target,
            "--threshold",
            "0.05",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
    )


def test_cli_outputs_filtered_sorted_csv(cli_files):
    """Проверить расчёт, порог, CSV и отделение предупреждений от результата."""
    result = run_cli(*cli_files)

    assert result.returncode == 0, result.stderr

    reader = csv.DictReader(io.StringIO(result.stdout))
    rows = list(reader)

    assert reader.fieldnames == ["person_id", "name", "effective_share"]
    assert [row["person_id"] for row in rows] == ["P2", "P1", "P3"]

    assert [float(row["effective_share"]) for row in rows] == pytest.approx(
        [0.35, 0.3, 0.05]
    )

    assert rows[1]["name"] == 'Иванов, "Иван"'

    assert "WARNING:" in result.stderr
    assert "WARNING:" not in result.stdout


def test_cli_reports_unknown_target(cli_files):
    """Неизвестная цель даёт ошибку в stderr и не создаёт CSV-результат."""
    result = run_cli(*cli_files, target="UNKNOWN")

    assert result.returncode == 1
    assert result.stdout == ""
    assert "UNKNOWN" in result.stderr
    assert "не найдена" in result.stderr
    assert "Traceback" not in result.stderr
