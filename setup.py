from setuptools import setup
import os
import sys

_here = os.path.abspath(os.path.dirname(__file__))

if sys.version_info[0] < 3:
    with open(os.path.join(_here, 'README.rst')) as f:
        long_description = f.read()
else:
    with open(os.path.join(_here, 'README.rst'), encoding='utf-8') as f:
        long_description = f.read()

version = {}
with open(os.path.join(_here, 'git_truckfactor', 'version.py')) as f:
    exec(f.read(), version)

setup(
    name='git-truckfactor',
    version=version['__version__'],
    description=('Calculate code contribution metrics for git repositories'),
    long_description=long_description,
    author='Philipp Rettig',
    author_email='ph.rettig13@gmail.com',
    url='https://github.com/PhilRett/gitmetrics',
    license='',
    packages=['git_truckfactor'],
    install_requires=['numpy', 'networkx'],
    include_package_data=True,
    classifiers=[   
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'Programming Language :: Python :: 3.9'],
    )