import csv
import subprocess
import sys
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parent
TARGETS = ("C900003", "C900012", "C91001999", "C900022", "C025145")
THRESHOLD = 0.0001


def main() -> None:
    results_dir = ROOT / "results"
    results_dir.mkdir(exist_ok=True)

    timings: list[tuple[str, float]] = []

    for target in TARGETS:
        csv_path = results_dir / f"{target}.csv"
        log_path = results_dir / f"{target}.log"

        started = perf_counter()

        # Сохраняем вывод напрямую в файлы.
        with csv_path.open("wb") as output, log_path.open("wb") as log:
            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "solve.py"),
                    "--entities",
                    str(ROOT / "entities.csv"),
                    "--edges",
                    str(ROOT / "edges.csv"),
                    "--target",
                    target,
                    "--threshold",
                    str(THRESHOLD),
                ],
                stdout=output,
                stderr=log,
            )

        elapsed = perf_counter() - started

        if completed.returncode != 0:
            raise SystemExit(f"Ошибка для {target}. Подробности: {log_path}")

        timings.append((target, elapsed))
        print(f"{target}: {elapsed:.3f} s")

    with (results_dir / "timings.csv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["target", "threshold", "elapsed_seconds"])

        for target, elapsed in timings:
            writer.writerow([target, THRESHOLD, f"{elapsed:.6f}"])


if __name__ == "__main__":
    main()
