from django.core.cache import caches


OTP_EXPIRY = 60
cache = caches["otp_database"]

def get_otp_key(email):
    return f"otp:{email.lower()}"


def save_otp(email, otp):
    key = get_otp_key(email)

    cache.set(
        key,
        str(otp),
        timeout=OTP_EXPIRY
    )


def get_otp(email):
    key = get_otp_key(email)

    return cache.get(key)


def delete_otp(email):
    key = get_otp_key(email)

    cache.delete(key)


def get_otp_ttl(email):
    key = get_otp_key(email)

    return cache.ttl(key)