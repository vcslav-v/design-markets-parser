"""Web endpoints."""

import os
from datetime import datetime
from threading import Thread
from loguru import logger

from flask import Flask, render_template, request, redirect, url_for, flash
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
    return redirect(url_for('cur_products'))


@app.route('/make',  methods=['GET', 'POST'])
@auth.login_required
def make_products():
    found_items = []
    creators = db_tools.get_creators()
    free_cm_products = db_tools.get_free_cm_products()
    markets = db_tools.get_markets()
    if request.method == 'POST':
        btn = request.form.get('btn')
        if btn == 'submit':
            product_name = request.form.get('product_name')
            creator_id = int(request.form.get('creator'))
            item_ids = []
            for key, value in request.form.to_dict().items():
                kw, *_ = key.split(':')
                if kw == 'item_id' and value:
                    try:
                        item_ids.append(int(value))
                    except ValueError:
                        flash('Use numbers, jerk!')
            db_tools.make_product(
                product_name,
                creator_id,
                item_ids,
            )
            
        elif btn == 'find':
            item_name = request.form.get('product_name')
            found_items = db_tools.find_product_items_by_name(item_name)

    return render_template(
        'make_products.html',
        creators = creators,
        found_items=found_items,
        free_cm_products=free_cm_products,
        markets=markets,
    )

@app.route('/products',  methods=['GET'])
@auth.login_required
def cur_products():
    products_info = db_tools.get_all_products_info()
    return render_template('products_list.html', products_info=products_info)

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
