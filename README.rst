===========
flask-chown
===========

.. image:: https://travis-ci.org/xvzf/flask-chown.svg?branch=master
    :target: https://travis-ci.org/xvzf/flask-chown

.. image:: https://badge.fury.io/py/flask-chown.svg
   :target: https://badge.fury.io/py/flask-chown
   :alt: PyPI version

.. image:: https://img.shields.io/pypi/pyversions/flask-chown.svg
   :target: https://pypi.org/project/flask-chown/
   :alt: Python Versions

.. image:: https://readthedocs.org/projects/flask-chown/badge/?version=latest
   :target: http://flask-chown.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

Flask view permission management the UNIX way using owner and groups

Documentation
=============

https://xvzf.tech/flask-chown

Example
=======

.. code-block:: python

  from flask_chwon import PermissionManager

  ...
  app = Flask(...)

  pm = PermissionManager()
  pm.init_app(app)
  # or
  # pm = PermissionManager(app)

  ...

  @app.route("/")
  @pm.chmod(user="helloworld", group="test")
  def index():
      return "Hello World"
