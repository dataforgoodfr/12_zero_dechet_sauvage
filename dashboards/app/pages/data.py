import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from folium import IFrame

# Configuration de la page
st.set_page_config(
    layout="wide", page_title="Dashboard Zéro Déchet Sauvage : onglet Data"
)

# Session state
session_state = st.session_state

# Récupérer les filtres géographiques s'ils ont été fixés
filtre_niveau = st.session_state.get("niveau_admin", "")
filtre_collectivite = st.session_state.get("collectivite", "")

# Titre de l'onglet
st.markdown(
    """# 🔎 Data
Visualisez les impacts sur les milieux naturels et secteurs/filières/marques à l’origine de cette pollution
"""
)

if filtre_niveau == "" and filtre_collectivite == "":
    st.write(
        "Aucune sélection de territoire n'ayant été effectuée les données sont globales"
    )
else:
    st.write(f"Votre territoire : {filtre_niveau} {filtre_collectivite}")


# Définition d'une fonction pour charger les données du nombre de déchets@st.cache_data
def load_df_dict_corr_dechet_materiau():
    return pd.read_csv(
        "https://github.com/dataforgoodfr/12_zero_dechet_sauvage/raw/1-"
        "exploration-des-donn%C3%A9es/Exploration_visualisation/data/dict_de"
        "chet_groupe_materiau.csv"
    )


# Appel des fonctions pour charger les données
df_dict_corr_dechet_materiau = load_df_dict_corr_dechet_materiau()

# Appeler les dataframes volumes et nb_dechets filtré depuis le session state
if ("df_other_filtre" not in st.session_state) or (
    "df_nb_dechets_filtre" not in st.session_state
):
    st.write(
        """
            ### :warning: Merci de sélectionner une collectivité\
            dans l'onglet Home pour afficher les données. :warning:
            """
    )
else:
    df_other = st.session_state["df_other_filtre"].copy()
    df_nb_dechet = st.session_state["df_nb_dechets_filtre"].copy()

# Copier le df pour la partie filtrée par milieu/lieu/année
df_other_metrics_raw = df_other.copy()


