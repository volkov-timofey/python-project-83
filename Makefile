#Makefile

install:
	poetry install

dev:
	poetry run flask --app page_analyzer:app run
	
lint: # run_linter
	poetry run flake8 hexlet-code	
	
PORT ?= 8000
start:
	poetry run gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app	
	

test:
	poetry run pytest

test-coverage:
	poetry run pytest --cov=gendiff --cov-report xml

gendiff: # run gendiff
	poetry run gendiff

build: # build project
	poetry build

publish: # publish without PyPI
	poetry publish --dry-run

package-install:
	python3 -m pip install --user --force-reinstall dist/*.whl

lint: # run_linter
	poetry run flake8 gendiff
	
full: build publish package-install

check: test lint

selfcheck:
	check