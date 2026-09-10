import argparse
import csv
import logging
import math
import sys
from pathlib import Path

from graph import build_incoming, collect_relevant_companies, prepare_target_edges
from loader import load_edges, load_entities
from solver import calculate_effective_shares


def parse_args() -> argparse.Namespace:
    """Прочитать и проверить аргументы командной строки."""
    parser = argparse.ArgumentParser(
        description="Рассчитать доли конечных бенефициаров компании."
    )
    parser.add_argument("--entities", type=Path, required=True)
    parser.add_argument("--edges", type=Path, required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--threshold", type=float, default=0.0001)

    args = parser.parse_args()
    args.target = args.target.strip()

    if not args.target:
        parser.error("--target не должен быть пустым")

    if not math.isfinite(args.threshold) or args.threshold < 0:
        parser.error("--threshold должен быть конечным неотрицательным числом")

    return args


def main() -> int:
    args = parse_args()

    # Сообщения отправляем в stderr, чтобы они не попадали в CSV.
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
        stream=sys.stderr,
    )

    try:
        entities = load_entities(args.entities)
        edges = load_edges(args.edges, entities, skip_invalid=True)

        incoming = build_incoming(entities, edges)
        relevant = collect_relevant_companies(incoming, args.target)
        target_edges = prepare_target_edges(incoming, relevant)

        shares = calculate_effective_shares(relevant, target_edges, args.target)

    except (OSError, ValueError, csv.Error) as exc:
        logging.error("%s", exc)
        return 1

    # Сравниваем с порогом до округления при выводе.
    rows = [
        (person_id, entities[person_id].name, share)
        for person_id, share in shares.items()
        if share >= args.threshold
    ]

    # При равных долях порядок задаёт ID: результат воспроизводим.
    rows.sort(key=lambda row: (-row[2], row[0]))

    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow(["person_id", "name", "effective_share"])

    for person_id, name, share in rows:
        writer.writerow([person_id, name, f"{share:.12g}"])

    return 0


if __name__ == "__main__":
    # Задаём UTF-8 для стандартных потоков вывода.
    sys.stdout.reconfigure(encoding="utf-8", newline="")
    sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
