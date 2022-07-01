start-dev:
	[ -z "$(shell docker network ls --filter=name=data-infrastructure-shared-network -q)" ] && docker network create data-infrastructure-shared-network || echo 'data-infrastructure-shared-network network already present'
	docker-compose -f docker-compose.yml -f docker-compose.single-network.yml up &

stop-dev:
	docker-compose -f docker-compose.yml -f docker-compose.single-network.yml down

start-rq-mon:
	docker-compose -f docker-compose.yml -f docker-compose-rq-monitor.yml up &

stop-rq-mon:
	docker-compose -f docker-compose.yml -f docker-compose-rq-monitor.yml down

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
	docker-compose run api python manage.py loadinitialmetadata --force

setup-flake8-hook:
	python3 -m venv env
	. env/bin/activate && pip install pre-commit && pre-commit install && git config --bool flake8.strict true

run-shell:
	docker-compose run api bash

run-test-reuse-db:
	docker-compose run api pytest --reuse-db -vv datahub/core/test/test_cache.py datahub/email_ingestion/test/test_tasks.py

reindex-opensearch:
	docker-compose run api python manage.py sync_search

fix-us-areas:
	docker-compose run api python manage.py fix_us_company_address

fix-ca-areas:
	docker-compose run api python manage.py fix_ca_company_address

start-frontend-api-dnb:
	$(MAKE) -C ../dnb-service start-dnb-for-data-hub-api
	$(MAKE) -C ../data-hub-frontend start-dev

stop-frontend-api-dnb:
	$(MAKE) -C ../dnb-service stop-dnb-for-data-hub-api
	$(MAKE) -C ../data-hub-frontend stop-dev
