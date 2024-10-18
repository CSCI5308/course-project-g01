
import sys
import os
import subprocess
import shutil
import stat
import git
import pkg_resources
import sentistrength
import pandas as pd
import json

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
from configuration import Configuration



def smelldetection1(repo_url, pat_token):

    results_folder = "../server_results/"  

    split = repo_url.split("/")
    repositoryPath = os.path.join(results_folder, split[3], split[4])
    resultsPath = os.path.join(repositoryPath, "results")


    smells_file = os.path.join(resultsPath, 'smells.json')
    df_file = os.path.join(resultsPath, 'results_0.csv')

    
    
    command = [
        'python3', 'smellserver.py',
        '-r', repo_url,
        '-p', pat_token,
        '-s', '../data/',
        '-o', results_folder
    ]
    
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while running command: {e}")
        return None, None

    # Read the smells.json file
    smells_data = None
    if os.path.exists(smells_file):
        with open(smells_file, 'r') as f:
            smells_data = json.load(f)
    else:
        print(f"Could not find {smells_file}")

    # Convert the result_0.csv file into a DataFrame
    df_data = None
    if os.path.exists(df_file):
        df_data = pd.read_csv(df_file)
        df_data.columns=["Metric", "Value"]
    else:
        print(f"Could not find {df_file}")
    shutil.rmtree(results_folder)
    return smells_data, df_data



class Progress(git.remote.RemoteProgress):
    def update(self, op_code, cur_count, max_count=None, message=""):
        print(self._cur_line, end="\r")


def commitDate(tag):
    return tag.commit.committed_date


def remove_readonly(fn, path, excinfo):
    os.chmod(path, stat.S_IWRITE)
    remove_tree(path)


def remove_tree(path):
    """Remove a file or directory tree."""
    if os.path.isdir(path):
        shutil.rmtree(path, onerror=remove_readonly)  # Removes directory and its contents
    elif os.path.isfile(path):
        os.remove(path)  # Removes the file
    else:
        raise ValueError(f"Path '{path}' is neither a file nor a directory.")



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



