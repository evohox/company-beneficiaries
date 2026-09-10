import csv
from pathlib import Path

from models import Entity


#
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
