import streamlit as st

# import altair as alt
import pandas as pd

# import duckdb
import plotly.express as px
import folium
from folium import IFrame
from streamlit_dynamic_filters import DynamicFilters

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

# Ajout des colonnes DEP_CODE_NOM et COMMUNE_CODE_NOM qui concatenent le numéro INSEE et le nom de l'entité géographique (ex : 13 - Bouches du Rhône)
df_other["DEP_CODE_NOM"] = df_other["DEP"] + " - " + df_other["DEPARTEMENT"]
df_other["COMMUNE_CODE_NOM"] = df_other["INSEE_COM"] + " - " + df_other["commune"]


# Création du filtre dynamique par niveau géographique
niveaux_geo = ["REGION", "DEP_CODE_NOM", "LIBEPCI", "BASSIN_DE_VIE", "COMMUNE_CODE_NOM"]
dynamic_filters = DynamicFilters(df_other, filters=niveaux_geo)
df_other_filtre = dynamic_filters.filter_df()

# 3 Onglets : Matériaux, Top déchets, Filières et marques
tab1, tab2, tab3 = st.tabs(
    [
        "Matériaux :wood:",
        "Top Déchets :wastebasket:",
        "Secteurs et marques :womans_clothes:",
    ]
)

# Creation des dictionnaires pour filtration des graphiques:
collectivites_dict = {
    "Région": df_other["REGION"].unique().tolist(),
    "Département": df_other["DEPARTEMENT"].unique().tolist(),
    "EPCI": df_other["EPCI"].unique().tolist(),
    "Commune": df_other["commune"].unique().tolist(),
    "Bassin de vie": df_other["BASSIN_DE_VIE"].unique().tolist(),
    "LIB EPCI": df_other["LIBEPCI"].unique().tolist(),
    "NATURE EPCI": df_other["NATURE_EPCI"].unique().tolist(),
}

milieu_lieu_dict = (
    df_other.groupby("TYPE_MILIEU")["TYPE_LIEU"]
    .unique()
    .apply(lambda x: x.tolist())
    .to_dict()
)

