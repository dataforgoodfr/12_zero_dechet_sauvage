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
if "structures_filtre" not in st.session_state:
    st.write(
        """
            ### :warning: Merci de sélectionner une collectivité\
            dans l'onglet Home pour afficher les données. :warning:
            """
    )
    st.stop()
else:
    df_structures = st.session_state["structures_filtre"]

# Appeler les dataframes filtrés depuis le session state
if "df_other_filtre" not in st.session_state:
    st.write(
        """
            ### :warning: Merci de sélectionner une collectivité\
            dans l'onglet Home pour afficher les données. :warning:
            """
    )
    st.stop()
else:
    df_releves = st.session_state["df_other_filtre"]

if "structures" not in st.session_state:
    st.write(
        """
            ### :warning: Merci de sélectionner une collectivité\
            dans l'onglet Home pour afficher les données. :warning:
            """
    )
    st.stop()
else:
    df_structures_full = st.session_state["structures"]

if filtre_niveau == "" and filtre_collectivite == "":
    st.write("Aucune sélection de territoire n'a été effectuée")
else:
    st.write(f"Votre territoire : {filtre_niveau} {filtre_collectivite}")

dict_agg_df_releves = {"DATE": "max", "ID_RELEVE": "count"}
df_releve_structure = (
    df_releves.groupby(["ID_STRUCTURE"]).agg(dict_agg_df_releves).reset_index()
)
df_releve_structure.rename(
    columns={"DATE": "Date dernière collecte", "ID_RELEVE": "Nombre de relevés"},
    inplace=True,
)

df_structures = df_structures.merge(
    df_releve_structure, how="left", left_on="ID_STRUCT", right_on="ID_STRUCTURE"
)
df_structures["Nombre de relevés"].fillna(0, inplace=True)
df_structures["Date dernière collecte"].fillna(" ", inplace=True)


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
nb_spots_adoptes = df_structures["A1S_NB_SPO"].sum()
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


@st.cache_data(show_spinner=False)
def split_frame(input_df, rows):
    df = [input_df.loc[i : i + rows - 1, :] for i in range(0, len(input_df), rows)]
    return df


# Affichage du dataframe
with st.container():
    st.markdown(""" **Structures du territoire**""")
    df_struct_simplifie = duckdb.query(
        (
            """SELECT 
                    NOM_structure as Nom, 
                    TYPE as Type, 
                    "Nombre de relevés",
                    A1S_NB_SPO as 'Nombre de spots adoptés',
                    "Date dernière collecte"
            FROM df_structures 
            ORDER BY Nom DESC;"""
        )
    ).to_df()
    top_menu = st.columns(2)
    with top_menu[0]:
        sort_field = st.selectbox(
            "Trier par",
            options=[
                "Nombre de relevés",
                "Type",
                "Nombre de spots adoptés",
                "Date dernière collecte",
            ],
        )
    with top_menu[1]:
        sort_direction = st.radio("Direction", options=["⬇️", "⬆️"], horizontal=True)
    df_struct_simplifie = df_struct_simplifie.sort_values(
        by=sort_field, ascending=sort_direction == "⬆️", ignore_index=True
    )
    pagination = st.container()

    bottom_menu = st.columns((4, 1, 1))
    with bottom_menu[2]:
        batch_size = st.selectbox("Taille Page", options=[10, 20])
    with bottom_menu[1]:
        total_pages = (
            int(len(df_struct_simplifie) / batch_size)
            if int(len(df_struct_simplifie) / batch_size) > 0
            else 1
        )
        current_page = st.number_input(
            "Page", min_value=1, max_value=total_pages, step=1
        )
    with bottom_menu[0]:
        st.markdown(f"Page **{current_page}** sur **{total_pages}** ")

    pages = split_frame(df_struct_simplifie, batch_size)
    pagination.dataframe(data=pages[current_page - 1], use_container_width=True)
