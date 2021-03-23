"""module that calculates the truckfactor for a local git repository"""
import os
import shlex
import subprocess
import csv
import collections
import re
import itertools
import numpy as np
from pathlib import Path

def truck_factor_repo(local_path_repo, cur_wd, start_date, end_date):
    """
    Calculate the truckfactor from a repository and write the truckfactor statistics to a csv file.

    Parameters
    ----------
    local_path_repo : str
        Local path to the directory of the git repository.
    cur_wd : str
        Current working directory
    start_date : str
        Start date from commit history in ISO format.
    end_date
        End date from commit history in ISO format.

    Returns
    -------
    tf - int
        Number of truckfactor developers.
    """

    list_files = list_files_linguist(local_path_repo, cur_wd)  # get the list of files

    dict_authors_file = authors_file_list(
        local_path_repo, cur_wd, list_files, start_date, end_date
    )  # get the name of each author and their authored files

    truck_factor = calculate_tf(
        local_path_repo, cur_wd, dict_authors_file
    )  # calculate the truck factor

    return truck_factor


def list_files_linguist(local_path_repo, cur_wd):
    """
    Get a list of source files from a repository that disregards third party code, documentation, images, ...

    Parameters
    ----------
    local_path_repo : str
        Local path to the directory of the git repository.
    cur_wd : str
        Current working directory.

    Returns
    -------
    files_linguist : list - [filename]
        List of source files from the git repository.
    """

    git_cmd = shlex.split("github-linguist --breakdown")

    pathlib_curwd = Path(cur_wd)
    pathlib_repo = pathlib_curwd.joinpath(local_path_repo)

    os.chdir(str(pathlib_repo))
    process = subprocess.run(git_cmd, capture_output=True, encoding="utf-8", shell=True
    )  # run the shell command git_cmd
    os.chdir(str(pathlib_curwd))  # change back to the current working directory

    # divide the output of the git command into list entries
    files_linguist = process.stdout.split("\n")

    # filter files_linguist: remove entries which do not represent a file name
    files_linguist = list(
        filter(lambda file: check_remove(file) == True, files_linguist)
    )

    return files_linguist


def check_remove(string):
    """
    Return true if input string has "." in it and not "%" in it
    """

    return bool("." in string and "%" not in string)


def authors_file_list(local_path_repo, cur_wd, list_files, start_date, end_date):
    """
    Loop through each file in a repository:
    - extract the commit history for each file
    - define the authors of each file
    - create a dictionary with the authors name and append their authored files

    Returns
    -------
    dict_files_authors : dict - {author: [filename]}
        Dictionary that stores the authors and their authored files.
    """

    dict_files_authors = {}

    for filename in list_files:
        commit_history = get_commit_history(
            local_path_repo, cur_wd, filename, start_date, end_date
        )
        if (not commit_history):  # stops the current iteration and moves to the next iteration if commit_history is empty
            continue

        list_doa = doa(commit_history)
        file_authors = get_authors_file(list_doa, filename)

        for i in range(1, len(file_authors)):
            if (file_authors[i] in dict_files_authors):  # if author is in dictionary append the filenames
                dict_files_authors[file_authors[i]].append(file_authors[0])
            else:
                dict_files_authors[file_authors[i]] = [file_authors[0]]  # if author not yet in dictionary, create a new entry with the author and filenames

    return dict_files_authors


