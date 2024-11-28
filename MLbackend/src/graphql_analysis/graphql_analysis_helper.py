import random
import time
from logging import Logger

import requests


def build_next_page_query(cursor: str):
    if cursor is None:
        return ""
    return ', after:"{0}"'.format(cursor)


def run_graphql_request(pat: str, query: str, logger: Logger):
    headers = {"Authorization": "Bearer {0}".format(pat)}

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
    raise Exception(
        "Query execution failed with code {0}: {1}".format(
            request.status_code, request.text
        )
    )


def add_login(node, authors: list):
    login = extract_author_login(node)

    if login is not None:
        authors.append(login)


def extract_author_login(node):
    if node is None or "login" not in node or node["login"] is None:
        return None

    return node["login"]
