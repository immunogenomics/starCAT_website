import os
from flask import Flask
from flask_login import LoginManager
from .jinjafilters import *
from .errorhandlers import *
from .config import Config
from .user_model import db


login_manager = LoginManager()

def create_app():
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)
    db.init_app(app)

    login_manager.init_app(app)
    #login_manager.login_view = 'bp.login'
    #login_manager.login_message_category = 'info'

    from . import bl_home
    app.register_blueprint(bl_home.bp)

    from . import bl_references
    app.register_blueprint(bl_references.bp)

    from . import bl_starcat
    app.register_blueprint(bl_starcat.bp)

    from . import bl_login
    app.register_blueprint(bl_login.bp)

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


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))