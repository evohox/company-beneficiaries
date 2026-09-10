import pytest

from graph import collect_relevant_companies
from models import Edge


@pytest.mark.parametrize(
    "incoming, target, expected",
    [
        pytest.param(
            {
                "C1": [Edge("P1", "C1", 1.0)],
                "C2": [Edge("C1", "C2", 0.5)],
                "C3": [Edge("P2", "C3", 1.0)],
            },
            "C2",
            {"C1", "C2"},
            id="chain-with-unrelated-company",
        ),
        pytest.param(
            {
                "C1": [],
                "C2": [Edge("C1", "C2", 0.5)],
                "C3": [Edge("C1", "C3", 0.5)],
                "C4": [
                    Edge("C2", "C4", 0.4),
                    Edge("C3", "C4", 0.3),
                ],
            },
            "C4",
            {"C1", "C2", "C3", "C4"},
            id="two-branches-with-common-owner",
        ),
        pytest.param(
            {
                "C1": [Edge("C2", "C1", 0.5)],
                "C2": [Edge("C1", "C2", 0.5)],
            },
            "C2",
            {"C1", "C2"},
            id="mutual-ownership",
        ),
        pytest.param(
            {
                "C1": [Edge("C1", "C1", 0.1)],
            },
            "C1",
            {"C1"},
            id="self-ownership",
        ),
        pytest.param(
            {
                "C1": [],
            },
            "C1",
            {"C1"},
            id="company-without-owners",
        ),
    ],
)
def test_collect_relevant_companies(incoming, target, expected):
    """Проверить состав найденных компаний для разных графов."""
    result = collect_relevant_companies(incoming, target)

    assert result == expected


def test_collect_relevant_companies_rejects_unknown_target():
    """Отсутствующая цель должна вызывать понятную ошибку."""
    incoming = {"C1": []}

    with pytest.raises(ValueError, match="Целевая компания"):
        collect_relevant_companies(incoming, target="C404")


def test_collect_relevant_companies_handles_long_chain():
    """Обход должен проходить цепочку из 2000 компаний."""
    length = 2000

    incoming = {
        "C0": [Edge("P1", "C0", 1.0)],
    }

    # Каждая предыдущая компания владеет следующей:
    # P1 → C0 → C1 → ... → C1999.
    for i in range(1, length):
        owner_id = f"C{i - 1}"
        owned_id = f"C{i}"
        incoming[owned_id] = [
            Edge(owner_id, owned_id, 1.0),
        ]

    result = collect_relevant_companies(
        incoming,
        target=f"C{length - 1}",
    )

    assert result == {f"C{i}" for i in range(length)}
