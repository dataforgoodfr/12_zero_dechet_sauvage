import pandas as pd
import streamlit as st

st.markdown(
    """
# Bienvenue 👋
#### Visualiser les collectes de déchets qui ont lieu sur votre territoire !
""",
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


# Création du filtre par niveau géographique : correspondance labels et variables du dataframe
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
    )


if st.button("Enregistrer la sélection"):
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

    # Filtrer et enregistrer le DataFrame dans un "session state" pour les onglets suivants
    colonne_filtre = niveaux_admin_dict[select_niveauadmin]
    st.session_state["df_other_filtre"] = df_other[
        df_other[colonne_filtre] == select_collectivite
    ]

    nb_releves = len(st.session_state["df_other_filtre"])
    st.write(
        f"{nb_releves} relevés de collecte disponibles \
             pour l'analyse sur votre territoire.",
    )