# 3 Onglets : Matériaux, Top déchets, Filières et marques
tab1, tab2, tab3 = st.tabs(
    [
        "Matériaux :wood:",
        "Top Déchets :wastebasket:",
        "Secteurs et marques :womans_clothes:",
    ]
)

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
    df_volume = df_other.copy()

    # Calcul des indicateurs clés de haut de tableau avant transformation
    volume_total = df_volume["VOLUME_TOTAL"].sum()
    poids_total = df_volume["POIDS_TOTAL"].sum()
    volume_total_categorise = df_volume[cols_volume].sum().sum()
    pct_volume_categorise = volume_total_categorise / volume_total
    nb_collectes_int = len(df_volume)

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
        "Textile": "#C384B1",
        "Papier": "#CAA674",
        "Metal": "#A0A0A0",
        "Verre": "#3DCE89",
        "Autre": "#F3B900",
        "Plastique": "#48BEF0",
        "Caoutchouc": "#364E74",
        "Bois": "#673C11",
        "Papier/Carton": "#CAA674",
        "Métal": "#A0A0A0",
        "Verre/Céramique": "#3DCE89",
        "Autre": "#F3B900",
    }

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
    nb_collectes = f"{nb_collectes_int:,.0f}".replace(",", " ")
    cell3.metric("Nombre de collectes réalisées", f"{nb_collectes}")

    # Message d'avertissement nb de collectes en dessous de 5
    if nb_collectes_int == 1:
        st.warning(
            "⚠️ Il n'y a qu' "
            + str(nb_collectes_int)
            + " collecte considérées dans les données présentées."
        )
    elif nb_collectes_int <= 5:
        st.warning(
            "⚠️ Il n'y a que "
            + str(nb_collectes_int)
            + " collectes considérées dans les données présentées."
        )

    # Ligne 2 : 2 graphiques en ligne : donut et bar chart matériaux

    l2_col1, l2_col2 = st.columns(2)
    cell4 = l2_col1.container(border=True)
    cell5 = l2_col2.container(border=True)
    with cell4:

        # Création du diagramme en donut en utilisant le dictionnaire de couleurs pour la correspondance
        fig = px.pie(
            df_totals_sorted,
            values="Volume",
            names="Matériau",
            title="Répartition des matériaux en volume",
            hole=0.4,
            color="Matériau",
            color_discrete_map=colors_map,
        )

        # Amélioration de l'affichage
        fig.update_traces(textinfo="percent")
        fig.update_layout(autosize=True, legend_title_text="Matériau")

        # Affichage du graphique
        st.plotly_chart(fig, use_container_width=True)

    with cell5:
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
        fig2.update_traces(texttemplate="%{text:.2s}", textposition="inside")
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

    # Ligne 3 : Graphe par milieu de collecte

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
        title="Part de chaque matériau en volume selon le milieu de collecte",
        color_discrete_map=colors_map,
    )
    fig3.update_layout(bargap=0.2, height=500)
    fig3.update_layout(yaxis_title="% du volume collecté", xaxis_title=None)
    fig3.update_xaxes(tickangle=-45)

    # Afficher le graphique
    with st.container(border=True):
        st.plotly_chart(fig3, use_container_width=True)

    st.divider()

    # Ligne 3 : Graphe par milieu , lieu et année
    st.write("**Détail par milieu, lieu ou année**")

    # Étape 1: Création des filtres

    df_other_metrics = df_other_metrics_raw.copy()
    df_other_metrics = df_other_metrics.fillna(0)

    selected_annee = st.selectbox(
        "Choisir une année:",
        options=["Aucune sélection"] + list(df_other["ANNEE"].unique()),
    )
    if selected_annee != "Aucune sélection":
        filtered_data_milieu = df_other[df_other["ANNEE"] == selected_annee].copy()
        filtered_metrics_milieu = df_other_metrics[
            df_other_metrics["ANNEE"] == selected_annee
        ].copy()
    else:
        filtered_data_milieu = df_other.copy()
        filtered_metrics_milieu = df_other_metrics.copy()

    selected_type_milieu = st.selectbox(
        "Choisir un type de milieu:",
        options=["Aucune sélection"]
        + list(filtered_data_milieu["TYPE_MILIEU"].unique()),
    )

    if selected_type_milieu != "Aucune sélection":
        filtered_data_lieu = filtered_data_milieu[
            filtered_data_milieu["TYPE_MILIEU"] == selected_type_milieu
        ]
        filtered_metrics_milieu = filtered_metrics_milieu[
            filtered_metrics_milieu["TYPE_MILIEU"] == selected_type_milieu
        ]
    else:
        filtered_data_lieu = filtered_data_milieu.copy()
        filtered_metrics_milieu = df_other_metrics.copy()

    selected_type_lieu = st.selectbox(
        "Choisir un type de lieu:",
        options=["Aucune sélection"] + list(filtered_data_lieu["TYPE_LIEU"].unique()),
    )

    if (
        selected_annee == "Aucune sélection"
        and selected_type_milieu == "Aucune sélection"
        and selected_type_lieu == "Aucune sélection"
    ):
        df_filtered = df_other.copy()
        df_filtered_metrics = df_other_metrics_raw.copy()
    elif (
        selected_type_milieu == "Aucune sélection"
        and selected_type_lieu == "Aucune sélection"
    ):
        df_filtered = df_other[df_other["ANNEE"] == selected_annee].copy()
        df_filtered_metrics = df_other_metrics_raw[
            df_other_metrics["ANNEE"] == selected_annee
        ].copy()
    elif (
        selected_annee == "Aucune sélection"
        and selected_type_lieu == "Aucune sélection"
        and selected_type_milieu != "Aucune sélection"
    ):
        df_filtered = df_other[df_other["TYPE_MILIEU"] == selected_type_milieu].copy()
        df_filtered_metrics = df_other_metrics_raw[
            df_other_metrics["TYPE_MILIEU"] == selected_type_milieu
        ].copy()

    elif (
        selected_annee == "Aucune sélection"
        and selected_type_lieu != "Aucune sélection"
        and selected_type_milieu == "Aucune sélection"
    ):
        df_filtered = df_other[df_other["TYPE_LIEU"] == selected_type_lieu].copy()
        df_filtered_metrics = df_other_metrics_raw[
            df_other_metrics["TYPE_LIEU"] == selected_type_lieu
        ].copy()

    elif (
        selected_annee == "Aucune sélection"
        and selected_type_lieu != "Aucune sélection"
        and selected_type_milieu != "Aucune sélection"
    ):
        df_filtered = df_other[
            (df_other["TYPE_LIEU"] == selected_type_lieu)
            & (df_other["TYPE_MILIEU"] == selected_type_milieu)
        ].copy()
        df_filtered_metrics = df_other_metrics_raw[
            (df_other_metrics["TYPE_LIEU"] == selected_type_lieu)
            & (df_other_metrics["TYPE_MILIEU"] == selected_type_milieu)
        ]
    elif (
        selected_annee != "Aucune sélection"
        and selected_type_lieu != "Aucune sélection"
        and selected_type_milieu == "Aucune sélection"
    ):
        df_filtered = df_other[
            (df_other["ANNEE"] == selected_annee)
            & (df_other["TYPE_LIEU"] == selected_type_lieu)
        ].copy()
        df_filtered_metrics = df_other_metrics_raw[
            (df_other_metrics["ANNEE"] == selected_annee)
            & (df_other_metrics["TYPE_LIEU"] == selected_type_lieu)
        ]
    elif (
        selected_annee != "Aucune sélection"
        and selected_type_lieu == "Aucune sélection"
        and selected_type_milieu != "Aucune sélection"
    ):
        df_filtered = df_other[
            (df_other["ANNEE"] == selected_annee)
            & (df_other["TYPE_MILIEU"] == selected_type_milieu)
        ].copy()
        df_filtered_metrics = df_other_metrics_raw[
            (df_other_metrics["ANNEE"] == selected_annee)
            & (df_other_metrics["TYPE_MILIEU"] == selected_type_milieu)
        ]

    else:
        df_filtered = df_other[
            (df_other["ANNEE"] == selected_annee)
            & (df_other["TYPE_MILIEU"] == selected_type_milieu)
            & (df_other["TYPE_LIEU"] == selected_type_lieu)
        ].copy()
        df_filtered_metrics = df_other_metrics_raw[
            (df_other_metrics["ANNEE"] == selected_annee)
            & (df_other_metrics["TYPE_MILIEU"] == selected_type_milieu)
            & (df_other_metrics["TYPE_LIEU"] == selected_type_lieu)
        ]

    # Ligne 5 : Metriques filtrés
    l5_col1, l5_col2, l5_col3 = st.columns(3)
    cell6 = l5_col1.container(border=True)
    cell7 = l5_col2.container(border=True)
    cell8 = l5_col3.container(border=True)

    poids_total_filtered = df_filtered_metrics["POIDS_TOTAL"].sum()
    volume_total_filtered = df_filtered_metrics["VOLUME_TOTAL"].sum()

    volume_total_filtered = f"{volume_total_filtered:,.0f}".replace(",", " ")
    cell6.metric("Volume de dechets collectés", f"{volume_total_filtered} litres")

    poids_total_filtered = f"{poids_total_filtered:,.0f}".replace(",", " ")
    cell7.metric("Poids total collecté", f"{poids_total_filtered} kg")

    nombre_collectes_filtered = f"{len(df_filtered):,.0f}".replace(",", " ")
    cell8.metric("Nombre de collectes", f"{nombre_collectes_filtered}")

    # Message d'avertissement nb de collectes en dessous de 5
    if len(df_filtered) == 1:
        st.warning(
            "⚠️ Il n'y a qu' "
            + str(len(df_filtered))
            + " collecte considérées dans les données présentées."
        )
    elif len(df_filtered) <= 5:
        st.warning(
            "⚠️ Il n'y a que "
            + str(len(df_filtered))
            + " collectes considérées dans les données présentées."
        )

    # Étape 3: Preparation dataframe pour graphe
    # Copie des données pour transfo
    df_volume2 = df_filtered.copy()

    # Calcul des indicateurs clés de haut de tableau avant transformation
    volume2_total = df_volume2["VOLUME_TOTAL"].sum()
    poids2_total = df_volume2["POIDS_TOTAL"].sum()
    volume2_total_categorise = df_volume2[cols_volume].sum().sum()
    pct_volume2_categorise = volume2_total_categorise / volume2_total
    nb_collectes2 = len(df_volume2)

    # estimation du poids categorisée en utilisant pct_volume_categorise
    poids2_total_categorise = round(poids2_total * pct_volume2_categorise)

    # Dépivotage du tableau pour avoir une base de données exploitable
    df_volume2 = df_volume2.melt(
        id_vars=cols_identifiers,
        value_vars=cols_volume,
        var_name="Matériau",
        value_name="Volume",
    )

    # Nettoyer le nom du Type déchet pour le rendre plus lisible
    df_volume2["Matériau"] = (
        df_volume2["Matériau"].str.replace("GLOBAL_VOLUME_", "").str.title()
    )

    # Grouper par type de matériau pour les visualisations
    df_totals_sorted2 = df_volume2.groupby(["Matériau"], as_index=False)["Volume"].sum()
    df_totals_sorted2 = df_totals_sorted2.sort_values(["Volume"], ascending=False)

    # Étape 4: Création du Graphique

    if not df_filtered.empty:
        fig4 = px.treemap(
            df_totals_sorted2,
            path=["Matériau"],
            values="Volume",
            title="Répartition des matériaux en volume",
            color="Matériau",
            color_discrete_map=colors_map,
        )
        fig4.update_layout(
            margin=dict(t=50, l=25, r=25, b=25), autosize=True, height=600
        )
        fig4.update_traces(
            textinfo="label+value",
            textfont=dict(size=16, family="Arial", color="black"),
        )
        with st.container(border=True):
            st.plotly_chart(fig4, use_container_width=True)

    else:
        st.write("Aucune donnée à afficher pour les filtres sélectionnés.")


