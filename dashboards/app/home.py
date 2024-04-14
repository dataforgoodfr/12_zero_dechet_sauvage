from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit_authenticator as stauth
import yaml
from st_pages import Page, show_pages
from yaml.loader import SafeLoader

st.markdown(
    """
# Bienvenue 👋
#### Visualiser les collectes de déchets qui ont lieu sur votre territoire !
""",
)

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
            Page("pages/actions.py", "Actions", "👊"),
            Page("pages/data.py", "Data", "🔍"),
            Page("pages/hotspots.py", "Hotspots", "🔥"),
            Page("pages/structures.py", "Structures", "🔭"),
        ],
    )
    st.markdown("""# À propos""")

    # Chargement des données géographiques pour le filtre : une seule fois à l'arrivée
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

    # Appel des fonctions pour charger les données

    df_other = load_df_other()

    # TODO : Raccourcir commentaire
    # Création du filtre par niveau géographique
    # : correspondance labels et variables du dataframe
    niveaux_admin_dict = {
        "Région": "REGION",
        "Département": "DEP_CODE_NOM",
        "EPCI": "LIBEPCI",
        "Commune": "COMMUNE_CODE_NOM",
    }

    # 1ère étape : sélection du niveau administratif concerné (région, dép...)
    # Si déjà saisi précédemment, initialiser le filtre avec la valeur
    index_admin = st.session_state.get("niveau_admin", None)
    select_niveauadmin = st.selectbox(
        "Niveau administratif : ",
        niveaux_admin_dict.keys(),
        index=1,
        key="niveau_admin",
    )

    if select_niveauadmin is not None:
        # Extraction de la liste depuis le dataframe
        liste_collectivites = df_other[niveaux_admin_dict[select_niveauadmin]]
        liste_collectivites = liste_collectivites.sort_values().unique()

        # 2ème filtre : sélection de la collectivité concernée
        index_collec = st.session_state.get("collectivite", None)
        select_collectivite = st.selectbox(
            "Collectivité : ",
            liste_collectivites,
            index=2,
            key="collectivite",
        )
    else:
        st.caption(
            "Choisissez un niveau administratif pour afficher la liste des collectivités.",
        )

    if st.button("Enregistrer la sélection"):
        # Retourner le filtre validé et le nombre de relevés disponibles
        filtre_niveau = st.session_state["niveau_admin"]
        filtre_collectivite = st.session_state["collectivite"]
        st.write(f"Vous avez sélectionné : {filtre_niveau} {filtre_collectivite}.")

        # TODO : Raccourcir commentaire
        # Enregistrer le DataFrame dans un
        # "session state" pour conserver le filtre dans les onglets
        colonne_filtre = niveaux_admin_dict[filtre_niveau]
        st.session_state["df_other"] = df_other[
            df_other[colonne_filtre] == filtre_collectivite
        ]

        nb_releves = len(st.session_state["df_other"])
        st.write(
            f"{nb_releves} relevés de collecte disponibles \
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
