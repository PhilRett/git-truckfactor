"""
Module for cloning and extracting metrics from a git repository.
"""
import subprocess
import os
import shlex
import re
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
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


def get_info(local_path_repo, cur_wd):
    """
    Return commit hash, author, author date in 'YYYY-MM-DD' format, author email address, commit comment, insertions and deletions.

    Parameters
    ----------
    local_path_repo : str
        Local path to the directory of the git repository.
    cur_wd : str
        Current working directory.

    Returns
    -------
    commit_info : list of lists - [['Commit', hash, author, date, email, commit comment, [insertions, deletions, total changes]]]
    """

    git_cmd = [
        "git", "log", "--pretty=format:Commit%n%H%n%an%n%as%n%ae%n%s%n", 
        "--shortstat"
        ]

    pathlib_curwd = Path(cur_wd)
    pathlib_repo = pathlib_curwd.joinpath(local_path_repo)

    os.chdir(str(pathlib_repo))
    process = subprocess.run(git_cmd, capture_output=True, encoding="utf-8", check=True)
    os.chdir(str(pathlib_curwd))  # change back to the current working directory

    log_shortstat = process.stdout.split("\n")
# append the ouptut of git log to a list, each commit stat can be separated by the entry "Commit"
    list_commit_info = []
    i_sep_cur = 0
    i_sep_prev = 0
    for i in range(1, len(log_shortstat)):  # loop through list
        if (log_shortstat[i] == "Commit"):  # if 'Commit' is found set the index for the previous and current separators
            i_sep_prev = i_sep_cur
            i_sep_cur = i
            list_commit_info.append(
                log_shortstat[i_sep_prev : i_sep_cur - 1]
            )  # append all items between string "commit"
    list_commit_info.append(
        log_shortstat[i_sep_cur:-1]
    )  # append items after last string "commit"

    list_commit_info = [
        list(filter(None, commit)) for commit in list_commit_info
    ]  # filter None values

    # extract the insertions and deletions
    for commit in list_commit_info:
        try:
            re_insert = re.search(r"(\d+|$)(?=\s*insert)", commit[6])
            insertions = re_insert.group(0) if re_insert else 0
            re_delet = re.search(r"(\d+|$)(?=\s*delet)", commit[6])
            deletions = re_delet.group(0) if re_delet else 0
            commit[6] = [insertions, deletions, int(insertions) + int(deletions)]
        except:
            # if no changes are made, the insertions and deletions are not displayed, therefore we add them if no changes can be detected
            commit.append([0, 0, 0])

    return list_commit_info


def commits_per_user(list_commit_info):
    """
    Return a dictionary that holds the people that commited on the specified repositories and the number of commits

    Parameters
    ----------
    list_commit_info : list
        list that holds information about commits, which is the list retrieved from function get_info()

    Returns
    -------
    dict_commits_user : dict - {'author': number of commits}
    """
    
    dict_commits_user = {}

    for commit in list_commit_info:
        author = commit[2]
        if (author in dict_commits_user):
            dict_commits_user[author] += 1
        else:
            dict_commits_user[author] = 1

    return dict_commits_user


def number_commits(list_commit_info):
    """
    Return a dictionary that holds the total number of commits and contributors of a repository

    Parameters
    ----------
    list_commit_info : list
        list that holds information about commits, which is the list retrieved from function get_info()

    Returns
    -------
    dict_commits_stats : dict - {'Total number of commits': num_commits
                                 'Number of contributors': num_contributors}
    """
    dict_commits_user = commits_per_user(list_commit_info)
    num_commits = sum(dict_commits_user.values()) #sum the values in the dictionary
    num_contributors = len(dict_commits_user) #length of the dictionary -> number of people
    
    #create a dictionary to store the values
    dict_commits_stats = {}
    dict_commits_stats["Total number of commits:"] = num_commits
    dict_commits_stats["Number of contributors"] = num_contributors

    return dict_commits_stats


def list_contributors(list_commit_info):
    """
    Return a list of contributors

    Parameters
    ----------
    list_commit_info : list
        list that holds information about commits, which is the list retrieved from function get_info()

    Returns
    -------
    list_contributors : list - [contributors]
    """
    list_contributors = list(set([commit[2] for commit in list_commit_info]))

    return list_contributors


def list_first_contributions(list_commit_info):
    """
    Return a list that holds the date of the initial contributions

    Parameters
    ----------
    list_commit_info : list
        list that holds information about commits, which is the list retrieved from function get_info()

    Returns
    -------
    list_first_contribution : list
    """
    dict_first_contribution = {}

    for commit in list_commit_info:
        contributor = commit[2]
        date = datetime.strptime(commit[3], "%Y-%m-%d")

        if (contributor in dict_first_contribution):
            if date < dict_first_contribution[contributor]:
                dict_first_contribution[contributor] = date
        else:
            dict_first_contribution[contributor] = date
    
    list_first_contribution = list(map(list, dict_first_contribution.items()))

    return list_first_contribution


