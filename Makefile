.PHONY: test-leeloo

tessa:
	docker-compose build && docker-compose run leeloo pytest -s

docker-cleanup:
	docker rm -f `docker ps -qa` || echo
