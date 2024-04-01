import streamlit as st
import altair as alt
import pandas as pd
import duckdb
import plotly.express as px
import folium
from folium import IFrame


# Page setting : wide layout
st.set_page_config(
    layout="wide", page_title="Dashboard Zéro Déchet Sauvage : onglet Data"
)

st.markdown(
    """# 🔎 Data
Visualisez les impacts sur les milieux naturels et secteurs/filières/marques à l’origine de cette pollution
"""
)

# Import des données

df_nb_dechet = pd.read_csv(
    (
        "https://github.com/dataforgoodfr/12_zero_dechet_sauvage/raw/2-"
        "nettoyage-et-augmentation-des-donn%C3%A9es/Exploration_visuali"
        "sation/data/data_releve_nb_dechet.csv"
    )
)

df_other = pd.read_csv(
    (
        "https://github.com/dataforgoodfr/12_zero_dechet_sauvage/raw/2-"
        "nettoyage-et-augmentation-des-donn%C3%A9es/Exploration_visuali"
        "sation/data/data_zds_enriched.csv"
    )
)


# 3 Onglets : Matériaux, Top déchets, Filières et marques
tab1, tab2, tab3 = st.tabs(
    [
        "Matériaux :wood:",
        "Top Déchets :wastebasket:",
        "Secteurs et marques :womans_clothes:",
    ]
)

# Onglet 1 : Matériaux
with tab1:

    # Transformation du dataframe pour les graphiques
    # Variables à conserver en ligne
    cols_identifiers = [
        "ANNEE",
        "TYPE_MILIEU",
        "INSEE_COM",
        "DEP",
        "REG",
        "EPCI",
        "BV2022",
    ]

    # variables à décroiser de la base de données correspondant aux Volume global de chaque matériau
    cols_volume = [k for k in df_other.columns if "GLOBAL_VOLUME_" in k]

    # Copie des données pour transfo
    df_volume = df_other.copy()

    # Calcul des indicateurs clés de haut de tableau avant transformation
    volume_total = df_volume["VOLUME_TOTAL"].sum()
    poids_total = df_volume["POIDS_TOTAL"].sum()
    volume_total_categorise = df_volume[cols_volume].sum().sum()
    pct_volume_cateforise = volume_total_categorise / volume_total
    nb_collectes = len(df_volume)

    # Dépivotage du tableau pour avoir une base de données exploitable
    df_volume = df_volume.melt(
        id_vars=cols_identifiers,
        value_vars=cols_volume,
        var_name="Matériau",
        value_name="Volume",
    )

    # Nettoyer le nom du Type déchet pour le rendre plus lisible
    df_volume["Matériau"] = (
        df_volume["Matériau"].str.replace("GLOBAL_VOLUME_", "").str.title()
    )

    # Grouper par type de matériau pour les visualisations
    df_totals_sorted = df_volume.groupby(["Matériau"], as_index=False)["Volume"].sum()
    df_totals_sorted = df_totals_sorted.sort_values(["Volume"], ascending=False)

    # Charte graphique MERTERRE :
    colors_map = {
        "Plastique": "#48BEF0",
        "Caoutchouc": "#364E74",
        "Bois": "#673C11",
        "Textile": "#C384B1",
        "Papier": "#CAA674",
        "Metal": "#A0A0A0",
        "Verre": "#3DCE89",
        "Autre": "#F3B900",
    }

    # Ligne 0 : Filtres géographiques
    l0_col1, l0_col2 = st.columns(2)
    filtre_niveaugeo = l0_col1.selectbox(
        "Niveau géo", ["Région", "Département", "EPCI", "Commune", "Bassin de vie"]
    )
    filtre_lieu = l0_col2.selectbox("Territoire", ["Ter1", "Ter2"])

    # Ligne 1 : 2 cellules avec les indicateurs clés en haut de page
    l1_col1, l1_col2, l1_col3 = st.columns(3)

    # Pour avoir 3 cellules avec bordure, il faut nester un st.container dans chaque colonne (pas d'option bordure dans st.column)

    # 1ère métrique : volume total de déchets collectés
    cell1 = l1_col1.container(border=True)
    cell1.metric("Volume de déchets collectés", f"{volume_total:.0f} litres")

    # 2ème métrique : poids
    cell2 = l1_col2.container(border=True)
    cell2.metric("Poids total collecté", f"{poids_total:.0f} kg")

    # 3ème métrique : nombre de relevés
    cell3 = l1_col3.container(border=True)
    cell3.metric("Nombre de collectes réalisées", f"{nb_collectes}")

    # Ligne 2 : 2 graphiques en ligne : donut et bar chart matériaux
    l2_col1, l2_col2 = st.columns(2)
    with l2_col1:

        # Création du diagramme en donut en utilisant le dictionnaire de couleurs pour la correspondance
        fig = px.pie(
            df_totals_sorted,
            values="Volume",
            names="Matériau",
            title="Répartition des matériaux en volume",
            hole=0.4,
            color="Matériau",  # Utilisation de 'index' pour le mappage des couleurs
            color_discrete_map=colors_map,
        )  # Application du dictionnaire de mappage de couleurs

        # Amélioration de l'affichage
        fig.update_traces(textinfo="percent")
        fig.update_layout(autosize=True, legend_title_text="Matériau")

        # Affichage du graphique
        st.plotly_chart(fig, use_container_width=True)

        st.write(
            f"Cette analyse se base sur les déchets qui ont pu être classés par matériau : {volume_total_categorise:.0f} Litres, soit {pct_volume_cateforise:.0%} du volume total"
        )

    with l2_col2:
        # Création du graphique en barres avec Plotly Express
        fig2 = px.bar(
            df_totals_sorted,
            x="Matériau",
            y="Volume",
            text="Volume",
            title="Volume total par materiau (en litres)",
            color="Matériau",
            color_discrete_map=colors_map,
        )

        # Amélioration du graphique
        fig2.update_traces(texttemplate="%{text:.2s}", textposition="outside")
        fig2.update_layout(
            autosize=True,
            uniformtext_minsize=8,
            uniformtext_mode="hide",
            xaxis_tickangle=90,
            showlegend=False,
        )

        # Affichage du graphique
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    # Ligne 3 : Graphe par milieu de collecte
    st.write("**Volume collecté par matériau en fonction du milieu de collecte**")

    # Part de volume collecté par type de milieu

    # Grouper par année et type de matériau
    df_typemilieu = df_volume.groupby(["TYPE_MILIEU", "Matériau"], as_index=False)[
        "Volume"
    ].sum()
    df_typemilieu = df_typemilieu.sort_values(
        ["TYPE_MILIEU", "Volume"], ascending=False
    )

    # Graphique à barre empilées du pourcentage de volume collecté par an et type de matériau
    fig3 = px.histogram(
        df_typemilieu,
        x="TYPE_MILIEU",
        y="Volume",
        color="Matériau",
        barnorm="percent",
        title="Répartition des matériaux en fonction du milieu de collecte",
        text_auto=False,
        color_discrete_map=colors_map,
    )

    fig3.update_layout(bargap=0.2)
    fig3.update_layout(yaxis_title="% du volume collecté", xaxis_title=None)

    # Afficher le graphique
    st.plotly_chart(fig3, use_container_width=True)

    st.divider()

    # Ligne 3 : Graphe par milieu de collecte
    st.write("**Détail par milieu, lieu ou année**")
    l3_col1, l3_col2, l3_col3 = st.columns(3)
    filtre_milieu = l3_col1.selectbox("Milieu", ["Test 1", "Test_2"], index=None)
    filtre_lieu = l3_col2.selectbox("Lieu", ["Lieu 1", "Lieu 2"], index=None)
    filtre_annee = l3_col3.selectbox("Année", [2020, 2021], index=None)

    # Ligne 4 : donut filtré et table de données
    l4_col1, l4_col2 = st.columns(2)
    with l4_col1:
        st.markdown("""**Répartition des matériaux collectés (% volume)**""")

    with l4_col2:
        st.markdown("""Table de données""")


