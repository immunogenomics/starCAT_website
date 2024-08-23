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

bcrypt = Bcrypt()
bp = Blueprint('bl_starcat', __name__, url_prefix='/starcat')

@bp.route('/run-starcat', methods=('GET', 'POST'))
def runstarcat():
    mc = set_menu("starcat")

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Authenticate user
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password) and user.is_email_verified:
            session['selected_ref'] = request.form.get('ref')
            file = request.files['file']
            
            if file:
                if os.path.splitext(file.filename)[-1] != '.h5ad':
                    flash("File Type Error", 'danger')
                else:
                    print('hello')
                    id = ''.join(random.choice(string.ascii_letters) for _ in range(15))
                    os.makedirs(os.path.join(current_app.config['UPLOAD_FOLDER'], id), exist_ok=True)
                    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], id, file.filename)
                    file.save(file_path)

                    if session.get('selected_ref'):
                        process_data(file_path, id)
                        out_file = os.path.join(current_app.config['UPLOAD_FOLDER'], id, 'starCAT_output.tar.gz')
                        return send_file(os.path.join(os.getcwd(), out_file), as_attachment=True,
                                         download_name='starCAT_output.tar.gz')
        else:
            flash('Invalid email or password. Please check they are entered correctly and make sure you have already registered\
                and verified your email', 'danger')
            return redirect(url_for('bl_starcat.runstarcat'))

    return render_template('starcat/starcatpage.html', mc=mc, references=['TCAT.V1', 'BCAT.V1'], 
                           selected_ref=session.get('selected_ref'))

@bp.errorhandler(RequestEntityTooLarge)
def file_size_error(error):
    flash('File Size Error', 'danger')
    return redirect(url_for('bl_starcat.runstarcat'))

def process_data(file_path, id):
    # Run starCAT
    out_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], id, 'starCAT_output')
    out_file = os.path.join(current_app.config['UPLOAD_FOLDER'], id, 'starCAT_output.tar.gz')
    os.makedirs(out_dir, exist_ok=True)

    cat = starCAT(reference=session.get('selected_ref'), cachedir=current_app.config['UPLOAD_FOLDER'])
    adata = cat.load_counts(file_path)
    usage, scores = cat.fit_transform(adata)
    cat.save_results(out_dir, 'starCAT')

    with tarfile.open(out_file, "w:gz") as tar:
        tar.add(out_dir, arcname='starCAT_output')

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

