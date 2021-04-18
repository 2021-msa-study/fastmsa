from setuptools import setup
from os import path

this_dir = path.abspath(path.dirname(__file__))
with open(path.join(this_dir, "README.md")) as f:
    long_description = f.read()

setup(
    name="fastmsa",
    packages=["fastmsa"],
    version="0.1",
    license="MIT",
    description="FastMSA - full-stack framework for microservice architecture applications",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Joseph Kim, Benzamin Yoon",
    author_email="cloudeyes@gmail.com",
    url="https://github.com/2021-msa-study/fastmsa",
    download_url="https://github.com/2021-msa-study/fastmsa/archive/v0.1.tar.gz",
    keywords=["fastmsa", "microservice" "framework", "sqlalchemy", "fastapi"],
    install_requires=[
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "uvicorn",
        "jinja2",
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