# Onglet 2 : Top Déchets
        
# Préparation des datas pour l'onglet 2
df_top = df_nb_dechet.copy()
df_top_data_releves = df_other.copy()
# Filtration sur les type-regroupement selection dechets "GROUPE" uniquement
df_top_dechet_milieu = df_top[df_top["type_regroupement"].isin(['GROUPE'])]
#Ajout du type milieu et lieu




with tab2:
    st.markdown(
        """## Quels sont les types de déchets les plus présents sur votre territoire ?
    """
    )
    res_aggCategory_filGroup = duckdb.query(
        (
            "SELECT categorie, sum(nb_dechet) AS total_dechet "
            "FROM df_nb_dechet "
            "WHERE type_regroupement = 'GROUPE' "
            "GROUP BY categorie "
            "HAVING sum(nb_dechet) > 10000 "
            "ORDER BY total_dechet DESC;"
        )
    ).to_df()

    # st.bar_chart(data=res_aggCategory_filGroup, x="categorie", y="total_dechet")

    st.altair_chart(
        alt.Chart(res_aggCategory_filGroup)
        .mark_bar()
        .encode(
            x=alt.X("categorie", sort=None, title=""),
            y=alt.Y("total_dechet", title="Total de déchet"),
        ),
        use_container_width=True,
    )


# Onglet 3 : Secteurs et marques
with tab3:
    st.markdown(
        """## Quels sont les secteurs, filières et marques les plus représentés ?
    """
    )
