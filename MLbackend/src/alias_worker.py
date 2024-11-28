import os
from logging import Logger
from typing import Generator, List

import git
import yaml

from MLbackend.src.configuration import Configuration
from MLbackend.src.utils import author_id_extractor


def replace_aliases(
    commits: List[git.Commit], config: Configuration, logger: Logger
) -> Generator[git.Commit, None, None]:

    logger.info("Cleaning aliased authors")

    # build path
    alias_path = os.path.join(config.repository_path, "aliases.yml")

    # quick lowercase and trim if no alias file
    if not os.path.exists(alias_path):
        return commits

    # read aliases
    content = ""
    with open(alias_path, "r", encoding="utf-8-sig") as file:
        content = file.read()

    aliases = yaml.load(content, Loader=yaml.FullLoader)
    if aliases is None:
        return commits

    # transpose for easy replacements
    transposes_aliases = {}
    for alias in aliases:
        for email in aliases[alias]:
            transposes_aliases[email] = alias

    # replace all author aliases with a unique one
    return replace_all(commits, transposes_aliases)


def replace_all(commits, aliases) -> Generator[git.Commit, None, None]:
    for commit in list(commits):
        copy = commit
        author = author_id_extractor(commit.author)

        if author in aliases:
            copy.author.email = aliases[author]

        yield copy
