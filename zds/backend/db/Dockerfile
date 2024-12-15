FROM mysql:9.1.0

ENV MYSQL_DATABASE zero_dechet_sauvage

COPY ./scripts/setup_db.sql /docker-entrypoint-initdb.d/

COPY ./.mysql_root_password /.mysql_root_password
COPY ./.mysql_merterre_password /.mysql_merterre_password
COPY ./scripts/create_merterre.sql create_merterre.sql
COPY ./create_merterre.sh /docker-entrypoint-initdb.d/
