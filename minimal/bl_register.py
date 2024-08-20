from flask import Blueprint, render_template, redirect, url_for, flash, request
from .user_model import RegistrationForm, User, db
from flask_bcrypt import Bcrypt
from flask_login import login_user, current_user, logout_user, login_required
from .layoutUtils import *

bcrypt = Bcrypt()

# Define the blueprint
bp = Blueprint('bl_register', __name__, url_prefix=None)

@bp.route("/register", methods=['GET', 'POST'])
def register():
    mc = set_menu("register")
    
    registration_form = RegistrationForm()
    if (request.method == 'POST'):
        if registration_form.validate_on_submit():
            hashed_password = bcrypt.generate_password_hash(registration_form.password.data).decode('utf-8')
            user = User(username=registration_form.email.data, email=registration_form.email.data, password=hashed_password)
            db.session.add(user)
            db.session.commit()
            flash('Your account has been created! You can now run starCAT.', 'success')
            return redirect(url_for('bl_register.register'))
        else:
            print(registration_form.errors)

    return render_template('register/register.html', mc=mc, registration_form=registration_form)