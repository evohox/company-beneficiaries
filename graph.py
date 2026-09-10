from models import Entity, Edge


def build_incoming(
    entities: dict[str, Entity],
    edges: list[Edge],
) -> dict[str, list[Edge]]:
    """Сгруппировать проверенные связи по компании владения."""
    # Сохраняем в графе и компании без известных владельцев.
    incoming: dict[str, list[Edge]] = {
        entity_id: []
        for entity_id, entity in entities.items()
        if entity.type == "company"
    }

    for edge in edges:
        incoming[edge.owned_id].append(edge)

    return incoming


def collect_relevant_companies(
    incoming: dict[str, list[Edge]],
    target: str,
) -> set[str]:
    """Найти целевую компанию и всех её компаний-владельцев.

    Учитывает прямое и косвенное владение.
    Физлица в возвращаемое множество не входят.
    """
    if target not in incoming:
        raise ValueError(f"Целевая компания {target!r} не найдена")

    relevant = {target}

    stack = [target]

    while stack:
        company_id = stack.pop()
        for edge in incoming[company_id]:
            owner_id = edge.owner_id

            # В incoming есть ключи для всех компаний.
            # Физлица ключами не являются: дальше по ним не идём.
            if owner_id not in incoming:
                continue

            if owner_id in relevant:
                continue

            relevant.add(owner_id)
            stack.append(owner_id)

    return relevant


def prepare_target_edges(
    incoming: dict[str, list[Edge]], relevant: set[str]
) -> list[Edge]:
    """Подготовить связи компаний из выбранного подграфа.

    Одинаковые записи учитываются один раз.
    Разные доли для одной пары владелец-компания
    вызывают ValueError.
    """

    unique: dict[tuple[str, str], Edge] = {}

    for company_id in sorted(relevant):
        for edge in incoming[company_id]:
            key = (edge.owner_id, edge.owned_id)

            previous = unique.get(key)

            if previous is None:
                unique[key] = edge
                continue

            if previous.share != edge.share:
                raise ValueError(
                    f"Противоречивые доли для связи "
                    f"{edge.owner_id!r} -> {edge.owned_id!r}: "
                    f"{previous.share} и {edge.share}"
                )

    return list(unique.values())
