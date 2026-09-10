import pytest

from graph import build_incoming
from models import Edge, Entity


@pytest.fixture
def entities():
    """Справочник с двумя людьми и двумя компаниями."""
    return {
        "P1": Entity(id="P1", type="person", name="Иванов"),
        "P2": Entity(id="P2", type="person", name="Петров"),
        "C1": Entity(id="C1", type="company", name="Альфа"),
        "C2": Entity(id="C2", type="company", name="Бета"),
    }


def test_build_incoming_groups_multiple_owners(entities):
    """Все владельцы одной компании должны попасть в её список."""
    first = Edge(owner_id="P1", owned_id="C1", share=0.3)
    second = Edge(owner_id="P2", owned_id="C1", share=0.7)

    incoming = build_incoming(entities, [first, second])

    assert incoming["C1"] == [first, second]


def test_build_incoming_separates_companies(entities):
    """Связи должны группироваться по owned_id."""
    first = Edge(owner_id="P1", owned_id="C1", share=0.5)
    second = Edge(owner_id="P1", owned_id="C2", share=0.4)

    incoming = build_incoming(entities, [first, second])

    # Один человек владеет разными компаниями:
    # каждая связь должна оказаться у своей компании.
    assert incoming == {
        "C1": [first],
        "C2": [second],
    }


def test_build_incoming_keeps_companies_without_owners(entities):
    """Даже при отсутствии связей компании остаются в графе."""
    incoming = build_incoming(entities, [])

    # Физлица не получают списков входящих связей.
    assert incoming == {
        "C1": [],
        "C2": [],
    }


def test_build_incoming_preserves_self_ownership(entities):
    """Самовладение должно сохраняться как обычная связь."""
    edge = Edge(owner_id="C1", owned_id="C1", share=0.1)

    incoming = build_incoming(entities, [edge])

    assert incoming["C1"] == [edge]


def test_build_incoming_preserves_mutual_ownership(entities):
    """Обе связи взаимного владения должны остаться в графе."""
    first = Edge(owner_id="C1", owned_id="C2", share=0.4)
    second = Edge(owner_id="C2", owned_id="C1", share=0.3)

    incoming = build_incoming(entities, [first, second])

    # C2 владеет C1, поэтому second находится под ключом C1.
    # C1 владеет C2, поэтому first находится под ключом C2.
    assert incoming == {
        "C1": [second],
        "C2": [first],
    }
