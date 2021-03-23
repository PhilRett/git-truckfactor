Git-truckfactor
===========
Git-truckfactor is a library that assits in the analysis of git repositories. It allows for calculation of truckfactor scores and code contribution metrics.

Installation
===============
Get the latest version by running::

    git clone https://github.com/PhilRett/git-truckfactor

or::

    git clone git@github.com:PhilRett/git-truckfactor.git


After cloning the git repository switch to the root directory where the setup.py file is located and enter::

    python setup.py install

to install the package and its python dependencies.

Dependencies
------------
Git-truckfactor requires the following python libraries:

* `NumPy <https://numpy.org>`_
* `NetworkX <https://networkx.org>`_

In addition git-truckfactor makes use of the ruby library Linguist. That means you will also need Ruby installed.

* `Linguist <https://github.com/github/linguist>`_


Usage
===============

See the `demo.ipynb </demo.ipynb>`_ file for examples on how to use git-truckfactor.

License
===============
