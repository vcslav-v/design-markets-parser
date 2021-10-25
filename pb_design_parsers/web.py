"""Web endpoints."""

import os
from datetime import datetime
from threading import Thread
from loguru import logger

from flask import Flask, render_template, request
from werkzeug.utils import secure_filename

from pb_design_parsers import creative
from pb_design_parsers import SPLITTER, UPLOAD_DIR

app = Flask(__name__)


@app.route("/upload-data",  methods=['GET', 'POST'])
def upload_data():
    if request.method == 'POST':
        data_files = request.files.getlist('data_file')
        prefix = request.form.get('prefix')
        if data_files:
            upload(data_files, prefix)
    return render_template('upload_data.html')


@app.route("/upload-data-manual",  methods=['GET', 'POST'])
def upload_data_manual():
    if request.method == 'POST':
        data_files = request.files.getlist('data_file')
        prefix = request.form.get('prefix')
        market_place, username, *_ = prefix.split()
        if data_files:
            upload(data_files, prefix)

            if market_place == 'cm':
                thread = Thread(
                    target=creative.add_data,
                    args=(username,)
                )
                thread.start()
    return render_template('upload_data_manual.html')


def upload(files, prefix, directory=UPLOAD_DIR):
    if not os.path.isdir(directory):
        os.mkdir(directory)
    for up_file in files:
        timestamp = int(datetime.utcnow().timestamp())
        filename = f'{prefix}{SPLITTER}{timestamp}{SPLITTER}{secure_filename(up_file.filename)}'
        up_file.save(os.path.join(directory, filename))
        logger.debug(os.listdir(directory))


def get_username(prexix: str) -> str:
    return prexix.split()[1]
