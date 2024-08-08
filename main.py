from minimal import create_app
import os

os.environ["SESSION_SECRET"]="MySessionSecret" 

app = create_app()
app.config['UPLOAD_FOLDER'] = './uploads'
app.run(port=8001)
