def normalize_names(values):
    """Normalize string names, skipping None and rejecting other non-strings."""
    result = []
    seen = set()
    for value in values:
        if value is None:
            continue
        if not isinstance(value, str):
            raise TypeError("normalize_names entries must be strings or None")
        name = value.strip()
        if not name:
            continue
        key = name
        if key in seen:
            continue
        seen.add(key)
        result.append(name)
    return result
