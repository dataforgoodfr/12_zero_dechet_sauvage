import streamlit as st
import altair as alt
import duckdb
import pandas as pd
import plotly.express as px


# Configuration de la page
st.set_page_config(
    layout="wide", page_title="Dashboard Zéro Déchet Sauvage : onglet Structures"
)

st.markdown(
    """# 🔭 Structures
*Quels sont les acteurs impliqués sur mon territoire ?*
"""
)


# Récupérer les filtres géographiques s'ils ont été fixés
filtre_niveau = st.session_state.get("niveau_admin", "")
filtre_collectivite = st.session_state.get("collectivite", "")


# Appeler les dataframes filtrés depuis le session state
if "structures" not in st.session_state:
    st.write(
        """
            ### :warning: Merci de sélectionner une collectivité\
            dans l'onglet Home pour afficher les données. :warning:
            """
    )
    st.stop()
else:
    df_structures = st.session_state["structures"]

# # df_nb_dechet = pd.read_csv(
# #     (
# #         "https://github.com/dataforgoodfr/12_zero_dechet_sauvage/raw/2-"
# #         "nettoyage-et-augmentation-des-donn%C3%A9es/Exploration_visuali"
# #         "sation/data/data_releve_nb_dechet.csv"
# #     )
# # )

# # df_other = pd.read_csv(
# #     (
# #         "https://github.com/dataforgoodfr/12_zero_dechet_sauvage/raw/2-"
# #         "nettoyage-et-augmentation-des-donn%C3%A9es/Exploration_visuali"
# #         "sation/data/data_zds_enriched.csv"
# #     )
# # )

# # res_aggCategory_filGroup = duckdb.query(
# #     (
# #         "SELECT categorie, sum(nb_dechet) AS total_dechet "
# #         "FROM df_nb_dechet "
# #         "WHERE type_regroupement = 'GROUPE' "
# #         "GROUP BY categorie "
# #         "HAVING sum(nb_dechet) > 10000 "
# #         "ORDER BY total_dechet DESC;"
# #     )
# # ).to_df()

# # st.bar_chart(data=res_aggCategory_filGroup, x="categorie", y="total_dechet")

# st.altair_chart(
#     alt.Chart(res_aggCategory_filGroup)
#     .mark_bar()
#     .encode(
#         x=alt.X("categorie", sort=None, title=""),
#         y=alt.Y("total_dechet", title="Total de déchet"),
#     ),
#     use_container_width=True,
# )

if filtre_niveau == "" and filtre_collectivite == "":
    st.write("Aucune sélection de territoire n'a été effectuée")
else:
    st.write(f"Votre territoire : {filtre_niveau} {filtre_collectivite}")


# Ligne 1 : 2 cellules avec les indicateurs clés en haut de page
l1_col1, l1_col2 = st.columns(2)

# Pour avoir une  bordure, il faut nester un st.container dans chaque colonne (pas d'option bordure dans st.column)

# 1ère métrique : nombre d'acteurs
cell1 = l1_col1.container(border=True)
nb_acteurs = len(df_structures)
# Trick pour séparer les milliers
cell1.metric("Acteurs présents sur le territoire", nb_acteurs)

# 2ème métrique : nb de spots adoptés
cell2 = l1_col2.container(border=True)
nb_spots_adoptes = df_structures["A1S_NB_SPOTS_ADOPTES"].sum()
cell2.metric("Spots adoptés", nb_spots_adoptes)


# Ligne 2 : 2 graphiques en ligne : carte et pie chart type de structures

# l2_col1, l2_col2 = st.columns(2)
# cell4 = l2_col1.container(border=True)
# cell5 = l2_col2.container(border=True)

with st.container():

    df_aggType = duckdb.query(
        (
            "SELECT TYPE, count(TYPE) AS nb_structures "
            "FROM df_structures "
            "GROUP BY TYPE "
            "ORDER BY nb_structures DESC;"
        )
    ).to_df()

    # Création du diagramme en donut en utilisant le dictionnaire de couleurs pour la correspondance
    fig = px.pie(
        df_aggType,
        values="nb_structures",
        names="TYPE",
        title="Répartition des types de structures",
        hole=0.4,
        color="TYPE",
    )

    # Amélioration de l'affichage
    # Change the percent format to round to integer
    fig.update_traces(
        textinfo="percent",
        texttemplate="%{percent:.0%}",
        textfont_size=16,
    )
    fig.update_layout(
        autosize=True,
        legend_title_text="Type de structure",
    )

    # Affichage du graphique
    st.plotly_chart(fig, use_container_width=True)

# Cartographie des structures
with st.container():
    st.markdown(""" **Cartographie des structures du territoire**""")


# Affichage du dataframe
with st.container():
    st.markdown(""" **Structures du territoire**""")
    df_struct_simplifie = duckdb.query(
        (
            "SELECT NOM as Nom, TYPE, ACTION_RAMASSAGE AS 'Nombre de collectes', A1S_NB_SPOTS_ADOPTES as 'Nombre de spots adoptés' "
            "FROM df_structures "
            "ORDER BY Nom DESC;"
        )
    ).to_df()

    st.dataframe(df_struct_simplifie, hide_index=True)
