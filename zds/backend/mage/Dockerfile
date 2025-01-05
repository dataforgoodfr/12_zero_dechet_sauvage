FROM mageai/mageai:0.9.66

MAINTAINER Data4Good
LABEL version="0.1.0"
LABEL description="ETL pour le projet Zéro Dechet Sauvage de l'association MerTerre"

ENV HOME=/home/merterre
ARG ADMINEXPRESSURL

RUN apt update
RUN apt install -y p7zip-full

RUN useradd -m -d $HOME -s /bin/bash merterre
WORKDIR $HOME/
RUN chown -R merterre:merterre $HOME

RUN mkdir /home/src/mage_data
RUN chown -R merterre:merterre /home/src/mage_data

RUN pip uninstall -y openpyxl

USER merterre

RUN wget $ADMINEXPRESSURL
RUN 7z x ADMIN-EXPRESS* && rm ADMIN-EXPRESS*.7z
RUN mkdir open_data/
RUN find ./ -name COMMUNE.* | xargs cp -t open_data/
RUN rm -r ADMIN-EXPRESS*

COPY ./requirements.txt .
RUN pip install -r requirements.txt

CMD ["mage", "start", "zds"]
