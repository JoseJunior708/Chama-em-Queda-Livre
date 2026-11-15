
from sqlalchemy import inspect


def serialize_model(instance, include_relationships=False):
    """
    Converte uma instância SQLAlchemy num dicionário Python.
    """
    if instance is None:
        return None

    state = inspect(instance)

    result = {
        column.key: getattr(instance, column.key)
        for column in state.mapper.column_attrs
    }

    if include_relationships:
        for relationship in state.mapper.relationships:
            value = getattr(instance, relationship.key)

            if relationship.uselist:
                result[relationship.key] = [
                    serialize_model(item, include_relationships=False)
                    for item in value
                ]
            elif value is not None:
                result[relationship.key] = serialize_model(
                    value,
                    include_relationships=False
                )
            else:
                result[relationship.key] = None

    return result
