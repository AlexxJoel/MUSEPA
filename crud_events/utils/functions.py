from datetime import datetime


def datetime_serializer(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def serialize_rows(rows, cursor):
    serialized_rows = []
    for row in rows:
        # Obtener nombres de columnas del cursor
        column_names = [desc[0] for desc in cursor.description]
        # Convertir la tupla a un diccionario
        serialized_row = dict(zip(column_names, row))
        # Convertir valores de fecha a formato isoformat
        serialized_row = {k: (v.isoformat() if isinstance(v, datetime) else v) for k, v in serialized_row.items()}
        serialized_rows.append(serialized_row)
    return serialized_rows
