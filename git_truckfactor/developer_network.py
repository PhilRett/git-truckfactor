import os
import subprocess
import networkx as nx
from pathlib import Path

def save_network_adjlist(local_path_repo, cur_wd, start_date, end_date, year, list_files):
    repo_name = local_path_repo.rpartition("/")[-1]
    destination = Path("./data/developer_networks/" + year + "/" + repo_name + "_adjacency_list.adjlist")

    if not destination.exists():
        dict_file_dev = create_dict_file_dev(local_path_repo, cur_wd, start_date, end_date, list_files)
        set_contributors = get_set_contributors(dict_file_dev)
        adjacency_list = create_adjacency_list(set_contributors, dict_file_dev)

        graph_repo = nx.Graph(adjacency_list)

        nx.write_adjlist(graph_repo, destination)


def create_dict_file_dev(local_path_repo, cur_wd, start_date, end_date, list_files):
    dict_file_dev = {}

    for source_file in list_files:
        list_contributors = get_contributors_file(local_path_repo, cur_wd, source_file, start_date, end_date)
        if len(list_contributors) <= 1:
            continue
        dict_file_dev[source_file] = list_contributors

    return dict_file_dev


def get_contributors_file(local_path_repo, cur_wd, filename, start_date, end_date):

    git_cmd = [
        "git", "log", "--after={" + start_date + "}", 
        "--before={" + end_date + "}", "--format=%an",
        filename
        ]

    pathlib_curwd = Path(cur_wd)
    pathlib_repo = pathlib_curwd.joinpath(local_path_repo)

    os.chdir(str(pathlib_repo))
    process = subprocess.run(git_cmd, capture_output=True, encoding="utf-8", check=True)
    os.chdir(str(pathlib_curwd))  # change back to the current working directory

    log_shortstat = process.stdout.split("\n")

    list_contributors_file = list(set(filter(None, log_shortstat)))
    
    return list_contributors_file


def get_set_contributors(dict_file_dev):
    set_contributors = set()

    for list_cont in dict_file_dev.values():
        set_contributors.update(list_cont)
    
    return set_contributors


def create_adjacency_list(set_contributors, dict_file_dev):
    adjacency_list = {}

    for contributor in set_contributors:
        for nodes in dict_file_dev.values():
            if contributor in nodes:
                connected_nodes = [node for node in nodes if node != contributor]
                if (contributor in adjacency_list):
                    adjacency_list[contributor].update(connected_nodes)
                else:
                    adjacency_list[contributor] = set(connected_nodes)

    return adjacency_list


def calculate_closeness_centrality(G, number):
    closeness_all = nx.closeness_centrality(G)
    closeness = sorted(closeness_all.items(),key=lambda x: x[1],reverse=True)[0:number]
    return closeness
