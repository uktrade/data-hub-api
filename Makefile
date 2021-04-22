tests:
	docker-compose build
	docker-compose run api bash tests.sh

flake8:
	docker-compose build
	docker-compose run api flake8

docker-cleanup:
	docker rm -f `docker ps -qa` || echo

migrate:
	docker-compose run api python manage.py migrate

makemigrations:
	docker-compose run api python manage.py makemigrations

shellplus:
	docker-compose run api python manage.py shell_plus --ipython

load-metadata:
	docker-compose run api python manage.py loadinitialmetadata

setup-flake8-hook:
	python3 -m venv env
	. env/bin/activate && pip install pre-commit && pre-commit install && git config --bool flake8.strict true

run-shell:
	docker-compose run api bash

run-test-reuse-db:
	docker-compose run api pytest --reuse-db -vv <Add Test File Path>

reindex-es:
	docker-compose run api python manage.py sync_es

fix-us-areas:
	docker-compose run api python manage.py fix_us_company_address

fix-ca-areas:
	docker-compose run api python manage.py fix_ca_company_address
