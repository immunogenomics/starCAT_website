from minimal import create_app
import os
import time
import threading
import shutil


def clear_uploads():
    '''Remove file uploads older than 1 hr.'''
    max_age_seconds = 3600  
    while True:
        current_time = time.time()
        for subdir in os.listdir(app.config['UPLOAD_FOLDER']):
            subdir_path = os.path.join(app.config['UPLOAD_FOLDER'], subdir)
            if (os.path.isdir(subdir_path)) and (subdir not in ['TCAT.V1', 'BCAT.V1']):
                last_modified_time = os.path.getmtime(subdir_path)
                directory_age = current_time - last_modified_time
                if directory_age > max_age_seconds:
                    shutil.rmtree(subdir_path)
                    print(f'Deleted: {subdir_path}')
        time.sleep(300)


if __name__ == "__main__":
    app = create_app()
    threading.Thread(target=clear_uploads, daemon=True).start()
    app.run(port=8001)
