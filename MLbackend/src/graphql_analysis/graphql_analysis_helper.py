import random
import time
from logging import Logger

import requests
from requests import HTTPError


def build_next_page_query(cursor: str):
    if cursor is None:
        return ""
    return ', after:"{0}"'.format(cursor)


def run_graphql_request(pat: str, query: str, logger: Logger):
    headers = {"Authorization": f"Bearer {pat}"}

    sleep_time = random.randint(0, 8)
    time.sleep(sleep_time)

    request = requests.post(
        "https://api.github.com/graphql", json={"query": query}, headers=headers
    )

    if request.status_code == 200:
        return request.json()["data"]

    logger.error(
        f"Query execution failed with code {request.status_code}: {request.text}."
    )

    # Raising a more specific HTTPError with detailed information
    raise HTTPError(
        f"Query execution failed with code {request.status_code}: {request.text}",
        response=request
    )


def add_login(node, authors: list):
    login = extract_author_login(node)

    if login is not None:
        authors.append(login)


def extract_author_login(node):
    if node is None or "login" not in node or node["login"] is None:
        return None

    return node["login"]