def get_commit_history(local_path_repo, cur_wd, filename, start_date, end_date):
    """
    Invoke subprocess and run git command 'log shortstat' to extract the commit history of a file

    Parameters
    ----------
    local_path_repo : str
        Local path to the directory of the git repository.
    cur_wd : str
        Current working directory
    filename : str
        Name of the source file.
    start_date : str
        Start date from commit history in ISO format.
    end_date
        End date from commit history in ISO format.

    Returns
    -------
    commit_info_file : list of lists - [[hash, author, date, insertions, deletions, total number of changes]]
        Commit history - information about commits of a source file.
    """

    git_cmd = [
        "git", "log", "--after={" + start_date + "}", 
        "--before={" + end_date + "}", "--pretty=format:Commit%n%H%n%an%n%as%n%ae%n%s%n", 
        "--shortstat", filename
        ]

    pathlib_curwd = Path(cur_wd)
    pathlib_repo = pathlib_curwd.joinpath(local_path_repo)

    os.chdir(str(pathlib_repo))
    process = subprocess.run(git_cmd, capture_output=True, encoding="utf-8", check=True)
    os.chdir(str(pathlib_curwd))  # change back to the current working directory

    log_shortstat = process.stdout.split("\n")

    # checks if the commit history is empty (no commits for a file in the specified timeline)
    if check_empty_commit_history(log_shortstat):
        return False

    # append the ouptut of git log to a list, each commit stat can be separated by the entry "Commit"
    commit_info_file = []
    i_sep_cur = 0
    i_sep_prev = 0
    for i in range(1, len(log_shortstat)):  # loop through list
        if (log_shortstat[i] == "Commit"):  # if 'Commit' is found set the index for the previous and current separators
            i_sep_prev = i_sep_cur
            i_sep_cur = i
            commit_info_file.append(
                log_shortstat[i_sep_prev : i_sep_cur - 1]
            )  # append all items between string "commit"
    commit_info_file.append(
        log_shortstat[i_sep_cur:-1]
    )  # append items after last string "commit"

    commit_info_file = [
        list(filter(None, commit)) for commit in commit_info_file
    ]  # filter None values

    # extract the insertions and deletions
    for commit in commit_info_file:
        try:
            re_insert = re.search(r"(\d+|$)(?=\s*insert)", commit[6])
            insertions = re_insert.group(0) if re_insert else 0
            re_delet = re.search(r"(\d+|$)(?=\s*delet)", commit[6])
            deletions = re_delet.group(0) if re_delet else 0
            commit[6] = [insertions, deletions, int(insertions) + int(deletions)]
        except:
            # if no changes are made, the insertions and deletions are not displayed, therefore we add them if no changes can be detected
            commit.append([0, 0, 0])

    return commit_info_file


def check_empty_commit_history(commit_history):
    """
    Return true if the commit_history is empty
    """

    return bool(len(commit_history) == 1 and not commit_history[0])


def doa(commit_history):
    """
    Calculate the degree of authorship for a source file for every author from a commit history

    Parameters
    ----------
    commit_history : str
        Commit history of a file (list of lists)

    Returns
    -------
    normalized_list : list of lists - [[author, doa, normalized doa]]
        Normalized degree-of-authorship list.
    """

    first_author = first_author_file(commit_history)  # get the first author of a file
    first_authorship = 0

    doa_list = []

    # loop through each commit in a file
    for commit in commit_history:
        author = commit[2]
        if author == first_author:  # set first authorship
            first_authorship = 1
        else:
            first_authorship = 0

        deliveries = commit[6][2]  # number of deliveries, number of changes made by the current developer in the loop
        acceptances = sum(
            commit_ac[6][2] for commit_ac in commit_history if commit_ac != author
        )  # number of acceptances, number of changes mady by any developer other than the current one
        degree_of_authorship = float(
            3.293 + 1.098 * first_authorship + 0.164 * deliveries - 0.321 * np.log(1 + acceptances)
        )  # calculate the degree of authorship for the current author in the loop
        doa_list.append([author, degree_of_authorship])

    dict_unique_author = collections.defaultdict(float)

    for author, value in doa_list:
        dict_unique_author[author] += value  # sum up the doa values for authors that have multiple commits -> merge same authors

    doa_list_unique_author = list(
        map(list, dict_unique_author.items())
    )  # convert the dict to list
    doa_unique_author_values = np.array(doa_list_unique_author)[:, 1].astype(np.float)  # extract the doa values from the list and convert to float

    # if only one author assign doa of 1 else calculate the normalized doa values
    if len(doa_unique_author_values) == 1:
        doa_list_unique_author[0].append(1)
        return doa_list_unique_author  # return doa when only 1 author
    else:
        return normalize_doa_list(
            doa_list_unique_author, doa_unique_author_values
        )  # return normalized doa list


def first_author_file(commit_history):
    """
    Return first author from the commit history
    """

    first_author = commit_history[-1][2]

    return first_author


def normalize_doa_list(doa_list, doa_values):
    """
    Calculate the degree of authorship for a source file for every author from a commit history

    Parameters
    ----------
    doa_list : list of lists - [[author, doa]]
        List of author and doa values.
    doa_values : list - [doa]
        List of doa values.

    Returns
    -------
    normalized_list : list of lists - [[author, doa, normalized doa]]
        Normalized degree-of-authorship list.
    """

    normalized_values = (doa_values - np.min(doa_values)) / (
        np.max(doa_values) - np.min(doa_values)
    )
    normalized_list = []

    for author, degree_of_authorship in zip(doa_list, normalized_values):
        normalized_list.append([author[0], author[1], degree_of_authorship])

    return normalized_list


