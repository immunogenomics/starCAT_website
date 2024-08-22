from flask import Blueprint, render_template, redirect, url_for, flash, request
from .user_model import RegistrationForm, User, db
from flask_bcrypt import Bcrypt
from flask_login import login_user, current_user, logout_user, login_required
from .layoutUtils import *
from .email import send_verification_email


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

            send_verification_email(user)

            flash('A verification email has been sent to your email address. Please check your inbox.', 'info')
            return redirect(url_for('bl_register.register'))
        else:
            print(registration_form.errors)

    return render_template('register/register.html', mc=mc, registration_form=registration_form)


@bp.route("/verify_email/<token>")
def verify_email(token):
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('bl_register.register'))
    
    user.is_email_verified = True
    db.session.commit()
    flash('Your email has been verified! You can now run starCAT.', 'success')
    return redirect(url_for('bl_starcat.runstarcat'))


