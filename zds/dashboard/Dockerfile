FROM python:3.11
MAINTAINER Data4Good
LABEL version="0.1.0"
LABEL description="Dashboard de l'application de visualisation \
de données du projet Zéro Dechet Sauvage de l'association MerTerre"

RUN apt-get update
RUN mkdir zds
RUN mkdir data
WORKDIR zds

RUN apt-get install -y locales
RUN echo "fr_FR.UTF-8 UTF-8" | tee -a /etc/locale.gen && locale-gen fr_FR.UTF-8

COPY app/ ./
RUN pip install -r requirements.txt

CMD ["streamlit", "run", "home.py", "--server.port=80"]
