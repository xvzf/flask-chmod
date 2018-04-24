===========
flask-chown
===========

Flask view permission management the UNIX way using owner and groups


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
