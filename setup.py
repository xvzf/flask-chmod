from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, "README.rst"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="flask-chown",
    version="0.2.1",
    description="Flask permissions the UNIX way using owner and groups",
    long_description=long_description,
    url="https://github.com/xvzf/flask-chown",
    author="Matthias Riegler",
    author_email="matthias@xvzf.tech",

    # Classifiers help users find your project by categorizing it.
    #
    # For a list of valid classifiers, see
    # https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Framework :: Flask",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
    ],

    keywords="flask permission flask-login flask-principal",
    packages=find_packages(exclude=["contrib", "docs", "tests"]),
    install_requires=["flask"],
    setup_requires=['pytest-runner'],
    tests_require=['pytest', 'future'],

    extras_require={  # Optional
        "caching support": ["redis"]
    },

    project_urls={  # Optional
        "Bug Reports": "https://github.com/xvzf/flask-chown/issues",
        "Source": "https://github.com/xvzf/flask-chown/",
    },

)
