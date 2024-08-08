from flask import (
    Blueprint, render_template, url_for
)
from .layoutUtils import *
from .auth import *

bp = Blueprint('bl_references', __name__, url_prefix='/references')

@bp.route('/',methods=('GET', 'POST'))
#@manage_cookie_policy
def refspawn():
    mc = set_menu("references")
    page_title = "This is a title that will end up in the page url"
    page_title_for_id = "This is a title that will end up in the page url"
    return render_template('references/referencespawn.html', mc=mc, 
        page_title=page_title, page_title_for_id=page_title_for_id)

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
