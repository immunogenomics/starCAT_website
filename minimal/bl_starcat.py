from flask import (
    Blueprint, render_template, url_for, request, flash
)
from .layoutUtils import *
from .auth import *


bp = Blueprint('bl_starcat', __name__, url_prefix='/starcat')

@bp.route('/',methods=('GET', 'POST'))
#@manage_cookie_policy
def runstarcat():
    mc = set_menu("starcat")
    page_title = "This is a title that will end up in the page url"
    page_title_for_id = "This is a title that will end up in the page url"
    if request.method == 'POST':
        file = request.files['file']
        if file:
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)
            # Run the processing script on the uploaded file
            #result = process_data(file_path)
            #flash(f'Processing complete: {result}')
            #return redirect(url_for('bl_starcat.runstarcat'))
    return render_template('starcat/niceurlsspawn.html', mc=mc, 
        page_title=page_title, page_title_for_id=page_title_for_id)

def process_data(file_path):
    """
    Dummy processing function.
    Replace this with actual data processing logic.
    """
    # Open the file and process it
    with open(file_path, 'r') as file:
        data = file.read()

    # Here you can add the logic to process the data
    # For example, you can parse CSV files, run computations, etc.
    # This is a placeholder for demonstration purposes.
    processed_data = f"Data processed for file: {file_path}"

    return processed_data

'''
@bp.route('/',methods=('GET', 'POST'))
#@manage_cookie_policy
def niceurlsspawn():
    mc = set_menu("starcat")
    page_title = "This is a title that will end up in the page url"
    page_title_for_id = "This is a title that will end up in the page url"
    return render_template('starcat/niceurlsspawn.html', mc=mc, 
        page_title=page_title, page_title_for_id=page_title_for_id)

@bp.route('/<slug>',methods=('GET', 'POST'))
#@manage_cookie_policy
def niceurl(slug=''):
    mc = set_menu("starcat")
    page_title = "This is a title that will end up in the page url"
    return render_template('starcat/pageniceurl.html', mc=mc, page_title=page_title)

@bp.route('/<slug>/<int:id>',methods=('GET', 'POST'))
#@manage_cookie_policy
def niceurlid(slug='', id=0):
    mc = set_menu("starcat")
    page_title_for_id = "This is a title that will end up in the page url"
    return render_template('starcat/pageniceurlid.html', mc=mc, page_title_for_id=page_title_for_id)
'''