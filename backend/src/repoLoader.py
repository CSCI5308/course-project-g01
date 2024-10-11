import os
import git

from configuration import Configuration
from utils.progress import Progress


def getRepo(config: Configuration):

    # build path
    repoPath = os.path.join(
        config.repositoryPath,
        "{}.{}".format(config.repositoryOwner, config.repositoryName),
    )

    # get repository reference
    repo = None
    if not os.path.exists(repoPath):
        print("Downloading repository...")
        repo = git.Repo.clone_from(
            config.repositoryUrl,
            repoPath,
            progress=Progress(),
            odbt=git.GitCmdObjectDB,
        )
        print()
    else:
        repo = git.Repo(repoPath, odbt=git.GitCmdObjectDB)

    return repo
