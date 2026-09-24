import re


def create_product_key(
    brand,
    name,
    package_quantity,
    package_unit
):

    value = (
        f"{brand.strip().lower()}-"
        f"{name.strip().lower()}-"
        f"{package_quantity}-"
        f"{package_unit.strip().lower()}"
    )

    value = re.sub(
        r"[^a-z0-9]+",
        "-",
        value
    )

    return value.strip("-")