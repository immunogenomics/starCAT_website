from flask import (
    Blueprint, render_template, url_for, current_app, abort, send_from_directory
)
from .layoutUtils import *
from .auth import *
from werkzeug.utils import safe_join
import pandas as pd
from minimal import reference_data

bp = Blueprint('bl_references', __name__, url_prefix='/references')

@bp.route('/',methods=('GET', 'POST'))
#@manage_cookie_policy
def refspawn():
    mc = set_menu("references")

    refdata = reference_data.copy()
    refdata['Download'] = ''
    for i in refdata.index:
        link = url_for("bl_references.download_file", filename=refdata.at[i, 'Name']+'.tar.gz')
        refdata.at[i, 'Download'] = '<a href="%s">Download</a>' % link
        publink = '<a href="%s">publication</a>' % refdata.at[i, 'Publication_Link']
        refdata.at[i, 'Description'] = refdata.at[i, 'Description'].replace('publication', publink)
        zenpath = '/'.join(refdata.at[i, 'Link'].split('/')[:-2])
        zenodolink = '<a href="%s">%s</a>' % (zenpath, refdata.at[i, 'Name'])
        refdata.at[i, 'Name'] = zenodolink

    cols = ['Name', 'Cell_Type', 'Tissue', 'Species', 'Contexts', 'Description', 'Download']
    skip_cols = ['Reference_Number', 'Version', 'Upload_Date', 'Link', 'Publication_Link', 'Author_Email',
       'Description']

    table_html = refdata[cols].to_html(classes='table table-striped table-hover',
                                        index=False, escape=False, justify='center')
    page_title = "This is a title that will end up in the page url"
    page_title_for_id = "This is a title that will end up in the page url"
    return render_template('references/referencespawn.html', mc=mc, 
        page_title=page_title, page_title_for_id=page_title_for_id,
        table_html=table_html)


# Route to handle file downloads
@bp.route('/download/<filename>')
def download_file(filename):
    try:
        # Define the directory where your .tar.gz files are stored
        reference_dir = os.path.join(current_app.root_path, 'static/reference_cache')

        # Securely join the directory and the filename
        file_path = safe_join(reference_dir, filename)

        # Check if the file exists and serve it
        if os.path.exists(file_path):
            return send_from_directory(reference_dir, filename, as_attachment=True)
        else:
            abort(404)
    except Exception as e:
        print(f"Error: {e}")
        abort(500)



@bp.route('/<slug>',methods=('GET', 'POST'))
#@manage_cookie_policy
def niceurl(slug=''):
    mc = set_menu("references")
    page_title = "This is a title that will end up in the page url"
    return render_template('references/pageniceurl.html', mc=mc, page_title=page_title)

@bp.route('/<slug>/<int:id>',methods=('GET', 'POST'))
#@manage_cookie_policy
def niceurlid(slug='', id=0):
    mc = set_menu("references")
    page_title_for_id = "This is a title that will end up in the page url"
    return render_template('references/pageniceurlid.html', mc=mc, page_title_for_id=page_title_for_id)
