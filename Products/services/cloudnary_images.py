from cloudinary.utils import cloudinary_url


def get_pr_small_url(public_id):
    url, _ = cloudinary_url(
        public_id,
        width=140,
        height=140,
        crop="fit",
        quality="auto",
        fetch_format="auto",
    )

    return url

def get_small_image(public_id):
    url, _ = cloudinary_url(
        public_id,
        width=300,
        height=300,
        crop="fit",
        quality="auto",
        fetch_format="auto",
    )

    return url


def get_medium_image(public_id):
    url, _ = cloudinary_url(
        public_id,
        width=400,
        height=400,
        crop="fit",
        quality="auto",
        fetch_format="auto",
    )

    return url


def get_large_image(public_id):
    url, _ = cloudinary_url(
        public_id,
        width=600,
        height=600,
        crop="fit",
        quality="auto",
        fetch_format="auto",
    )

    return url