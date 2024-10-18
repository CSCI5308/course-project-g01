
#REPLICA OF devNetwork.py FILE
import sys
import os
import subprocess
import shutil
import stat
import git
import pkg_resources
import sentistrength

from configuration import parseDevNetworkArgs
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


def main(argv):
    try:
        # validate running in venv
        if not hasattr(sys, "prefix"):
            raise Exception(
                "The tool does not appear to be running in the virtual environment!\nSee README for activation."
            )

        # validate python version
        
        # validate installed modules
        required = {
            "wheel",
            "networkx",
            "pandas",
            "matplotlib",
            "gitpython",
            "requests",
            "pyyaml",
            "progress",
            "strsimpy",
            "python-dateutil",
            "sentistrength",
            "joblib",
        }
        installed = {pkg for pkg in pkg_resources.working_set.by_key}
        missing = required - installed

        if len(missing) > 0:
            raise Exception(
                "Missing required modules: {0}.\nSee README for tool installation.".format(
                    missing
                )
            )

        # parse args
        config = parseDevNetworkArgs(sys.argv)
        # prepare folders
        if os.path.exists(config.resultsPath):
            remove_tree(config.resultsPath)

        os.makedirs(config.metricsPath)

        # get repository reference
        repo = getRepo(config)
        # setup sentiment analysis
        senti = sentistrength.PySentiStr()

        sentiJarPath = os.path.join(config.sentiStrengthPath, "SentiStrength.jar").replace("\\", "/")
        senti.setSentiStrengthPath(sentiJarPath)

        sentiDataPath = os.path.join(config.sentiStrengthPath, "SentiStrength_Data").replace("\\", "/") + "/"
        senti.setSentiStrengthLanguageFolderPath(sentiDataPath)

        # prepare batch delta
        delta = relativedelta(months=+config.batchMonths)

        # handle aliases
        commits = list(replaceAliases(repo.iter_commits(), config))

        # run analysis
        batchDates, authorInfoDict, daysActive = commitAnalysis(
            senti, commits, delta, config
        )

        tagAnalysis(repo, delta, batchDates, daysActive, config)
        # Tag Analysis (results_{batch_id}.csv to pdf)
        



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

            # Import the whole
            
            import pandas as pd
            df = pd.read_csv(os.path.join(config.resultsPath, f"results_{batchIdx}.csv"))
    
            import pandas as pd
            from fpdf import FPDF
            # Create a PDF documen
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            for i in range(len(df)):
                row = df.iloc[i].values
                row_data = " | ".join(map(str, row))
                pdf.cell(200, 10, txt=row_data, ln=True)
            
            pdf_output_path = os.path.join(config.resultsPath, f"results_{batchIdx}.pdf")
            pdf.output(pdf_output_path)


            # run smell detection
            smells = smellDetection(config, batchIdx)
            import json
            json_output_path = os.path.join(config.resultsPath, f"smells.json")
            with open(json_output_path, 'w') as json_file:
                json.dump(smells, json_file)  


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


import os
import subprocess
import platform

def explore(path):
    path = os.path.normpath(path)
    if platform.system() == "Windows":
        FILEBROWSER_PATH = os.path.join(os.getenv("WINDIR"), "explorer.exe")
        if os.path.isdir(path):
            subprocess.run([FILEBROWSER_PATH, path])
        elif os.path.isfile(path):
            subprocess.run([FILEBROWSER_PATH, "/select,", os.path.normpath(path)])
    else:
        if platform.system() == "Darwin": # macOS
            subprocess.run(["open", path])
        elif platform.system() == "Linux":
            subprocess.run(["xdg-open", path])
        else:
            print(f"File explorer not supported on {platform.system()} systems.")

if __name__ == "__main__":
    main(sys.argv[1:])
