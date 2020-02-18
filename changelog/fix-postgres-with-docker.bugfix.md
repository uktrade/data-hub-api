A fix was made for environments using docker-compose which enables the postgres
image to start successfully. A `POSTGRES_PASSWORD` was added for each postgres
image and configs were updated accordingly.
