import os
from flask import Flask
from .jinjafilters import *
from .errorhandlers import *
from .config import Config
from .user_model import db

def create_app():
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)
    db.init_app(app)

    from . import bl_home
    app.register_blueprint(bl_home.bp)

    from . import bl_references
    app.register_blueprint(bl_references.bp)

    from . import bl_starcat
    app.register_blueprint(bl_starcat.bp)

    #Add other blueprints if needed

    from . import auth
    app.register_blueprint(auth.bp)

    #ADDS HANDLER FOR ERRORs
    app.register_error_handler(500, error_500)
    app.register_error_handler(404, error_404)

    #JINJA FILTERS
    app.jinja_env.filters['slugify'] = slugify
    app.jinja_env.filters['displayError'] = displayError 
    app.jinja_env.filters['displayMessage'] = displayMessage

    return app