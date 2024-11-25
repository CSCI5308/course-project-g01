import os
from logging import Logger

import git

from MLbackend.src.configuration import Configuration


def getRepo(config: Configuration, logger: Logger):
    repoPath = os.path.join(
        config.repositoryPath,
        "{}.{}".format(config.repositoryOwner, config.repositoryName),
    )

    # Reference from https://docs.readthedocs.io/en/stable/guides/private-python-packages.html
    pat = config.pat or os.getenv("GITHUB_TOKEN")

    repoUrl = config.repositoryUrl.replace("https://", f"https://{pat}@")

    repo = None
    try:
        if not os.path.exists(repoPath):
            logger.info(f"Repository path does not exist. Cloning from {repoUrl}")
            repo = git.Repo.clone_from(
                repoUrl,
                repoPath,
                odbt=git.GitCmdObjectDB,
            )
            logger.info(f"Cloned repository from {repoUrl}")
        else:
            repo = git.Repo(repoPath, odbt=git.GitCmdObjectDB)
            logger.info(f"Repository already cloned from {repoUrl}")
    except git.exc.GitCommandError as e:
        logger.error(f"Failed to clone or open repository: {e}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return None

    return repo
