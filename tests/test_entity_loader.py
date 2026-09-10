import pytest

from loader import load_entities


def test_load_entities_normalizes_and_read_csv(tmp_path):
    """Проверить удаление пробелов и чтение имени с CSV-кавычками."""

    # tmp_path — временная папка pytest: тест не меняет исходные CSV.
    path = tmp_path / "entities.scv"
    path.write_text(
        "id,type,name\n" " P1, person , Иванов \n" 'C1,company,"ООО ""Альфа, Бета"""\n',
        encoding="utf-8-sig",
    )

    entities = load_entities(path)

    assert set(entities) == {"P1", "C1"}
    assert entities["P1"].type == "person"
    assert entities["P1"].name == "Иванов"
    assert entities["C1"].type == "company"
    assert entities["C1"].name == 'ООО "Альфа, Бета"'


# Каждая пара задаёт отдельный случай:
# содержимое строк CSV и ожидаемый фрагмент сообщения об ошибке.
@pytest.mark.parametrize(
    "rows, message",
    [
        (",person,Иванов\n", "пустой id"),
        ("P1,unknown,Иванов\n", "неизвестный type"),
        ("P1,person,\n", "пустое имя"),
        ("P1,person\n", "неверное число полей"),
        (
            "P1,person,Иванов\n P1 ,person,Петров\n",
            "повторный id",
        ),
    ],
)
def test_load_entities_rejects_invalid_records(tmp_path, rows, message):
    """Проверить отклонение некорректных записей с понятной причиной."""
    path = tmp_path / "entities.scv"
    path.write_text(
        "id,type,name\n" + rows,
        encoding="utf-8-sig",
    )

    # Проверяем и тип исключения, и причину ошибки:
    # падение по другой причине не должно считаться успехом теста.
    with pytest.raises(ValueError, match=message):
        load_entities(path)


def test_load_entities_rejects_wrong_header(tmp_path):
    """Проверить отклонение CSV без обязательной колонки type."""
    path = tmp_path / "entities.csv"
    path.write_text(
        "id,name\nP1,Иванов\n",
        encoding="utf-8-sig",
    )

    with pytest.raises(ValueError, match="ожидаются колонки"):
        load_entities(path)
