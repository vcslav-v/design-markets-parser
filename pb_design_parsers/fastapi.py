from fastapi import FastAPI
from pb_design_parsers.api.routes import routes

app = FastAPI(debug=True)

app.include_router(routes)
