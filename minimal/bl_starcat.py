from flask import (
    Blueprint, render_template, url_for, request, flash, redirect, send_file, Markup

)
from .layoutUtils import *
from .auth import *
import tarfile
import pandas as pd
import numpy as np
import scanpy as sc
from starcat import starCAT


bp = Blueprint('bl_starcat', __name__, url_prefix='/starcat')


@bp.route('/run-starcat',methods=('GET', 'POST'))
def runstarcat():
    mc = set_menu("starcat")
    set_session()

    print(session.get('selected_ref', 'none'))

    if request.method == 'POST':
        file = request.files['file']
        if file:
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file.filename)
            os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
            file.save(file_path)

            if session.get('selected_ref'):
                # flash("processing_message")
                process_data(file_path)
                out_file = os.path.join(current_app.config['UPLOAD_FOLDER'], 'starCAT_output.tar.gz')
                return send_file(os.path.join(os.getcwd(), out_file), as_attachment=True)
            
            else:
                flash("select_ref_message") 

    return render_template('starcat/starcatpage.html', mc=mc, references=session.get('references'),
                            selected_ref = session.get('selected_ref'))


@bp.route('/set-session', methods=['POST'])
def set_session(selected_ref = None):
    # Add session variables. Update selected reference only to initialize or if passed to the function.
    session['references'] = ['', 'TCAT.V1', 'BCAT.V1']
    if (not session.get('selected_ref')) or (selected_ref!=None):
        session['selected_ref'] = selected_ref
    return redirect(url_for('bl_starcat.runstarcat'))


@bp.route('/choose-ref', methods=('GET', 'POST'))
def chooseref():    
    # Update reference 
    if request.method == 'POST':
        reference = request.form.get('ref')
        set_session(selected_ref = reference)
        return redirect(url_for('bl_starcat.runstarcat'))


def process_data(file_path):
    # Run starCAT
    out_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'starCAT_output')
    out_file = os.path.join(current_app.config['UPLOAD_FOLDER'], 'starCAT_output.tar.gz')
    os.makedirs(out_dir, exist_ok=True)

    cat = starCAT(reference=session.get('selected_ref'), cachedir=current_app.config['UPLOAD_FOLDER'])
    adata = cat.load_counts(file_path)
    usage, scores = cat.fit_transform(adata)
    cat.save_results(out_dir, 'starCAT')

    with tarfile.open(out_file, "w:gz") as tar:
        tar.add(out_dir, arcname = 'starCAT_output')


