import os
import io
import secrets

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from pb_design_parsers import creative, db_tools, schemas
from pb_design_parsers.api import service

router = APIRouter()
security = HTTPBasic()

username = os.environ.get('API_USERNAME', 'api')
password = os.environ.get('API_PASSWORD', 'pass')


def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, username)
    correct_password = secrets.compare_digest(credentials.password, password)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect username or password',
            headers={'WWW-Authenticate': 'Basic'},
        )
    return credentials.username


@router.post('/get_creators')
def get_creators(_: str = Depends(get_current_username)) -> schemas.creators:
    return db_tools.get_creators()

@router.post('/get_markets')
def get_markets(_: str = Depends(get_current_username)) -> schemas.market_places:
    return db_tools.get_markets()

@router.post('/post_sale_file')
def post_sale_file(prefix: str, file: UploadFile):
    market_place, username, *_ = prefix.split()
    with io.StringIO(file.file.read().decode()) as file_stream:
        if market_place == 'cm':
            creative.add_data(username, file_stream)
    


@router.post('/post_product')
def post_product(product_info: schemas.product, _: str = Depends(get_current_username)) -> schemas.result:
    result = schemas.result()
    try:
        product_info.items = service.collect_name_and_cat(product_info.items)
    except ValueError as e:
        result.status = 500 
        result.arg = e.args[0]
        return result
    for item in product_info.items:
        try:
            item.ident = db_tools.add_product_item(item)
        except Exception as e:
            result.status = 500 
            result.arg = 'DB problem'
            return result
    try:
        db_tools.make_product(product_info)
    except ValueError as e:
            result.status = 500 
            result.arg = e.args[0]
            return result
    return result
