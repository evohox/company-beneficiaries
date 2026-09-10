from scipy.sparse import csc_matrix

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
