import numpy as np

from models import Edge
from solver import build_company_matrix


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
