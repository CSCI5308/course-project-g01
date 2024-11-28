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
    aliasPath = os.path.join(config.repositoryPath, "aliases.yml")

    # quick lowercase and trim if no alias file
    if aliasPath is None or not os.path.exists(aliasPath):
        return commits

    # read aliases
    content = ""
    with open(aliasPath, "r", encoding="utf-8-sig") as file:
        content = file.read()

    aliases = yaml.load(content, Loader=yaml.FullLoader)
    if aliases is None:
        return commits

    # transpose for easy replacements
    transposesAliases = {}
    for alias in aliases:
        for email in aliases[alias]:
            transposesAliases[email] = alias

    # replace all author aliases with a unique one
    return replaceAll(commits, transposesAliases)


def replaceAll(commits, aliases) -> Generator[git.Commit, None, None]:
    for commit in list(commits):
        copy = commit
        author = author_id_extractor(commit.author)

        if author in aliases:
            copy.author.email = aliases[author]

        yield copy