annee_liste = sorted(df_other["ANNEE"].unique().tolist(), reverse=True)

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
    df_volume = df_other_filtre.copy()

    # Calcul des indicateurs clés de haut de tableau avant transformation
    volume_total = df_volume["VOLUME_TOTAL"].sum()
    poids_total = df_volume["POIDS_TOTAL"].sum()
    volume_total_categorise = df_volume[cols_volume].sum().sum()
    pct_volume_categorise = volume_total_categorise / volume_total
    nb_collectes = len(df_volume)

    # estimation du poids categorisée en utilisant pct_volume_categorise
    poids_total_categorise = round(poids_total * pct_volume_categorise)

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
    # Popover cell
    #    with st.popover("Filtres géographiques", help = "Sélectionnez le niveau géographique souhaité pour afficher les indicateurs") :

    dynamic_filters.display_filters(location="sidebar")
    # filtre_region = st.selectbox(
    #    "Région :", collectivites_dict["Région"],
    #    index=None
    # )

    # Ligne 1 : 2 cellules avec les indicateurs clés en haut de page
    l1_col1, l1_col2, l1_col3 = st.columns(3)

    # Pour avoir 3 cellules avec bordure, il faut nester un st.container dans chaque colonne (pas d'option bordure dans st.column)

    # 1ère métrique : volume total de déchets collectés
    cell1 = l1_col1.container(border=True)
    # Trick pour séparer les milliers
    volume_total = f"{volume_total:,.0f}".replace(",", " ")
    cell1.metric("Volume de déchets collectés", f"{volume_total} litres")

    # 2ème métrique : poids
    cell2 = l1_col2.container(border=True)
    poids_total = f"{poids_total:,.0f}".replace(",", " ")

    cell2.metric("Poids total collecté", f"{poids_total} kg")

    # 3ème métrique : nombre de relevés
    cell3 = l1_col3.container(border=True)
    nb_collectes = f"{nb_collectes:,.0f}".replace(",", " ")
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

    st.write("")
    st.caption(
        f"Note : Cette analyse se base sur les déchets qui ont pu être classés par matériau : {volume_total_categorise:.0f} Litres, soit {pct_volume_categorise:.0%} du volume total collecté."
    )

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
with tab2:

    # Ligne 1 : 3 cellules avec les indicateurs clés en haut de page
    l1_col1, l1_col2, l1_col3 = st.columns(3)
    # Pour avoir 3 cellules avec bordure, il faut nester un st.container dans chaque colonne (pas d'option bordure dans st.column)
    # 1ère métrique : volume total de déchets collectés
    cell1 = l1_col1.container(border=True)
    # Trick pour séparer les milliers

    volume_total_categorise = f"{volume_total_categorise:,.0f}".replace(",", " ")
    cell1.metric("Volume de déchets catégorisés", f"{volume_total_categorise} litres")

    # 2ème métrique : poids
    cell2 = l1_col2.container(border=True)
    poids_total_categorise = f"{poids_total_categorise:,.0f}".replace(",", " ")
    # poids_total = f"{poids_total:,.0f}".replace(",", " ")
    cell2.metric(
        "Poids estimé de déchets categorisés",
        f"{poids_total_categorise} kg",
    )

    # 3ème métrique : nombre de relevés
    cell3 = l1_col3.container(border=True)
    # nb_collectes = f"{nb_collectes:,.0f}".replace(",", " ")
    cell3.metric("Nombre de collectes réalisées", f"{nb_collectes}")

    # Ligne 2 : graphique top déchets

    # Préparation des datas pour l'onglet 2
    df_top = df_nb_dechet.copy()

    df_top_data_releves = df_other_filtre.copy()
    # Filtration des données pour nb_dechets
    df_top10 = pd.merge(df_top, df_top_data_releves, on="ID_RELEVE", how="inner")
    # Filtration sur les type-regroupement selection dechets "GROUPE" uniquement
    df_dechets_groupe = df_top10[df_top10["type_regroupement"].isin(["GROUPE"])]
    # Group by 'categorie', sum 'nb_dechet', et top 10
    df_top10_dechets = (
        df_dechets_groupe.groupby("categorie")
        .agg({"nb_dechet": "sum"})
        .sort_values(by="nb_dechet", ascending=False)
        .head(10)
    )
    # recuperation de ces 10 dechets dans une liste pour filtration bubble map
    noms_top10_dechets = df_top10_dechets.index.tolist()
    # Preparation de la figure barplot
    df_top10_dechets.reset_index(inplace=True)
    # Création du graphique en barres avec Plotly Express
    fig = px.bar(
        df_top10_dechets,
        x="categorie",
        y="nb_dechet",
        labels={"categorie": "Dechet", "nb_dechet": "Nombre total"},
        title="Top 10 dechets ramassés",
    )
    fig.update_layout(yaxis_type="log")
    # Amélioration du visuel du graphique
    fig.update_traces(
        # texttemplate="%{text:.2f}",
        textposition="outside"
    )
    fig.update_layout(
        width=1400,
        height=900,
        uniformtext_minsize=8,
        uniformtext_mode="hide",
        xaxis_tickangle=90,
    )

    #        st.markdown(
    #            """## Quels sont les types de déchets les plus présents sur votre territoire ?
    #        """
    #        )
    #    res_aggCategory_filGroup = duckdb.query(
    #        (
    #            "SELECT categorie, sum(nb_dechet) AS total_dechet "
    #            "FROM df_nb_dechet "
    #            "WHERE type_regroupement = 'GROUPE' "
    #            "GROUP BY categorie "
    #            "HAVING sum(nb_dechet) > 10000 "
    #            "ORDER BY total_dechet DESC;"
    #        )
    #    ).to_df()

    # st.bar_chart(data=res_aggCategory_filGroup, x="categorie", y="total_dechet")

    #    st.altair_chart(
    #        alt.Chart(res_aggCategory_filGroup)
    #        .mark_bar()
    #        .encode(
    #            x=alt.X("categorie", sort=None, title=""),
    #            y=alt.Y("total_dechet", title="Total de déchet"),
    #        ),
    #        use_container_width=True,
    #    )

    with st.container():
        col1, col2 = st.columns([3, 1])

        with col1:
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.write("Métriques des déchets")  # Titre pour les cartes
            for index, row in df_top10_dechets.iterrows():
                value = f"{row['nb_dechet']:,.0f}".replace(",", " ")
                st.metric(label=row["categorie"], value=value)

    with st.container():
        # Ajout de la selectbox
        selected_dechet = st.selectbox(
            "Choisir un type de déchet :", noms_top10_dechets, index=0
        )

        # Filtration sur le dechet top 10 sélectionné
        df_top_map = df_top[df_top["categorie"] == selected_dechet]

        # Création du DataFrame de travail pour la carte
        df_map_data = pd.merge(
            df_top_map, df_top_data_releves, on="ID_RELEVE", how="inner"
        )

        # Création de la carte centrée autour d'une localisation
        # Calcul des limites à partir de vos données
        min_lat = df_map_data["LIEU_COORD_GPS_Y"].min()
        max_lat = df_map_data["LIEU_COORD_GPS_Y"].max()
        min_lon = df_map_data["LIEU_COORD_GPS_X"].min()
        max_lon = df_map_data["LIEU_COORD_GPS_X"].max()

        map_paca = folium.Map(
            location=[(min_lat + max_lat) / 2, (min_lon + max_lon) / 2],
            zoom_start=8,
            tiles="OpenStreetMap",
        )

        # Facteur de normalisation pour ajuster la taille des bulles
        normalisation_facteur = 1000

        for index, row in df_map_data.iterrows():
            # Application de la normalisation
            radius = row["nb_dechet"] / normalisation_facteur

            # Application d'une limite minimale pour le rayon si nécessaire
            radius = max(radius, 1)

            folium.CircleMarker(
                location=(row["LIEU_COORD_GPS_Y"], row["LIEU_COORD_GPS_X"]),
                radius=radius,  # Utilisation du rayon ajusté
                popup=f"{row['NOM_ZONE']}, {row['LIEU_VILLE']}, {row['DATE']} : {row['nb_dechet']} {selected_dechet}",
                color="#3186cc",
                fill=True,
                fill_color="#3186cc",
            ).add_to(map_paca)

        # Affichage de la carte Folium dans Streamlit
        st_folium = st.components.v1.html
        st_folium(
            folium.Figure().add_child(map_paca).render(),  # , width=1400
            height=1000,
        )


