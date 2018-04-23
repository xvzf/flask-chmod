===========
flask-chmod
===========

Flask view permission management the UNIX way using groups and a chmod oriented syntax.


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

  # 100 -> 'User'  access is allowed
  # 010 -> 'Group' access is allowed
  # 001 -> 'Other' access is allowed
  #
  # Add up these values to get a valid chmod
  @app.route("/")
  @pm.chmod(110, user="helloworld", group="test")
  def index():
      return "Hello World"
