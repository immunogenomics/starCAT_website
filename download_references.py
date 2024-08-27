import subprocess as sp
import pandas as pd
from minimal import refurl
import os

outdir = './minimal/static/reference_cache/'
refdata = pd.read_csv(refurl, sep='\t', comment='#')

if not os.path.exists(outdir):
	os.mkdir(outdir)

for i in refdata.index:
	link = refdata.at[i, 'Link']
	fn = os.path.basename(link)
	cmd = 'wget -O %s %s' % (os.path.join(outdir, fn), link)
	sp.call(cmd, shell=True)