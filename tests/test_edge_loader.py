import pytest
import logging

from loader import load_edges
from models import Edge, Entity


@pytest.fixture
def entities():
    """Справочник сущностей для тестирования связей."""
    return {
        "P1": Entity(id="P1", type="person", name="Иванов"),
        "C1": Entity(id="C1", type="company", name="Альфа"),
    }


def test_load_edges_normalizes_and_preserves_valid_edges(tmp_path, entities):
    """Проверить пробелы, пропуск нулей и сохранение самовладения."""
    path = tmp_path / "edges.csv"
    path.write_text(
        "owner_id,owned_id,share\n" " P1 , C1 , 0.5 \n" "P1,C1,0\n" "C1,C1,0.2\n",
        encoding="utf-8-sig",
    )

    edges = load_edges(path, entities)

    # Нулевая связь исключена, остальные сохранились.
    # Связь после нулевой строки тоже должна быть прочитана.
    assert edges == [
        Edge(owner_id="P1", owned_id="C1", share=0.5),
        Edge(owner_id="C1", owned_id="C1", share=0.2),
    ]


def test_load_edges_returns_empty_list_for_zero_share(tmp_path, entities):
    """Нулевая доля допустима, но не создаёт связь в результате."""
    path = tmp_path / "edges.csv"
    path.write_text(
        "owner_id,owned_id,share\n" "P1,C1,0\n",
        encoding="utf-8-sig",
    )

    assert load_edges(path, entities) == []


# Каждый пример содержит одну проблему и ожидаемую причину ошибки.
@pytest.mark.parametrize(
    "row, message",
    [
        ("P404,C1,0.5\n", "неизвестный владелец"),
        ("P1,C404,0.5\n", "неизвестный объект владения"),
        ("C1,P1,0.5\n", "должен быть компанией"),
        ("P1,C1,abc\n", "не является числом"),
        ("P1,C1,NaN\n", "конечным числом"),
        ("P1,C1,inf\n", "конечным числом"),
        ("P1,C1,-inf\n", "конечным числом"),
        ("P1,C1,-0.1\n", "диапазоне"),
        ("P1,C1,1.1\n", "диапазоне"),
        ("P1,C1\n", "неверное число полей"),
        ("P1,C1,0.5,extra\n", "неверное число полей"),
    ],
)
def test_load_edges_rejects_invalid_records(tmp_path, entities, row, message):
    """Некорректная связь должна остановить строгую загрузку."""
    path = tmp_path / "edges.csv"
    path.write_text(
        "owner_id,owned_id,share\n" + row,
        encoding="utf-8-sig",
    )

    # Проверяем причину ошибки, чтобы случайное падение
    # по другой причине не считалось успешным тестом.
    with pytest.raises(ValueError, match=message):
        load_edges(path, entities)


@pytest.mark.parametrize("skip_invalid", [False, True])
def test_load_edges_rejects_wrong_header(tmp_path, entities, skip_invalid):
    """CSV без обязательной колонки share должен быть отклонён."""
    path = tmp_path / "edges.csv"
    path.write_text(
        "owner_id,owned_id\n" "P1,C1\n",
        encoding="utf-8-sig",
    )

    with pytest.raises(ValueError, match="ожидаются колонки"):
        load_edges(
            path,
            entities,
            skip_invalid=skip_invalid,
        )


def test_load_edges_skips_invalid_and_reports(tmp_path, entities, caplog):
    """Ошибочная запись пропускается, следующие связи загружаются."""
    path = tmp_path / "edges.csv"
    path.write_text(
        "owner_id,owned_id,share\n"
        "P1,C1,0.5\n"
        "P1,C1,1.2\n"
        "P1,C1,0\n"
        "C1,C1,0.2\n",
        encoding="utf-8-sig",
    )

    caplog.set_level(logging.INFO, logger="loader")

    result = load_edges(path, entities, skip_invalid=True)

    assert result == [
        Edge("P1", "C1", 0.5),
        Edge("C1", "C1", 0.2),
    ]

    assert "строка 3" in caplog.text
    assert "диапазоне [0, 1]" in caplog.text
    assert "некорректных=1" in caplog.text
    assert "нулевых=1" in caplog.text
