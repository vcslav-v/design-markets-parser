"""Web endpoints."""

import os

from flask import Flask, render_template, request
from werkzeug.utils import secure_filename

from pb_design_parsers import UPLOAD_DIR, CM_PB_PREFIX

app = Flask(__name__)


@app.route("/upload-data",  methods=['GET', 'POST'])
def upload_data():
    if request.method == 'POST':
        cm_pb_data_files = request.files.getlist('cm_pb_data_file')
        if cm_pb_data_files:
            upload(cm_pb_data_files, CM_PB_PREFIX)
    return render_template('upload_data.html')


def upload(files, prefix, directory=UPLOAD_DIR):
    if not os.path.isdir(directory):
        os.mkdir(directory)
    for up_file in files:
        filename = f'{prefix}-{secure_filename(up_file.filename)}'
        up_file.save(os.path.join(directory, filename))
