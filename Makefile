APP_NAME = pb_design_parsers
APP_AUTHOR = vaclav-v

FILE_VSCODE_SETTINGS = .vscode/settings.json

define VSCODE_SETTINGS
echo "{" >> $(FILE_VSCODE_SETTINGS)
echo "\"python.pythonPath\": \"`poetry show -v 2 | grep virtualenv | cut -d ' ' -f 3 | xargs` \"," >> $(FILE_VSCODE_SETTINGS)
echo "\"python.linting.pylintEnabled\": true," >> $(FILE_VSCODE_SETTINGS)
echo "\"python.linting.flake8Enabled\": true," >> $(FILE_VSCODE_SETTINGS)
echo "\"python.linting.mypyEnabled\": true," >> $(FILE_VSCODE_SETTINGS)
echo "\"python.linting.enabled\": true," >> $(FILE_VSCODE_SETTINGS)
echo "}" >> $(FILE_VSCODE_SETTINGS)

endef


FILE_GITIGNORE = .gitignore

define GITIGNORE
echo ".venv" >> $(FILE_GITIGNORE)
echo ".vscode" >> $(FILE_GITIGNORE)
echo "*_cache" >> $(FILE_GITIGNORE)
echo "__pycache__" >> $(FILE_GITIGNORE)
echo ".python-version" >> $(FILE_GITIGNORE)

endef


init:
	poetry init -n --name $(APP_NAME) --author $(APP_AUTHOR)
	poetry add --dev flake8
	poetry add --dev mypy
	mkdir .vscode
	touch $(FILE_VSCODE_SETTINGS)
	$(VSCODE_SETTINGS)
	touch $(FILE_GITIGNORE)
	$(GITIGNORE)
	mkdir $(APP_NAME)
	touch $(APP_NAME)/__init__.py
	echo '"""Main module $(APP_NAME) project."""' > $(APP_NAME)/__init__.py
	poetry shell
	flake8 --max-line-length 100

lint:
	poetry run flake8 $(APP_NAME)
	poetry run mypy $(APP_NAME)

install:
	poetry install

sqlalchemy:
	poetry add sqlalchemy
	poetry add psycopg2-binary
	poetry add alembic
	poetry run alembic init alembic

db_revision:
	poetry run alembic revision --autogenerate

db_update:
	poetry run alembic upgrade head
test:
	poetry run pytest tests/
test-full-diff:
	poetry run pytest -vv tests/
package-install:
	python3 -m pip -q install poetry
	poetry build -q
	python3 -m pip -q install --user dist/*.whl
coverage:
	poetry run pytest --cov=$(APP_NAME) --cov-report xml tests/

req:
	poetry export>requirements.txt

env:
	export FLASK_APP="gamemaster_bot.app"
	export DOMAIN=127.0.0.1:5000
	export BOT_TOKEN="386692915:AAFS9qFwTSkzSRVFjesBifBz3SjPAye4IOI"
	export DB_URL=127.0.0.1:8000
	export REDIS="localhost"
db:
	docker run --name test-postgres -e POSTGRES_PASSWORD=mysecretpassword -e POSTGRES_DB=postgres -d -p 5432:5432 postgres

req:
	poetry export -f requirements.txt --output requirements.txt --without-hashes