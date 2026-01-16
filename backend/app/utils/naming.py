import re


def generate_corporate_email(full_name: str, domain: str = "teplocentral.org") -> str:
    parts = [part for part in re.split(r"\s+", full_name.strip()) if part]
    if len(parts) >= 3:
        first, middle, last = parts[0], parts[1], parts[2]
        local = f"{first[0]}.{middle[0]}.{last}"
    elif len(parts) == 2:
        first, last = parts[0], parts[1]
        local = f"{first[0]}.{last}"
    elif parts:
        local = parts[0]
    else:
        local = "user"
    return f"{local.lower()}@{domain}"
