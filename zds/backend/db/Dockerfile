FROM mysql:9.1.0

ENV MYSQL_DATABASE zero_dechet_sauvage

COPY ./scripts/setup_db.sql /docker-entrypoint-initdb.d/
