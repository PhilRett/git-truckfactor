Git-truckfactor
===============
Git-truckfactor is a library that assits in the analysis of git repositories. It allows for calculation of Truck Factor scores and code contribution metrics.

The tool closely resembles the algorithm proposed by `Avelino et al. <https://arxiv.org/pdf/1604.06766.pdf>`_ to estimate the Truck Factor.

Installation
===============
Get the latest version by running::

    pip install git-truckfactor

Dependencies
------------
Git-truckfactor requires the following python libraries:

* `NumPy <https://numpy.org>`_
* `NetworkX <https://networkx.org>`_

In addition git-truckfactor makes use of the ruby library Linguist. That means you will also need Ruby installed.

* `Linguist <https://github.com/github/linguist>`_


Usage
===============

The git-truckfactor package is intended to be used as a module.

1. Import the module into the python environment::

            import git_truckfactor

2. Clone git repository

    command:: 
        
            git_truckfactor.clone_repository(<github_repository_url>, <local_repository_path>)

    example:: 
        
            git_truckfactor.clone_repository('https://github.com/pandas-dev/pandas.git', './github_repos/pandas')

    returns: local_repository_path

3. Calculate truckfactor

    command::
        
            git_truckfactor.truck_factor_repo(<local_repository_path>, <cur_wd>, <start_date>, <end_date>)

    example:: 
    
            cur_wd = os.getcwd()
            git_truckfactor.truck_factor_repo('./github_repos/pandas', cur_wd, '2020-01-01', '2021-01-01')
    
    returns: truckfactor score + creates a directory 'truckfactor_results' with truck factor statistics stored in a CSV-file


See the `demo.ipynb </demo.ipynb>`_ file for examples on how to use git-truckfactor for multiple repositories.