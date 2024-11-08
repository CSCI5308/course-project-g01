import os
import sys

import pytest

from MLbackend.validations import (InvalidInputError, validate_email,
                                   validate_pat, validate_url)

# Add the project directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))


def test_validate_url():
    with pytest.raises(InvalidInputError):
        validate_url("invalid_url")


def test_validate_email():
    with pytest.raises(InvalidInputError):
        validate_email("invalid_email")


def test_validate_pat():
    with pytest.raises(ValueError):
        validate_pat("invalid_pat!")
