"""Install Dallinger as a command line utility."""
import pathlib
from setuptools import setup

# The directory containing this file
HERE = pathlib.Path(__file__).parent

README = (HERE / "README.md").read_text(encoding="utf-8")


setup_args = dict(
    name="dallinger",
    packages=["dallinger", "dallinger_scripts"],
    version="7.7.0",
    description="Laboratory automation for the behavioral and social sciences",
    long_description=README,
    long_description_content_type="text/markdown",
    url="http://github.com/Dallinger/Dallinger",
    maintainer="Jordan Suchow",
    maintainer_email="suchow@berkeley.edu",
    license="MIT",
    keywords=["science", "cultural evolution", "experiments", "psychology"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Framework :: Pytest",
    ],
    include_package_data=True,
    zip_safe=False,
    entry_points={
        "console_scripts": [
            "dallinger = dallinger.command_line:dallinger",
            "dallinger-housekeeper = dallinger.command_line:dallinger_housekeeper",
            "dallinger_heroku_web = dallinger_scripts.web:main",
            "dallinger_heroku_worker = dallinger_scripts.worker:main",
            "dallinger_heroku_clock = dallinger_scripts.clock:main",
        ],
        "dallinger.experiments": [],
        "pytest11": ["pytest_dallinger = dallinger.pytest_dallinger"],
    },
    install_requires=[
        "APScheduler",
        "cached-property",
        "boto3",
        "build",
        "click",
        "faker",
        "Flask-Sockets",
        "Flask<2.0",
        "flask-crossdomain",
        "flask-login",
        "Flask-WTF",
        "future",
        "gevent",
        "greenlet",
        "gunicorn",
        "heroku3",
        "librosa",
        "localconfig",
        "pexpect",
        "pip>=20",
        "pip-tools",
        "psycopg2",
        "psutil",
        "redis",
        "requests",
        "rq",
        "selenium",
        "six",
        "SQLAlchemy",
        "sqlalchemy-postgres-copy",
        "tabulate",
        "timeago",
        "tzlocal",
        "ua-parser",
        "user-agents",
    ],
    extras_require={
        "jupyter": [
            "jupyter",
            "ipywidgets",
        ],
        "data": [
            "pandas",
            "tablib[all]",
        ],
        "dev": [
            "alabaster",
            "black",
            "bumpversion",
            "coverage",
            "coverage_pth",
            "codecov",
            "flake8",
            "mock",
            "pre-commit",
            "pycodestyle",
            "pypandoc",
            "pytest",
            "pytest-rerunfailures",
            "recommonmark",
            "sphinxcontrib-spelling",
            "Sphinx",
            "tox",
            "sphinx-js",
            "sphinx_rtd_theme",
        ],
        "docker": ["docker", "docker-compose", "paramiko", "sshtunnel"],
        ':python_version <= "3.7"': ["importlib_metadata"],
    },
)

setup(**setup_args)