def get_authors_file(list_doa, filename):
    """
    Return the authors of a file.
    """

    # set threshold parameters
    th_norm_doa = 0.75
    th_abs_doa = 20

    authors_file = [filename]

    # loop through the doa list and extract the authors of a file if the doa values exceed a certain threshold or the author has first authorship
    for item in list_doa:
        if item[1] >= th_abs_doa and item[2] > th_norm_doa or item[2] == 1:
            authors_file.append(item[0])  # append the author to the list

    return authors_file


def calculate_tf(local_path_repo, cur_wd, dict_authors_file):
    """
    Calculate the truck factor for a repository and writes the truckfactor statistics to a csv file.
    Loop through the list of authors
        - get the coverage -> percentage of covered files by the current authors in the authors_list
        - remove the top author (author with the most covered files)
        - increase the truck factor by 1
        - if the coverage is less than 0.5 stop the iteration and return the truck factor and tf statistics

    Returns
    -------
    truckfactor - int
        Number of truckfactor developers.
    """

    authors_list = list(dict_authors_file.keys())  # create a list with the authors
    author_num_files = dict(
        map(lambda author: (author, len(dict_authors_file[author])), authors_list)
    )  # create a dictionary with the authors and the number of files they authored
    num_changed_files = get_num_unique_files(
        dict_authors_file
    )  # get the unique total number of files authored
    tf_stats = [
        ["author", "covered_files", "pct_covered_files", "truck_factor"]
    ]  # create a list which will hold the truckfactor statistics

    repo_name = local_path_repo.rpartition("/")[-1]  # extract the repo name from the repo path
    dict_truckfactor = {"Repository" : repo_name, "Truckfactor_authors" : []}
    truckfactor = 0
    while authors_list:
        coverage = get_coverage(
            authors_list, dict_authors_file, num_changed_files
        )  # get file coverage
        if coverage < 0.5:
            break

        top_author = find_top_author(authors_list, dict_authors_file)  # get top author
        authors_list.remove(top_author)  # remove top author
        top_author_number_files = author_num_files.get(top_author)  # get the number of files from the removed author for the tf statistics
        tf_stats.append(
            [top_author,top_author_number_files,top_author_number_files / num_changed_files,1,]
        )  # add truckfactor statistics for the tf developers
        truckfactor += 1

        #append the truckfactor results to dictionary
        dict_truckfactor.update({"Truckfactor":truckfactor})
        dict_truckfactor["Truckfactor_authors"].append(top_author)

    # add the truckfactors statistics for non tf developers
    for author in authors_list:
        author_number_files = author_num_files.get(author)
        tf_stats.append(
            [author, author_number_files, author_number_files / num_changed_files, 0]
        )

    write_to_csv(local_path_repo, cur_wd, tf_stats, repo_name)  # write the tf statistics to a csv file

    return dict_truckfactor

'''
if (file_authors[i] in dict_files_authors):  # if author is in dictionary append the filenames
    dict_files_authors[file_authors[i]].append(file_authors[0])
else:
    dict_files_authors[file_authors[i]] = [file_authors[0]] 
'''

def get_num_unique_files(dict_authors_file):
    """
    Return the unique total number of files authored from dict_authors_file.
    """

    changed_files_unchained = list(dict_authors_file.values())
    changed_files_chained = list(itertools.chain.from_iterable(changed_files_unchained))
    num_changed_files = len(set(changed_files_chained))

    return num_changed_files


def get_coverage(authors_list, dict_authors_file, num_changed_files):
    """
    Return the pct of covered files by a set of authors.
    """

    covered_files = set()

    for author in authors_list:
        covered_files.update(dict_authors_file[author])

    return len(covered_files) / num_changed_files


def find_top_author(authors_list, dict_authors_file):
    """
    Return the top author from a set of authors.

    Parameters
    ----------
    authors_list : list - [author]
        List of authors.
    dict_authors_file : dict - {author: [filename]}
        Dictionary that stores the authors and their authored files.
    """

    author_num_files = dict(
        map(lambda author: (author, len(dict_authors_file[author])), authors_list)
    )
    top_author = max(author_num_files, key=author_num_files.get)

    return top_author


def write_to_csv(local_path_repo, cur_wd, tf_stats, repo_name):
    """
    Write the truckfactor statistics to a csv file.
    """

    pathlib_curwd = Path(cur_wd)

    directory_path = pathlib_curwd.joinpath("truckfactor_results")

    try:
        os.makedirs(directory_path)  # create directory if not already existent
    except:
        pass

    csv_file = directory_path.joinpath("truckfactor_stats_" + repo_name + ".csv")
    #csv_file = (
    #    directory_path + "\\truckfactor_stats_" + repo_name + ".csv"
    #)  # path to csv file

    # write the truck factor stats to csv file
    with open(csv_file, "w", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(tf_stats)
