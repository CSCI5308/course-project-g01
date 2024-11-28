import os
from logging import Logger

import git

from MLbackend.src.configuration import Configuration


def get_repo(config: Configuration, logger: Logger):
    repo_path = os.path.join(
        config.repository_path,
        "{}.{}".format(config.repository_owner, config.repository_name),
    )

    # Reference from https://docs.readthedocs.io/en/stable/guides/private-python-packages.html
    pat = config.pat or os.getenv("GITHUB_TOKEN")

    repo_url = config.repository_url.replace("https://", f"https://{pat}@")

    repo = None
    try:
        if not os.path.exists(repo_path):
            logger.info(f"Repository path does not exist. Cloning from {repo_url}")
            repo = git.Repo.clone_from(
                repo_url,
                repo_path,
                odbt=git.GitCmdObjectDB,
            )
            logger.info(f"Cloned repository from {repo_url}")
        else:
            repo = git.Repo(repo_path, odbt=git.GitCmdObjectDB)
            logger.info(f"Repository already cloned from {repo_url}")
    except git.exc.GitCommandError as e:
        logger.error(f"Failed to clone or open repository: {e}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return None

    return repo