def plot_new_contributors_month(list_commit_info):
    """
    Create a plot that shows new contributors per month

    Parameters
    ----------
    list_commit_info : list
        list that holds information about commits, which is the list retrieved from function get_info()
    """
    
    list_first_contribution = list_first_contributions(list_commit_info)
    
    #transform commit_info to a pandas dataframe
    df_first_contribution = pd.DataFrame(list_first_contribution, columns = ['contributor', 'date_first_contribution'])

    #group commit_info by month
    first_cont_month = df_first_contribution.groupby([df_first_contribution['date_first_contribution'].dt.strftime('%m-%Y')]).agg({'contributor': pd.Series.nunique}) #group by month and year, count unique values using aggregate function
    first_cont_month.index = pd.to_datetime(first_cont_month.index) #convert index to datetime type
    first_cont_month = first_cont_month.sort_index() #sort by index/date

    #Create a plot that shows the unique contributors per month
    month_year = first_cont_month.index

    count_cont_month = first_cont_month['contributor']

    fig = go.Figure()

    fig.add_trace(go.Scatter(x=month_year, y=count_cont_month, name='Count of new contributors per month',
                         line=dict(color='royalblue', width=2)))

    fig.update_layout(title='Count of new contributors per month over time',
                   xaxis_title='Date',
                   yaxis_title='Count of  newcontributors')


    fig.show()


def lines_of_code_added(list_commit_info):
    """
    Return a dictionary that holds the contributors and their delivered lines of code

    Parameters
    ----------
    list_commit_info : list
        list that holds information about commits, which is the list retrieved from function get_info()

    Returns
    -------
    dict_loc_user : dict - {"author" : loc_added}
    """

    dict_loc_user = {}

    for commit in list_commit_info:
        author = commit[2]
        loc_added = int(commit[-1][0])
        if (author in dict_loc_user):
            dict_loc_user[author] += loc_added
        else:
            dict_loc_user[author] = loc_added

    return dict_loc_user


def plot_unique_contributors_month(list_commit_info):
    """
    Create a plot that shows the unique contributors per month

    Parameters
    ----------
    list_commit_info : list
        list that holds information about commits, which is the list retrieved from function get_info()
    """

    commit_info = [commit[1:5] for commit in list_commit_info]

    #transform commit_info to a pandas dataframe
    df_commit_info = pd.DataFrame(commit_info, columns = ['commit hash', 'author', 'date', 'email'])
    df_commit_info['date']= pd.to_datetime(df_commit_info['date'])

    #group commit_info by month
    cont_month = df_commit_info.groupby([df_commit_info['date'].dt.strftime('%m-%Y')]).agg({'author': pd.Series.nunique}) #group by month and year, count unique values using aggregate function
    cont_month.index = pd.to_datetime(cont_month.index) #convert index to datetime type
    cont_month = cont_month.sort_index() #sort by index/date

    #Create a plot that shows the unique contributors per month
    month_year = cont_month.index
    count_cont_month = cont_month['author']

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=month_year, y=count_cont_month, name='Count of contributors per month',
                         line=dict(color='royalblue', width=2)))

    fig.update_layout(title='Count of unique contributors per month over time',
                      xaxis_title='Date',
                      yaxis_title='Count of contributors')
    fig.show()


def plot_unique_contributors_quarter(list_commit_info):
    """
    Create a plot that shows the unique contributors per quarter

    Parameters
    ----------
    list_commit_info : list
        list that holds information about commits, which is the list retrieved from function get_info()
    """

    commit_info = [commit[1:5] for commit in list_commit_info]

    #transform commit_info to a pandas dataframe
    df_commit_info = pd.DataFrame(commit_info, columns = ['commit hash', 'author', 'date', 'email'])
    df_commit_info['date']= pd.to_datetime(df_commit_info['date'])

    #group df_commit_info by quarter
    cont_quarter = df_commit_info.groupby(df_commit_info['date'].dt.to_period('Q')).agg({'author': pd.Series.nunique}) #group by month and year count 
    cont_quarter = cont_quarter.sort_index().to_timestamp() #convert the period type to a timestamp to be able to plot it with plotly

    #Create a plot that shows the unique contributors per quarter
    quarter = cont_quarter.index
    count_cont_quarter = cont_quarter['author']

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=quarter, y=count_cont_quarter, name='Count of contributors per quarter',
                         line=dict(color='firebrick', width=2)))

    fig.update_layout(title='Count of unique contributors per quarter over time',
                   xaxis_title='Date',
                   yaxis_title='Count of contributors')
    fig.show()