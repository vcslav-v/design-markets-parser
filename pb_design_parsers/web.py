"""Web endpoints."""

import os

from flask import Flask, render_template, request
from werkzeug.utils import secure_filename

from pb_design_parsers import UPLOAD_DIR

app = Flask(__name__)


@app.route("/upload-data",  methods=['GET', 'POST'])
def upload_data():
    if request.method == 'POST':
        data_files = request.files.getlist('data_file')
        prefix = request.form.get('prefix')
        if data_files:
            upload(data_files, prefix)
    return render_template('upload_data.html')


def upload(files, prefix, directory=UPLOAD_DIR):
    if not os.path.isdir(directory):
        os.mkdir(directory)
    for up_file in files:
        filename = f'{prefix}-{secure_filename(up_file.filename)}'
        up_file.save(os.path.join(directory, filename))
