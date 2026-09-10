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
