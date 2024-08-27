from flask import (
    Blueprint, render_template, url_for, request, flash, redirect, send_file, session, current_app
)
from .layoutUtils import *
from .auth import *
from .user_model import User, db, RequestResetForm, ResetPasswordForm
import os
import tarfile
import random
import string
from werkzeug.exceptions import RequestEntityTooLarge
from flask_bcrypt import Bcrypt
from starcat import starCAT
from .email import send_reset_email
from flask_login import current_user
from minimal import reference_names

bcrypt = Bcrypt()
bp = Blueprint('bl_starcat', __name__, url_prefix='/starcat')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    mc = set_menu("starcat")

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('Email not recognized. Please register', 'danger')
            return redirect(url_for('bl_starcat.login'))
        elif not user.is_email_verified:
            flash('Email not verified. Please check your email to confirm registration', 'danger')
            return redirect(url_for('bl_starcat.login'))
        elif not bcrypt.check_password_hash(user.password, password):
            flash('Incorrect password. Please double check or reset if necessary', 'danger')
            return redirect(url_for('bl_starcat.login'))
        else:
            session['verified'] = True
            return redirect(url_for('bl_starcat.runstarcat'))

    if not session.get('verified'):
        return render_template('starcat/login.html', mc=mc, references=reference_names)
    else:
        return render_template('starcat/starcatpage.html', mc=mc, references=reference_names)


@bp.route('/run-starcat', methods=('GET', 'POST'))
def runstarcat():
    mc = set_menu("starcat")
    if not session.get('verified'):
        flash('Please login', 'danger')
        return redirect(url_for('bl_starcat.login'))

    return render_template('starcat/starcatpage.html', mc=mc, references=reference_names)


@bp.route('/logout')
def logout():
    # Clear the session to log the user out
    session.pop('verified', None)
    # Redirect the user back to the login page
    return redirect(url_for('bl_starcat.login'))


@bp.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    mc = set_menu("starcat")
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_reset_email(user)
        flash('If an account with that email exists, a reset link has been sent.', 'info')
        return redirect(url_for('bl_starcat.runstarcat'))
    return render_template('starcat/reset_request.html', mc=mc, form=form)

@bp.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    mc = set_menu("starcat")
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('bl_starcat.reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('bl_starcat.runstarcat'))
    return render_template('starcat/reset_token.html', mc=mc, form=form)

