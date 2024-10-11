import os
import shutil
import stat
import git
import sentistrength
from pathlib import Path
from typing import Optional

import testConfig
from configuration import Configuration
from repoLoader import getRepo
from aliasWorker import replaceAliases
from commitAnalysis import commitAnalysis
import centralityAnalysis as centrality
from tagAnalysis import tagAnalysis
from devAnalysis import devAnalysis
from graphqlAnalysis.releaseAnalysis import releaseAnalysis
from graphqlAnalysis.prAnalysis import prAnalysis
from graphqlAnalysis.issueAnalysis import issueAnalysis
from smellDetection import smellDetection
from politenessAnalysis import politenessAnalysis
from dateutil.relativedelta import relativedelta


def communitySmellsDetector(
    pat: str,
    repo_url: str,
    senti_strength_path: Path,
    output_path: Path,
    google_api_key: Optional[str] = None,
    batch_months: float = 9999,
    start_date: Optional[str] = None,
):

    try:

        # parse args
        config: Configuration = Configuration(
            repositoryUrl=repo_url,
            batchMonths=batch_months,
            outputPath=output_path,
            sentiStrengthPath=senti_strength_path,
            maxDistance=0,
            pat=pat,
            googleKey=google_api_key,
            startDate=start_date,
        )

        # prepare folders
        if os.path.exists(config.resultsPath):
            remove_tree(config.resultsPath)

        os.makedirs(config.metricsPath)

        # get repository reference
        repo = getRepo(config)

        # setup sentiment analysis
        senti = sentistrength.PySentiStr()

        senti.setSentiStrengthPath(
            os.path.join(config.sentiStrengthPath, "SentiStrength.jar")
        )

        senti.setSentiStrengthLanguageFolderPath(
            os.path.join(config.sentiStrengthPath, "SentiStrength_Data")
        )

        # prepare batch delta
        delta = relativedelta(months=+config.batchMonths)

        # handle aliases
        commits = list(replaceAliases(repo.iter_commits(), config))

        # run analysis
        batchDates, authorInfoDict, daysActive = commitAnalysis(
            senti, commits, delta, config
        )

        tagAnalysis(repo, delta, batchDates, daysActive, config)

        coreDevs = centrality.centralityAnalysis(commits, delta, batchDates, config)

        releaseAnalysis(commits, config, delta, batchDates)

        prParticipantBatches, prCommentBatches = prAnalysis(
            config,
            senti,
            delta,
            batchDates,
        )

        issueParticipantBatches, issueCommentBatches = issueAnalysis(
            config,
            senti,
            delta,
            batchDates,
        )

        politenessAnalysis(config, prCommentBatches, issueCommentBatches)

        for batchIdx, batchDate in enumerate(batchDates):

            # get combined author lists
            combinedAuthorsInBatch = (
                prParticipantBatches[batchIdx] + issueParticipantBatches[batchIdx]
            )

            # build combined network
            centrality.buildGraphQlNetwork(
                batchIdx,
                combinedAuthorsInBatch,
                "issuesAndPRsCentrality",
                config,
            )

            # get combined unique authors for both PRs and issues
            uniqueAuthorsInPrBatch = set(
                author for pr in prParticipantBatches[batchIdx] for author in pr
            )

            uniqueAuthorsInIssueBatch = set(
                author for pr in issueParticipantBatches[batchIdx] for author in pr
            )

            uniqueAuthorsInBatch = uniqueAuthorsInPrBatch.union(
                uniqueAuthorsInIssueBatch
            )

            # get batch core team
            batchCoreDevs = coreDevs[batchIdx]

            # run dev analysis
            devAnalysis(
                authorInfoDict,
                batchIdx,
                uniqueAuthorsInBatch,
                batchCoreDevs,
                config,
            )

            # run smell detection
            smellDetection(config, batchIdx)

    finally:
        # close repo to avoid resource leaks
        if "repo" in locals():
            del repo


class Progress(git.remote.RemoteProgress):
    def update(self, op_code, cur_count, max_count=None, message=""):
        print(self._cur_line, end="\r")


def commitDate(tag):
    return tag.commit.committed_date


def remove_readonly(fn, path, excinfo):
    os.chmod(path, stat.S_IWRITE)
    remove_tree(path)


def remove_tree(path):
    if os.path.isdir(path):
        shutil.rmtree(path, onerror=remove_readonly)
    else:
        os.remove(path)


if __name__ == "__main__":
    communitySmellsDetector(
        pat=testConfig.PAT,
        repo_url=testConfig.REPO_URL,
        output_path=testConfig.OUTPUT_PATH,
        senti_strength_path=testConfig.SENTI_STRENGTH_PATH,
    )
