import re

import validators

from MLbackend.config import LOGGER


class InvalidInputError(Exception):
    pass


def validate_url(url: str) -> None:
    if not url or not validators.url(url):
        LOGGER.error(f"Invalid repository URL format {url}.")
        raise InvalidInputError("Invalid repository URL format.")


def validate_email(email: str) -> None:
    if not email or not validators.email(email):
        LOGGER.error(f"Invalid Email format {email}.")
        raise InvalidInputError("Invalid email format.")


def validate_pat(token: str) -> None:
    if not re.match(r"^[a-zA-Z0-9-_]+$", token):
        LOGGER.error(f"Invalid PAT format {token}.")
        raise ValueError("Invalid PAT format.")