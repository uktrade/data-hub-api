tests:
	docker-compose build
	docker-compose run leeloo bash tests.sh

flake8:
	docker-compose build
	docker-compose run leeloo flake8

docker-cleanup:
	docker rm -f `docker ps -qa` || echo

migrate:
	docker-compose run leeloo python manage.py migrate

init-es:
	docker-compose run leeloo python manage.py init_es

makemigrations:
	docker-compose run leeloo python manage.py makemigrations

shellplus:
	docker-compose run leeloo python manage.py shell_plus --ipython

load-metadata:
	docker-compose run leeloo python manage.py loadinitialmetadata
