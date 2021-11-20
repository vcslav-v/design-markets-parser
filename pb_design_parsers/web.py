"""Web endpoints."""

import os
from datetime import datetime
from threading import Thread
from loguru import logger

from flask import Flask, render_template, request, redirect, url_for
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from pb_design_parsers import creative, db_tools
from pb_design_parsers import SPLITTER, UPLOAD_DIR

app = Flask(__name__)
auth = HTTPBasicAuth()
app.config['SECRET_KEY'] = os.environ.get('FLASK_KEY') or 'you-will-never-guess'
users = {
    os.environ.get('FLASK_LOGIN') or 'root': generate_password_hash(
        os.environ.get('FLASK_PASS') or 'pass'
    ),
}


@auth.verify_password
def verify_password(username, password):
    if username in users and \
            check_password_hash(users.get(username), password):
        return username


@app.route('/upload-data',  methods=['GET', 'POST'])
def upload_data():
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
    return render_template('upload_data.html')


@app.route('/')
@auth.login_required
def index():
    return redirect(url_for('product_merge'))


@app.route('/product-merge',  methods=['GET', 'POST'])
@auth.login_required
def product_merge():
    if request.method == 'POST':
        product_for_divide = request.form.get('divide')
        if product_for_divide and product_for_divide.isdecimal():
            db_tools.divide_product(int(product_for_divide))
        else:
            for raw_main_product, raw_additional_product in request.form.items():
                main_product = raw_main_product.split()[0]
                if main_product.isdecimal():
                    main_product = int(main_product)
                else:
                    break

                if raw_additional_product.isdecimal():
                    additional_product = int(raw_additional_product)
                else:
                    break

                db_tools.merge_products(main_product, additional_product)

    products_info = db_tools.get_all_products_info()
    return render_template('product_merge.html', products_info=products_info)


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
