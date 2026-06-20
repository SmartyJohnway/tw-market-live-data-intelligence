def safe_parse_float(value, flags, field_name):
    if value is None:
        return None
    val_str = str(value).strip().replace(',', '')
    if val_str in ('', '-', '--', '---'):
        return None
    try:
        return float(val_str)
    except ValueError:
        flags.append(f"malformed_{field_name}")
        return None

def safe_parse_int(value, flags, field_name):
    if value is None:
        return None
    val_str = str(value).strip().replace(',', '')
    if val_str in ('', '-', '--', '---'):
        return None
    try:
        return int(float(val_str))
    except ValueError:
        flags.append(f"malformed_{field_name}")
        return None
