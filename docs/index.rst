===========
flask-chown
===========

Flask view permission management the UNIX way using owner and groups

Content
=======
.. toctree::
   :maxdepth: 4

   flask_chown


Example
=======

.. code-block:: python

  from flask_chmod import PermissionManager

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
