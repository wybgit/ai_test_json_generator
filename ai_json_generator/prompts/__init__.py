# -*- coding: utf-8 -*-
"""
Prompt templates for AI JSON generator.
"""

import os

# Get the list of prompt template files
def list_templates():
    """
    Returns a list of available prompt templates.
    """
    current_dir = os.path.dirname(__file__)
    templates = []
    for file in os.listdir(current_dir):
        if file.endswith('.prompt'):
            templates.append(file)
    return templates 