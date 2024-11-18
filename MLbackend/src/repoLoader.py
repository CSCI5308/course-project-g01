import os
import git
from logging import Logger

from MLbackend.src.configuration import Configuration
from MLbackend.src.utils.progress import Progress


def getRepo(config: Configuration, logger: Logger):

    # build path
    repoPath = os.path.join(
        config.repositoryPath,
        "{}.{}".format(config.repositoryOwner, config.repositoryName),
    )

    # get repository reference
    repo = None
    if not os.path.exists(repoPath):
        logger.info("Downloading repository")
        repo = git.Repo.clone_from(
            config.repositoryUrl,
            repoPath,
            odbt=git.GitCmdObjectDB,
        )
        logger.info(f"Cloned repository from link {config.repositoryUrl}")
    else:
        repo = git.Repo(repoPath, odbt=git.GitCmdObjectDB)
        logger.info(f"Repositroy from link {config.repositoryUrl} is already cloned.")

    return repo
