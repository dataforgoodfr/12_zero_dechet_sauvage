FROM mageai/mageai:0.9.66

MAINTAINER Data4Good
LABEL version="0.1.0"
LABEL description="ETL pour le projet Zéro Dechet Sauvage de l'association MerTerre"

ENV HOME=/home/merterre

RUN useradd -m -d $HOME -s /bin/bash merterre
RUN mkdir -p $HOME/zds
WORKDIR $HOME/
RUN chown -R merterre:merterre $HOME

RUN mkdir /home/src/mage_data
RUN chown -R merterre:merterre /home/src/mage_data

USER merterre

CMD ["mage", "start", "zds"]
