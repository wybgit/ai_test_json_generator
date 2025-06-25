#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import os

# Read version from .env file or use default
version = "0.1.0"
try:
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f.readlines():
                if line.startswith('VERSION='):
                    version = line.split('=')[1].strip()
                    break
except:
    pass

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = [line.strip() for line in f.readlines() if line.strip()]

setup(
    name="ai_json_generator",
    version=version,
    author="Original Author",
    author_email="author@example.com",
    description="A tool for generating AI model JSON descriptions based on templates",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/Test_Json_Generator",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "ai_json_generator": [
            "*.json", 
            "prompts/*", 
            "data_files/*",
            "prompts/*.prompt",
            "data_files/*.csv",
            "data_files/*.txt",
            "data_files/*.md"
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "ai-json-generate=ai_json_generator.generate_json:main",
            "ai-json-operator=ai_json_generator.generate_operator_testcase:main",
        ],
    },
) 