.PHONY: test-leeloo

tests:
	docker-compose build --no-cache && docker-compose run leeloo pytest -s

flake8:
	docker-compose run leeloo flake8

docker-cleanup:
	docker rm -f `docker ps -qa` || echo

migrate:
	docker-compose run leeloo python manage.py migrate

makemigrations:
	docker-compose run leeloo python manage.py makemigrations

shellplus:
	docker-compose run leeloo python manage.py shell_plus --ipython

load-metadata:
	docker-compose run leeloo python manage.py loaddata /app/fixtures/metadata.yaml

load-undefined:
	docker-compose run leeloo python manage.py loaddata /app/fixtures/undefined.yaml

load-businesstypes:
	docker-compose run leeloo python manage.py loaddata /app/fixtures/datahub_businesstypes.yaml

load-all-metadata:	load-metadata load-undefined load-businesstypes
