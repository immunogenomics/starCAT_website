from flask import Blueprint, render_template, redirect, url_for, flash, request
from .user_model import RegistrationForm, LoginForm, User, db
from flask_bcrypt import Bcrypt
from flask_login import login_user, current_user, logout_user, login_required
from .layoutUtils import *

bcrypt = Bcrypt()

# Define the blueprint
bp = Blueprint('bl_login', __name__, url_prefix=None)

@bp.route("/login", methods=['GET', 'POST'])
def login():
    mc = set_menu("login")
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    login_form = LoginForm()
    registration_form = RegistrationForm()

    if login_form.validate_on_submit() and 'login' in request.form:
        user = User.query.filter_by(email=login_form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, login_form.password.data):
            login_user(user, remember=login_form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')

    elif registration_form.validate_on_submit() and 'register' in request.form:
        hashed_password = bcrypt.generate_password_hash(registration_form.password.data).decode('utf-8')
        user = User(username=registration_form.username.data, email=registration_form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You can now log in', 'success')
        return redirect(url_for('bp.auth'))
    
    return render_template('login/login.html', mc=mc, login_form=login_form, registration_form=registration_form)