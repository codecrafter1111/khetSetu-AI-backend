import random
import string

def generate_partner_id():
    prefix = "RDR"

    random_digits = ''.join(
        random.choices(string.digits, k=6)
    )

    return f"{prefix}{random_digits}"

