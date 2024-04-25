from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit_authenticator as stauth
import yaml
from st_pages import Page, show_pages
from yaml.loader import SafeLoader

# Configuration de la page
st.set_page_config(
    layout="wide",
    page_title="Dashboard Zéro Déchet Sauvage",
    page_icon=":dolphin:",
    menu_items={
        "About": "https://www.zero-dechet-sauvage.org/",
    },
)

# load and apply CSS styles
def load_css(file_name: str) -> None:
    with Path(file_name).open() as f:
        st.markdown(f"<style>{f.readline()}</style>", unsafe_allow_html=True)


# Login
p_cred = Path(".credentials.yml")
with p_cred.open() as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config["credentials"],
    config["cookie"]["name"],
    config["cookie"]["key"],
    config["cookie"]["expiry_days"],
    config["pre-authorized"],
)
authenticator.login(
    fields={
        "Form name": "Connexion",
        "Username": "Identifiant",
        "Password": "Mot de passe",
        "Login": "Connexion",
    },
)

if st.session_state["authentication_status"]:
    show_pages(
        [
            Page("home.py", "Accueil", "🏠"),
        ],
    )

    # Load and apply the CSS file at the start of your app
    # local debug
    load_css("style.css")

    st.markdown(
        """
    # Bienvenue 👋
    #### Visualiser les collectes de déchets qui ont lieu sur votre territoire !
    """,
    )

    st.markdown("""# À propos""")

    # Chargement des données et filtre géographique à l'arrivée sur le dashboard
    # Table des volumes par matériaux
    @st.cache_data
    def load_df_other() -> pd.DataFrame:
        df = pd.read_csv(
            "https://github.com/dataforgoodfr/12_zero_dechet_sauvage/raw/2-"
            "nettoyage-et-augmentation-des-donn%C3%A9es/Exploration_visuali"
            "sation/data/data_zds_enriched.csv",
        )
        # Ajout des colonnes DEP_CODE_NOM et COMMUNE_CODE_NOM qui concatenent le numéro INSEE
        # et le nom de l'entité géographique (ex : 13 - Bouches du Rhône)
        df["DEP_CODE_NOM"] = df["DEP"] + " - " + df["DEPARTEMENT"]
        df["COMMUNE_CODE_NOM"] = df["INSEE_COM"] + " - " + df["commune"]
        return df

    # Table des structures
    @st.cache_data
    def load_structures() -> pd.DataFrame:
        df = pd.read_csv(
            "https://github.com/dataforgoodfr/12_zero_dechet_sauvage/raw/4-"
            "onglet-structures/Exploration_visuali"
            "sation/data/structures_export_cleaned.csv",
            index_col=0,
        )
        # Ajout des colonnes DEP_CODE_NOM et COMMUNE_CODE_NOM qui concatenent le numéro INSEE
        # et le nom de l'entité géographique (ex : 13 - Bouches du Rhône)
        df["DEP_CODE_NOM"] = df["dep"] + " - " + df["departement"]
        df["COMMUNE_CODE_NOM"] = df["INSEE_COM"] + " - " + df["COMMUNE"]
        df.columns = [c.upper() for c in df.columns]
        return df

    # Table du nb de déchets
    @st.cache_data
    def load_df_nb_dechet() -> pd.DataFrame:
        return pd.read_csv(
            "https://github.com/dataforgoodfr/12_zero_dechet_sauvage/raw/2-"
            "nettoyage-et-augmentation-des-donn%C3%A9es/Exploration_visuali"
            "sation/data/data_releve_nb_dechet.csv",
        )

    # Appel des fonctions pour charger les données

    df_other = load_df_other()
    df_structures = load_structures()

    # Création du filtre par niveau géographique : correspondance labels et variables
    df_nb_dechets = load_df_nb_dechet()

    # Création du filtre par niveau géographique : correspondance labels et variables du df
    niveaux_admin_dict = {
        "Région": "REGION",
        "Département": "DEP_CODE_NOM",
        "EPCI": "LIBEPCI",
        "Commune": "COMMUNE_CODE_NOM",
    }

    # 1ère étape : sélection du niveau administratif concerné (région, dép...)
    # Si déjà saisi précédemment, initialiser le filtre avec les valeurs entrées précédemment
    # Récupérer les index pour conserver la valeur des filtres au changement de pages
    # Filtre niveau administratif
    niveau_admin = st.session_state.get("niveau_admin", None)
    index_admin = st.session_state.get("index_admin", None)
    # Filtre collectivité
    collectivite = st.session_state.get("collectivite", None)
    index_collec = st.session_state.get("index_collec", None)

    # Initialiser la selectbox avec l'index récupéré
    select_niveauadmin = st.selectbox(
        "Niveau administratif : ",
        niveaux_admin_dict.keys(),
        index=index_admin,
        placeholder="Choisir une option",
    )

    if select_niveauadmin is not None:
        # Filtrer la liste des collectivités en fonction du niveau admin
        liste_collectivites = df_other[niveaux_admin_dict[select_niveauadmin]]
        liste_collectivites = liste_collectivites.sort_values().unique()

        # 2ème filtre : sélection de la collectivité concernée
        select_collectivite = st.selectbox(
            "Collectivité : ",
            liste_collectivites,
            index=index_collec,
            placeholder="Choisir une collectivité",
        )

    button_disabled = not select_niveauadmin or not select_collectivite
    if st.button("Enregistrer la sélection", disabled=button_disabled):
        # Enregistrer les valeurs sélectionnées dans le session.state
        st.session_state["niveau_admin"] = select_niveauadmin
        st.session_state["index_admin"] = list(niveaux_admin_dict.keys()).index(
            select_niveauadmin,
        )

        st.session_state["collectivite"] = select_collectivite
        st.session_state["index_collec"] = list(liste_collectivites).index(
            select_collectivite,
        )

        # Afficher la collectivité sélectionnée
        st.write(f"Vous avez sélectionné : {select_niveauadmin} {select_collectivite}.")
        show_pages(
            [
                Page("home.py", "Accueil", "🏠"),
                Page("pages/structures.py", "Structures", "🔭"),
                Page("pages/actions.py", "Actions", "👊"),
                Page("pages/data.py", "Data", "🔍"),
                Page("pages/hotspots.py", "Hotspots", "🔥"),
            ],
        )

        # Filtrer et enregistrer le DataFrame dans un session state pour la suite
        colonne_filtre = niveaux_admin_dict[select_niveauadmin]
        df_other_filtre = df_other[df_other[colonne_filtre] == select_collectivite]
        st.session_state["df_other_filtre"] = df_other_filtre

        # Filtrer dataframe structures et enregistrer dans le session.state
        df_structures_filtre = df_structures[
            df_structures[colonne_filtre] == select_collectivite
        ]
        st.session_state["structures_filtre"] = df_structures_filtre
        st.session_state["structures"] = df_structures

        # Filtrer et enregistrer le dataframe nb_dechets dans session.State
        # Récuperer la liste des relevés
        id_releves = df_other_filtre["ID_RELEVE"].unique()
        # Filtrer df_nb_dechets sur la liste des relevés
        st.session_state["df_nb_dechets_filtre"] = df_nb_dechets[
            df_nb_dechets["ID_RELEVE"].isin(id_releves)
        ]

        # Afficher le nombre de relevés disponibles
        nb_releves = len(st.session_state["df_other_filtre"])
        st.write(
            f"{nb_releves} relevés de collecte sont disponibles \
                pour l'analyse sur votre territoire.",
        )

    authenticator.logout()
elif st.session_state["authentication_status"] is False:
    st.error("Mauvais identifiants ou mot de passe.")
elif st.session_state["authentication_status"] is None:
    st.warning("Veuillez entrer votre identifiant et mot de passe")

    show_pages(
        [
            Page("home.py", "Home", "🏠 "),
            Page("pages/register.py", "S'enregistrer", "🚀"),
        ],
    )
