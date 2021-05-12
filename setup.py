import os
from os import path

from setuptools import setup


def package_files(directory):
    paths = []
    for (path, _, filenames) in os.walk(directory):
        if "__pycache__" in path:
            continue
        for filename in filenames:
            paths.append(os.path.join("..", path, filename))
    return paths


extra_files = package_files("fastmsa/templates")

this_dir = path.abspath(path.dirname(__file__))
with open(path.join(this_dir, "README.md")) as f:
    long_description = f.read()

setup(
    name="FastMSA",
    description="FastMSA - full-stack framework for microservice architecture applications",
    long_description=long_description,
    long_description_content_type="text/markdown",
    version="0.3",
    license="MIT",
    author="Joseph Kim, Benzamin Yoon",
    author_email="cloudeyes@gmail.com",
    packages=["fastmsa", "fastmsa.test", "fastmsa.core"],
    package_data={
        "": extra_files,
        "fastmsa": ["py.typed"],
        "fastmsa.core": ["py.typed"],
        "fastmsa.test": ["py.typed"],
    },
    url="https://github.com/2021-msa-study/fastmsa",
    download_url="https://github.com/2021-msa-study/fastmsa/archive/v0.3.tar.gz",
    keywords=["fastmsa", "microservice" "framework", "sqlalchemy", "fastapi"],
    install_requires=[
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "uvicorn",
        "jinja2",
        "colorama",
        "tenacity",
        "aioredis",
        "httpx",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.9",
    ],
    entry_points={
        "console_scripts": [
            "msa = fastmsa.command:console_main",
        ]
    },
)