# Onglet 3 : Secteurs et marques
with tab3:
    st.write("")

    # Préparation des données
    df_dechet_copy = df_nb_dechet.copy()

    df_filtre_copy = df_other_filtre.copy()
    # Filtration des données pour nb_dechets
    df_init = pd.merge(df_dechet_copy, df_filtre_copy, on="ID_RELEVE", how="inner")

    # Data pour le plot secteur
    secteur_df = df_init[df_init["type_regroupement"].isin(["SECTEUR"])]
    top_secteur_df = (
        secteur_df.groupby("categorie")["nb_dechet"].sum().sort_values(ascending=True)
    )
    top_secteur_df = top_secteur_df.reset_index()
    top_secteur_df.columns = ["Secteur", "Nombre de déchets"]

    # Data pour le plot marque
    marque_df = df_init[df_init["type_regroupement"].isin(["MARQUE"])]
    top_marque_df = (
        marque_df.groupby("categorie")["nb_dechet"].sum().sort_values(ascending=True)
    )
    top_marque_df = top_marque_df.reset_index()
    top_marque_df.columns = ["Marque", "Nombre de déchets"]

    # Chiffres clés
    nb_dechet_secteur = secteur_df["nb_dechet"].sum()
    nb_secteurs = len(top_secteur_df["Secteur"].unique())

    nb_dechet_marque = marque_df["nb_dechet"].sum()
    nb_marques = len(top_marque_df["Marque"].unique())

    # Ligne 1 : 3 cellules avec les indicateurs clés en haut de page

    l1_col1, l1_col2 = st.columns(2)
    # Pour avoir 3 cellules avec bordure, il faut nester un st.container dans chaque colonne (pas d'option bordure dans st.column)
    # 1ère métrique : volume total de déchets collectés
    cell1 = l1_col1.container(border=True)
    # Trick pour séparer les milliers

    nb_dechet_secteur = f"{nb_dechet_secteur:,.0f}".replace(",", " ")
    cell1.metric(
        "Nombre de déchets catégorisés par secteur", f"{nb_dechet_secteur} dechets"
    )

    # 2ème métrique : poids
    cell2 = l1_col2.container(border=True)
    nb_secteurs = f"{nb_secteurs:,.0f}".replace(",", " ")
    # poids_total = f"{poids_total:,.0f}".replace(",", " ")
    cell2.metric(
        "Nombre de secteurs identifiés lors des collectes",
        f"{nb_secteurs} secteurs",
    )

    fig_secteur = px.bar(
        top_secteur_df.tail(10),
        x="Nombre de déchets",
        y="Secteur",
        title="Top 10 des secteurs les plus ramassés",
        orientation="h",
    )
    # add log scale to x axis
    fig_secteur.update_layout(xaxis_type="log")
    fig_secteur.update_traces(
        # texttemplate="%{text:.2f}",
        textposition="outside"
    )
    fig_secteur.update_layout(
        width=800, height=500, uniformtext_minsize=8, uniformtext_mode="hide"
    )

    st.plotly_chart(fig_secteur, use_container_width=False)

    l1_col1, l1_col2 = st.columns(2)
    cell1 = l1_col1.container(border=True)
    # Trick pour séparer les milliers

    nb_dechet_marque = f"{nb_dechet_marque:,.0f}".replace(",", " ")
    cell1.metric(
        "Nombre de déchets catégorisés par marque", f"{nb_dechet_marque} dechets"
    )

    # 2ème métrique : poids
    cell2 = l1_col2.container(border=True)
    nb_marques = f"{nb_marques:,.0f}".replace(",", " ")
    # poids_total = f"{poids_total:,.0f}".replace(",", " ")
    cell2.metric(
        "Nombre de marques identifiés lors des collectes",
        f"{nb_marques} marques",
    )
    fig_marque = px.bar(
        top_marque_df.tail(10),
        x="Nombre de déchets",
        y="Marque",
        title="Top 10 des marques les plus ramassées",
        orientation="h",
    )
    # add log scale to x axis
    fig_marque.update_layout(xaxis_type="log")
    fig_marque.update_traces(
        # texttemplate="%{text:.2f}",
        textposition="outside"
    )

    fig_marque.update_layout(
        width=800, height=500, uniformtext_minsize=8, uniformtext_mode="hide"
    )
    st.plotly_chart(fig_marque, use_container_width=False)


#    st.markdown(
#        """## Quels sont les secteurs, filières et marques les plus représentés ?
#    """
#    )