# Onglet 2 : Top Déchets
with tab2:

    # Préparation des datas pour l'onglet 2
    df_top = df_nb_dechet.copy()
    df_top_data_releves = df_other.copy()

    # Calcul du nombre total de déchets catégorisés sur le territoier
    nb_total_dechets = df_top[(df_top["type_regroupement"] == "GROUPE")][
        "nb_dechet"
    ].sum()
    nb_total_dechets = f"{nb_total_dechets:,.0f}".replace(",", " ")

    # Ligne 1 : 3 cellules avec les indicateurs clés en haut de page
    l1_col1, l1_col2, l1_col3 = st.columns(3)
    # Pour avoir 3 cellules avec bordure, il faut nester un st.container dans chaque colonne (pas d'option bordure dans st.column)
    # 1ère métrique : volume total de déchets collectés
    cell1 = l1_col1.container(border=True)
    # Trick pour séparer les milliers

    # volume_total_categorise = f"{volume_total_categorise:,.0f}".replace(",", " ")
    cell1.metric("Nombre de déchets catégorisés", f"{nb_total_dechets} déchets")

    # 2ème métrique : équivalent volume catégorisé
    cell2 = l1_col2.container(border=True)
    volume_total_categorise = f"{volume_total_categorise:,.0f}".replace(",", " ")
    cell2.metric(
        "Equivalent en volume ",
        f"{volume_total_categorise} litres",
    )

    # 3ème métrique : nombre de relevés
    cell3 = l1_col3.container(border=True)
    # nb_collectes = f"{nb_collectes:,.0f}".replace(",", " ")
    cell3.metric("Nombre de collectes comptabilisées", f"{nb_collectes}")

    # Ligne 2 : graphique top déchets

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
    # Preparation des datas pour l'onglet 3# ajout de la colonne materiau
    df_top10_dechets = df_top10_dechets.merge(
        df_dict_corr_dechet_materiau, on="categorie", how="left"
    )
    # Preparation de la figure barplot
    df_top10_dechets.reset_index(inplace=True)
    # Création du graphique en barres avec Plotly Express

    fig5 = px.bar(
        df_top10_dechets,
        y="categorie",
        x="nb_dechet",
        labels={"categorie": "Dechet", "nb_dechet": "Nombre total"},
        title="Top 10 dechets ramassés ",
        text="nb_dechet",
        color="Materiau",
        color_discrete_map=colors_map,
        category_orders={"categorie": df_top10_dechets["categorie"].tolist()},
    )
    fig5.update_layout(xaxis_type="log")
    # Amélioration du visuel du graphique
    fig5.update_traces(
        # texttemplate="%{text:.2f}",
        textposition="inside",
        textfont_color="white",
        textfont_size=20,
    )
    fig5.update_layout(
        width=1400,
        height=900,
        uniformtext_minsize=8,
        uniformtext_mode="hide",
        xaxis_tickangle=90,
    )

    # Suppression de la colonne categorie
    del df_top10_dechets["Materiau"]

    with st.container(border=True):
        st.plotly_chart(fig5, use_container_width=True)

        st.write("")
        st.caption(
            f"Note : Analyse basée sur les collectes qui ont fait l'objet d'un comptage détaillé par déchet,\
             soit {volume_total_categorise} litres équivalent à {pct_volume_categorise:.0%} du volume collecté\
                sur le territoire."
        )
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
            height=750,
        )


