#!/usr/bin/env python

import os
import sys
from setuptools import setup

DOCLINES = (__doc__ or '').split("\n")


def setup_package():
    src_path = os.path.dirname(os.path.abspath(sys.argv[0]))
    old_path = os.getcwd()
    os.chdir(src_path)
    sys.path.insert(0, src_path)

    try:
        # See setup.cfg
        setup(py_modules=['cssdecl'],
              setup_requires=['pytest-runner'],
              tests_require=['pytest>=2.7', 'pytest-cov~=2.4'],
              install_requires=['tinycss2~=0.5'])
    finally:
        del sys.path[0]
        os.chdir(old_path)
    return


if __name__ == '__main__':
    setup_package()
