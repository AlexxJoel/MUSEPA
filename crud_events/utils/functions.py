from datetime import datetime


# Serializador de tipos de dato datetime
def datetime_serializer(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


# Para funciones que consulten un array
def serialize_rows(rows, cursor):
    serialized_rows = []
    for row in rows:
        # Obtener nombres de columnas del cursor
        column_names = [desc[0] for desc in cursor.description]
        # Convertir la tupla a un diccionario
        serialized_row = dict(zip(column_names, row))
        # Agregar al array
        serialized_rows.append(serialized_row)
    return serialized_rows


# Para funciones que consulten un solo objeto
def serialize_row(row, cursor):
    if row is not None:
        # Obtener nombres de columnas del cursor
        column_names = [desc[0] for desc in cursor.description]
        # Convertir la tupla a un diccionario
        serialized_row = dict(zip(column_names, row))
        return serialized_row
    else:
        return None