# Onglet 3 : Secteurs et marques
with tab3:
    st.write("")

    # Préparation des données
    df_dechet_copy = df_nb_dechet.copy()
    df_filtre_copy = df_other.copy()

    # Étape 1: Création des filtres
    selected_annee_onglet_3 = st.selectbox(
        "Choisir une année:",
        options=["Aucune sélection"] + list(df_other["ANNEE"].sort_values().unique()),
        key="année_select",
    )
    if selected_annee_onglet_3 != "Aucune sélection":
        filtered_data_milieu = df_other[df_other["ANNEE"] == selected_annee_onglet_3]
    else:
        filtered_data_milieu = df_other.copy()

    selected_type_milieu_onglet_3 = st.selectbox(
        "Choisir un type de milieu:",
        options=["Aucune sélection"]
        + list(filtered_data_milieu["TYPE_MILIEU"].unique()),
        key="type_milieu_select",
    )

    if selected_type_milieu_onglet_3 != "Aucune sélection":
        filtered_data_lieu = filtered_data_milieu[
            filtered_data_milieu["TYPE_MILIEU"] == selected_type_milieu_onglet_3
        ]
    else:
        filtered_data_lieu = filtered_data_milieu

    selected_type_lieu_onglet_3 = st.selectbox(
        "Choisir un type de lieu:",
        options=["Aucune sélection"] + list(filtered_data_lieu["TYPE_LIEU"].unique()),
        key="type_lieu_select",
    )

    if (
        selected_annee_onglet_3 == "Aucune sélection"
        and selected_type_milieu_onglet_3 == "Aucune sélection"
        and selected_type_lieu_onglet_3 == "Aucune sélection"
    ):
        df_filtered = df_other.copy()
    elif (
        selected_type_milieu_onglet_3 == "Aucune sélection"
        and selected_type_lieu_onglet_3 == "Aucune sélection"
    ):
        df_filtered = df_other[df_other["ANNEE"] == selected_annee_onglet_3].copy()
    elif (
        selected_annee_onglet_3 == "Aucune sélection"
        and selected_type_lieu_onglet_3 == "Aucune sélection"
        and selected_type_milieu_onglet_3 != "Aucune sélection"
    ):
        df_filtered = df_other[
            df_other["TYPE_MILIEU"] == selected_type_milieu_onglet_3
        ].copy()
    elif (
        selected_annee_onglet_3 == "Aucune sélection"
        and selected_type_lieu_onglet_3 != "Aucune sélection"
        and selected_type_milieu_onglet_3 == "Aucune sélection"
    ):
        df_filtered = df_other[
            df_other["TYPE_LIEU"] == selected_type_lieu_onglet_3
        ].copy()
    elif (
        selected_annee_onglet_3 == "Aucune sélection"
        and selected_type_lieu_onglet_3 != "Aucune sélection"
        and selected_type_milieu_onglet_3 != "Aucune sélection"
    ):
        df_filtered = df_other[
            (df_other["TYPE_LIEU"] == selected_type_lieu_onglet_3)
            & (df_other["TYPE_MILIEU"] == selected_type_milieu_onglet_3)
        ].copy()
    elif (
        selected_annee_onglet_3 != "Aucune sélection"
        and selected_type_lieu_onglet_3 != "Aucune sélection"
        and selected_type_milieu_onglet_3 == "Aucune sélection"
    ):
        df_filtered = df_other[
            (df_other["ANNEE"] == selected_annee_onglet_3)
            & (df_other["TYPE_LIEU"] == selected_type_lieu_onglet_3)
        ].copy()
    elif (
        selected_annee_onglet_3 != "Aucune sélection"
        and selected_type_lieu_onglet_3 == "Aucune sélection"
        and selected_type_milieu_onglet_3 != "Aucune sélection"
    ):
        df_filtered = df_other[
            (df_other["ANNEE"] == selected_annee_onglet_3)
            & (df_other["TYPE_MILIEU"] == selected_type_milieu_onglet_3)
        ].copy()

    elif selected_type_lieu_onglet_3 == "Aucune sélection":
        df_filtered = df_other[
            (df_other["ANNEE"] == selected_annee_onglet_3)
            & (df_other["TYPE_MILIEU"] == selected_type_milieu_onglet_3)
        ].copy()
    else:
        df_filtered = df_other[
            (df_other["ANNEE"] == selected_annee_onglet_3)
            & (df_other["TYPE_MILIEU"] == selected_type_milieu_onglet_3)
            & (df_other["TYPE_LIEU"] == selected_type_lieu_onglet_3)
        ].copy()

    # Filtration des données pour nb_dechets
    df_init = pd.merge(df_dechet_copy, df_filtered, on="ID_RELEVE", how="inner")

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
    colors_map_secteur = {
        "AGRICULTURE": "#156644",
        "ALIMENTATION": "#F7D156",
        "AMEUBLEMENT, DÉCORATION ET ÉQUIPEMENT DE LA MAISON": "#F79D65",
        "AQUACULTURE": "#0067C2",
        "BÂTIMENT, TRAVAUX ET MATÉRIAUX DE CONSTRUCTION": "#FF9900",
        "CHASSE ET ARMEMENT": "#23A76F",
        "COSMÉTIQUES, HYGIÈNE ET SOINS PERSONNELS": "#BF726B",
        "DÉTERGENTS ET PRODUITS D'ENTRETIENS": "#506266",
        "EMBALLAGE INDUSTRIEL ET COLIS": "#754B30",
        "GRAPHIQUE ET PAPETERIE ET FOURNITURES DE BUREAU": "#EFEFEF",
        "INDÉTERMINÉ": "#967EA1",
        "INFORMATIQUE ET HIGHTECH": "#E351F7",
        "JOUETS ET LOISIR": "#A64D79",
        "MATÉRIEL ÉLECTRIQUE ET ÉLECTROMÉNAGER": "#AE05C3",
        "MÉTALLURGIE": "#EC4773",
        "PÊCHE": "#003463",
        "PETROCHIMIE": "#0D0D0D",
        "PHARMACEUTIQUE/PARAMÉDICAL": "#61BF5E",
        "PLASTURGIE": "#05A2AD",
        "TABAC": "#E9003F",
        "TEXTILE ET HABILLEMENT": "#FA9EE5",
        "TRAITEMENT DES EAUX": "#4AA6F7",
        "TRANSPORT / AUTOMOBILE": "#6C2775",
        "VAISSELLE À USAGE UNIQUE": "#732D3A",
        "AUTRES SECTEURS": "#D9C190",
    }

    fig_secteur = px.bar(
        top_secteur_df.tail(10).sort_values(by="Nombre de déchets", ascending=False),
        x="Nombre de déchets",
        y="Secteur",
        color="Secteur",
        title="Top 10 des secteurs les plus ramassés",
        orientation="h",
        color_discrete_map=colors_map_secteur,
        text_auto=True,
    )
    # add log scale to x axis
    fig_secteur.update_layout(xaxis_type="log")
    fig_secteur.update_traces(texttemplate="%{value:.0f}", textposition="inside")
    fig_secteur.update_layout(
        width=800,
        height=500,
        uniformtext_mode="hide",
        showlegend=False,
        yaxis_title=None,
    )
    with st.container(border=True):
        st.plotly_chart(fig_secteur, use_container_width=True)

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
    cell2.metric(
        "Nombre de marques identifiés lors des collectes",
        f"{nb_marques} marques",
    )
    colors_map_marque = {
        "HEINEKEN": "#F7D156",
        "COCA-COLA": "#F7D156",
        "MARLBORO": "#E9003F",
        "CRISTALINE": "#F7D156",
        "PHILIP MORRIS": "#E9003F",
        "CAPRI-SUN": "#F7D156",
        "OASIS": "#F7D156",
        "1664": "#F7D156",
        "WINSTON": "#E9003F",
        "RED BULL": "#F7D156",
    }

    fig_marque = px.bar(
        top_marque_df.tail(10).sort_values(by="Nombre de déchets", ascending=False),
        x="Nombre de déchets",
        y="Marque",
        title="Top 10 des marques les plus ramassées",
        color="Marque",
        orientation="h",
        color_discrete_map=colors_map_marque,
        text_auto=False,
    )
    # add log scale to x axis
    fig_marque.update_layout(xaxis_type="log")
    fig_marque.update_traces(texttemplate="%{value:.0f}", textposition="inside")

    fig_marque.update_layout(
        width=800,
        height=500,
        uniformtext_minsize=8,
        uniformtext_mode="hide",
        yaxis_title=None,
    )

    with st.container(border=True):
        st.plotly_chart(fig_marque, use_container_width=True)
