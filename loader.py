import math
import csv
from pathlib import Path

from models import Entity, Edge


def load_entities(path: str | Path) -> dict[str, Entity]:
    """Загрузить сущности из CSV в словарь по ID.

    Удаляет пробелы по краям значений.
    При неверной структуре или недопустимых значениях
    записей выбрасывает ValueError.
    """
    path = Path(path)
    entities: dict[str, Entity] = {}

    # utf-8-sig поддерживает UTF-8 с BOM и без него.
    # newline="" оставляет обработку переносов строк CSV-парсеру.
    with path.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file, strict=True)
        columns = reader.fieldnames

        # Порядок колонок может отличаться, но их состав и количество
        # должны совпадать с ожидаемыми. Проверка количества выявляет и дубли.
        if (
            columns is None
            or len(columns) != 3
            or set(columns) != {"id", "type", "name"}
        ):
            raise ValueError(f"{path}: ожидаются колонки id,type,name")

        for row in reader:
            location = f"{path}, строка {reader.line_num}"

            # DictReader помещает лишние поля под ключ None,
            # а отсутствующие поля заполняет значением None.
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"{location}: неверное число полей")

            # Нормализуем значения до валидации, чтобы "P1" и " P1 "
            # считались одним идентификатором.
            entity_id = row["id"].strip()
            entity_type = row["type"].strip()
            entity_name = row["name"].strip()

            if not entity_id:
                raise ValueError(f"{location}: пустой id")

            if entity_type not in {"person", "company"}:
                raise ValueError(f"{location}: неизвестный type {entity_type!r}")

            if not entity_name:
                raise ValueError(f"{location}: пустое имя")

            # Повторный ID считаем ошибкой, чтобы не перезаписать
            # ранее загруженную сущность без предупреждения.
            if entity_id in entities:
                raise ValueError(f"{location}: повторный id {entity_id!r}")

            entities[entity_id] = Entity(
                id=entity_id,
                type=entity_type,
                name=entity_name,
            )

    return entities


def load_edges(
    path: str | Path,
    entities: dict[str, Entity],
) -> list[Edge]:
    """Загрузить проверенные связи владения из CSV.

    Некорректные записи вызывают ValueError.
    Нулевые доли пропускаются, самовладение сохраняется.
    """

    path = Path(path)
    edges: list[Edge] = []

    # Поддерживаем UTF-8 с BOM и без него.
    # Обработку переносов строк оставляем CSV-парсеру.
    with path.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file, strict=True)
        columns = reader.fieldnames

        # Порядок колонок не важен, но их состав и количество
        # должны совпадать с ожидаемыми.
        if (
            columns is None
            or len(columns) != 3
            or set(columns) != {"owner_id", "owned_id", "share"}
        ):
            raise ValueError(f"{path}: ожидаются колонки owner_id,owned_id,share")

        for row in reader:
            location = f"{path}, строка {reader.line_num}"

            # Лишние поля DictReader помещает под ключ None,
            # отсутствующие поля заполняет значением None.
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"{location}: неверное число полей")

            # Удаляем пробелы до поиска ID и преобразования доли.
            owner_id = row["owner_id"].strip()
            owned_id = row["owned_id"].strip()
            raw_share = row["share"].strip()

            # Проверяем существование ID до обращения
            # к соответствующим объектам в словаре.
            if owner_id not in entities:
                raise ValueError(f"{location}: неизвестный владелец {owner_id!r}")

            if owned_id not in entities:
                raise ValueError(
                    f"{location}: неизвестный объект владения {owned_id!r}"
                )

            # Владельцем может быть человек или компания,
            # объектом владения — только компания.
            if entities[owned_id].type != "company":
                raise ValueError(
                    f"{location}: объект владения {owned_id!r} "
                    f"должен быть компанией"
                )

            # Преобразование Share из str в float
            try:
                share = float(raw_share)
            except ValueError as exc:
                raise ValueError(
                    f"{location}: доля {raw_share!r} " f"не является числом"
                ) from exc

            # float() принимает NaN и бесконечность,
            # поэтому проверяем конечность отдельно.
            if not math.isfinite(share):
                raise ValueError(f"{location}: доля должна быть конечным числом")

            if not 0 <= share <= 1:
                raise ValueError(
                    f"{location}: доля {share} " f"должна находиться в диапазоне [0, 1]"
                )

            # Нулевая доля допустима, но не влияет на расчёт.
            if share == 0:
                continue

            edges.append(Edge(owner_id=owner_id, owned_id=owned_id, share=share))

    return edges
