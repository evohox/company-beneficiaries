import math
import warnings
import numpy as np
from collections import defaultdict
from scipy.sparse import csc_matrix, eye
from scipy.sparse.linalg import MatrixRankWarning, spsolve

from models import Edge


def build_company_matrix(
    relevant: set[str],
    edges: list[Edge],
) -> tuple[csc_matrix, dict[str, int]]:
    """Построить матрицу прямого владения между компаниями.

    Строка — владелец, столбец — компания владения.
    """
    index = {
        company_id: position for position, company_id in enumerate(sorted(relevant))
    }

    rows: list[int] = []
    cols: list[int] = []
    shares: list[float] = []

    for edge in edges:
        if edge.owner_id not in index:
            continue

        rows.append(index[edge.owner_id])
        cols.append(index[edge.owned_id])
        shares.append(edge.share)

    size = len(index)

    matrix = csc_matrix((shares, (rows, cols)), shape=(size, size), dtype=float)

    return matrix, index


def calculate_effective_shares(
    relevant: set[str],
    edges: list[Edge],
    target: str,
) -> dict[str, float]:
    """Рассчитать эффективные доли физических лиц в целевой компании.

    Вырожденная система или недопустимый численный результат
    вызывают ValueError.
    """

    if target not in relevant:
        raise ValueError(f"Целевая компания {target!r} отсутствует в подграфе")

    ownership, index = build_company_matrix(relevant, edges)
    size = len(index)

    system = eye(size, format="csc") - ownership

    rhs = np.zeros(size, dtype=float)
    rhs[index[target]] = 1.0

    # SciPy может сообщить о вырожденной матрице предупреждением.
    # Превращаем его в исключение, чтобы остановить расчёт.
    with warnings.catch_warnings():
        warnings.simplefilter("error", MatrixRankWarning)

        try:
            weights = spsolve(system, rhs)
        except MatrixRankWarning as exc:
            raise ValueError(
                "Система владения вырождена: " "невозможно получить однозначное решение"
            ) from exc

    if not np.all(np.isfinite(weights)):
        raise ValueError("Расчёт дал бесконечные или неопределённые коэффициенты")

    # Коэффициенты представляют суммы неотрицательных вкладов.
    # Отрицательный результат нельзя использовать как долю владения.
    if np.any(weights < 0):
        raise ValueError(
            "Получены отрицательные коэффициенты: "
            "проверьте циклы владения и численную устойчивость"
        )

    if not np.allclose(system @ weights, rhs, rtol=1e-9, atol=1e-12):
        raise ValueError("Решение не удовлетворяет системе с нужной точностью")

    contributions: dict[str, list[float]] = defaultdict(list)

    for edge in edges:
        if edge.owner_id in index:
            continue

        company_weight = weights[index[edge.owned_id]]
        contribution = edge.share * company_weight

        contributions[edge.owner_id].append(contribution)

    result: dict[str, float] = {}

    for person_id, parts in contributions.items():
        total = math.fsum(parts)

        if total > 0:
            result[person_id] = total

    return result
