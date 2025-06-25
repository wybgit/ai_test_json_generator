# -*- coding: utf-8 -*-
"""
Data files for AI JSON generator.
"""

import os

# Get the list of data files
def list_data_files():
    """
    Returns a list of available data files.
    """
    current_dir = os.path.dirname(__file__)
    data_files = []
    for file in os.listdir(current_dir):
        if file != '__init__.py' and not file.endswith('.pyc'):
            data_files.append(file)
    return data_files 