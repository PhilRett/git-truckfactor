"""
Module for cloning and extracting metrics from a git repository.
"""
import subprocess
import shlex
import os
from pathlib import Path


def clone_repository(url_repo, path_to):
    """
    Clone a git repository to a specified path.

    Parameters
    ----------
    url_repo : str
        URL address of git repository.
    path_to : str
        Local path to destination directory.
    """

    #specify the git command, split the string and put into list
    git_cmd = shlex.split('git clone ' + url_repo + " " + path_to)

    destination = Path(path_to)

    if not destination.exists():
        process = subprocess.run(git_cmd, stdout = subprocess.PIPE, stderr = subprocess.PIPE, check = True)
        process #run the git command

    return path_to

def commits_per_user(local_path_repo, cur_wd):
    """
    Return a dictionary that holds the people that commited on the specified repositories and the number of commits

    Parameters
    ----------
    local_path_repo : str
        Local path to the directory of the git repository.
    cur_wd : str
        Current working directory.

    Returns
    -------
    dict_commits_user : dict - {'author': number of commits}
    """

    git_cmd = shlex.split('git shortlog -s --all')
    os.chdir(local_path_repo) #change to the local git repository that is to analyze
    process= subprocess.run(git_cmd, capture_output=True, encoding='utf-8', check = True) #run the git command, output as strings
    os.chdir(cur_wd) #change back to the current working directory

    num_commits_user= process.stdout.split('\n')

    #create a dictionary from the process output
    dict_commits_user = {}
    for x in num_commits_user:
        y = x.strip()
        z = y.split(None, 1)
        if z:
            dict_commits_user[z[1]] = z[0]
    
    #convert the values of the dictionary to type integer
    dict_commits_user = dict((key,int(value)) for key, value in dict_commits_user.items())

    return dict_commits_user

def number_commits(local_path_repo, cur_wd):
    """
    Return a dictionary that holds the total number of commits and the number of people that commited

    Parameters
    ----------
    local_path_repo : str
        Local path to the directory of the git repository.
    cur_wd : str
        Current working directory.

    Returns
    -------
    dict_commits_stats : dict - {'Total number of commits': x, 'Number of people that commited' : y}
    """

    dict_commits_user = commits_per_user(local_path_repo, cur_wd)
    num_commits = sum(dict_commits_user.values()) #sum the values in the dictionary
    num_people_commited = len(dict_commits_user) #length of the dictionary -> number of people
    
    #create a dictionary to store the values
    dict_commits_stats = {}
    dict_commits_stats["Total number of commits:"] = num_commits
    dict_commits_stats["Number of people that commited"] = num_people_commited

    return dict_commits_stats


def get_commit_info(local_path_repo, cur_wd):
    """
    Return commit hash, author, author date in 'YYYY-MM-DD' format and author email address

    Parameters
    ----------
    local_path_repo : str
        Local path to the directory of the git repository.
    cur_wd : str
        Current working directory.

    Returns
    -------
    commit_info : list of lists - [[hash, author, date, email]]
    """

    git_cmd=shlex.split('git log --pretty=format:"%H%n%an%n%as%n%ae"')
    os.chdir(local_path_repo)
    process= subprocess.run(git_cmd, capture_output=True, encoding = 'utf-8', check = True)
    os.chdir(cur_wd) #change back to the current working directory

    commits_user= process.stdout.split('\n')

    #create a list of lists from the output (n = number of elements each sublist should have)
    n = 4
    commit_info = [commits_user[i:i+n] for i in range(0, len(commits_user), n)]

    return commit_info
