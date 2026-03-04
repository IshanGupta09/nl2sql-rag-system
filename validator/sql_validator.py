

def validate_sql(sql: str) -> bool:
    """
    Basic safety filter.
    Prevent destructive queries.
    """

    forbidden = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER"]

    for word in forbidden:
        if word in sql.upper():
            return False

    return True
