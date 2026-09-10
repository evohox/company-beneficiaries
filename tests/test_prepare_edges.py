import pytest

from graph import prepare_target_edges
from models import Edge


def test_prepare_target_edges_removes_only_exact_duplicates():
    """Дубли удаляются, разные владельцы и компании сохраняются."""
    first = Edge("P1", "C1", 0.4)
    second = Edge("P2", "C1", 0.4)
    third = Edge("P1", "C2", 0.2)

    incoming = {
        "C1": [
            first,
            Edge("P1", "C1", 0.4),
            second,
        ],
        "C2": [third],
    }

    result = prepare_target_edges(
        incoming,
        relevant={"C1", "C2"},
    )

    assert result == [first, second, third]


def test_prepare_target_edges_rejects_conflicting_shares():
    """Разные доли одной пары в нужном подграфе вызывают ошибку."""
    incoming = {
        "C1": [
            Edge("P1", "C1", 0.4),
            Edge("P1", "C1", 0.6),
        ],
    }

    with pytest.raises(ValueError, match="Противоречивые доли"):
        prepare_target_edges(
            incoming,
            relevant={"C1"},
        )


def test_prepare_target_edges_ignores_unrelated_conflicts():
    """Конфликт вне выбранного подграфа не влияет на результат."""
    valid_edge = Edge("P1", "C1", 0.5)

    incoming = {
        "C1": [valid_edge],
        "C2": [
            Edge("P2", "C2", 0.3),
            Edge("P2", "C2", 0.7),
        ],
    }

    result = prepare_target_edges(
        incoming,
        relevant={"C1"},
    )

    assert result == [valid_edge]
