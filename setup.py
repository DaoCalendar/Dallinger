"""Install Dallinger as a command line utility."""
import pathlib

from setuptools import setup

# The directory containing this file
HERE = pathlib.Path(__file__).parent

README = (HERE / "README.md").read_text(encoding="utf-8")


setup_args = dict(
    name="dallinger",
    packages=["dallinger", "dallinger_scripts"],
    version="9.11.0",
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
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
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
        "Flask-Sock",
        "Flask",
        "flask-crossdomain",
        "flask-login",
        "Flask-WTF",
        "future",
        "gevent",
        "greenlet",
        "gunicorn[gevent]",
        "heroku3",
        "ipython < 8.13",
        "localconfig",
        "numpy < 1.25",
        "pandas < 2.1",
        "pexpect",
        "pip >= 20",
        "pip-tools",
        "psycopg2",
        "psutil",
        "pyopenssl",
        "redis",
        "requests",
        "rq",
        "selenium",
        "six",
        "SQLAlchemy < 2",
        "sqlalchemy-postgres-copy",
        "tabulate",
        "tenacity",
        "timeago",
        "tzlocal",
        "ua-parser",
        "urllib3 < 2",
        "user-agents",
    ],
    extras_require={
        "jupyter": [
            "ipywidgets",
            "jupyter",
            "jupyter-server",
        ],
        "data": [
            "pandas",
            "tablib[all]",
        ],
        "dev": [
            "alabaster",
            "black",
            "black[jupyter]",
            "bump2version",
            "coverage",
            "coverage_pth",
            "flake8",
            "isort",
            "mock",
            "myst-parser",
            "pre-commit < 3.6",
            "pycodestyle",
            "pypandoc",
            "pytest",
            "pytest-rerunfailures",
            "sphinx < 7.2",
            "sphinx_rtd_theme",
            "sphinxcontrib-applehelp <= 1.0.4",
            "sphinxcontrib-devhelp <= 1.0.2",
            "sphinxcontrib-htmlhelp <= 2.0.1",
            "sphinxcontrib-qthelp <= 1.0.3",
            "sphinxcontrib-serializinghtml <= 1.1.5",
            "sphinxcontrib-spelling",
            "tox",
        ],
        "docker": ["docker", "paramiko", "sshtunnel"],
    },
)

setup(**setup_args)
