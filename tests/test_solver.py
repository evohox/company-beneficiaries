import numpy as np
import pytest

from models import Edge
from solver import build_company_matrix, calculate_effective_shares


def test_build_company_matrix_maps_ownership_correctly():
    """Проверить направление связей, самовладение и исключение физлиц."""
    edges = [
        Edge("P1", "C1", 0.5),
        Edge("C1", "C2", 0.4),
        Edge("C2", "C1", 0.2),
        Edge("C1", "C1", 0.1),
    ]

    matrix, index = build_company_matrix(
        relevant={"C1", "C2"},
        edges=edges,
    )

    assert index == {"C1": 0, "C2": 1}

    np.testing.assert_allclose(
        matrix.toarray(),
        [
            [0.1, 0.4],
            [0.2, 0.0],
        ],
    )


def test_calculate_effective_shares_combines_direct_and_indirect_ownership():
    """Прямые и косвенные вклады каждого человека складываются."""
    edges = [
        Edge("P1", "C1", 0.5),
        Edge("P2", "C1", 0.5),
        Edge("C1", "C2", 0.4),
        Edge("P1", "C2", 0.1),
    ]

    result = calculate_effective_shares(
        relevant={"C1", "C2"},
        edges=edges,
        target="C2",
    )

    assert result == pytest.approx(
        {"P1": 0.3, "P2": 0.2},
        rel=1e-9,
        abs=1e-12,
    )


def test_calculate_effective_shares_handles_mutual_ownership():
    """Взаимное владение учитывается при расчёте доли человека."""
    edges = [
        Edge("P1", "C1", 0.5),
        Edge("P1", "C2", 0.5),
        Edge("C1", "C2", 0.5),
        Edge("C2", "C1", 0.5),
    ]

    result = calculate_effective_shares(
        relevant={"C1", "C2"},
        edges=edges,
        target="C2",
    )

    assert result == pytest.approx(
        {"P1": 1.0},
        rel=1e-9,
        abs=1e-12,
    )


def test_calculate_effective_shares_rejects_singular_system():
    """Вырожденная система вызывает ошибку согласно выбранной политике."""
    edges = [
        Edge("C1", "C1", 1.0),
    ]

    with pytest.raises(ValueError, match="вырождена"):
        calculate_effective_shares(
            relevant={"C1"},
            edges=edges,
            target="C1",
        )
