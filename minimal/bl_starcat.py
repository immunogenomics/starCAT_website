from flask import (
    Blueprint, render_template, url_for, request, flash, redirect, send_file, session, current_app
)
from .layoutUtils import *
from .auth import *
from .user_model import User, db  # Import User model for authentication
import os
import tarfile
import random
import string
from werkzeug.exceptions import RequestEntityTooLarge
from flask_bcrypt import Bcrypt
from starcat import starCAT

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
        if user and bcrypt.check_password_hash(user.password, password):
            session['selected_ref'] = request.form.get('ref')
            file = request.files['file']
            
            if file:
                if os.path.splitext(file.filename)[-1] != '.h5ad':
                    flash("File Type Error", 'danger')
                else:
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
            flash('Invalid email or password. Please check they are entered correctly and make sure you have already registered.', 'danger')
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