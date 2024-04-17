import pandas as pd
from datetime import datetime, timedelta

import plotly.express as px

import streamlit as st
import folium

# from folium import IFrame

# Page setting : wide layout
st.set_page_config(
    layout="wide", page_title="Dashboard Zéro Déchet Sauvage : onglet Actions"
)

# Session state
session_state = st.session_state

# Récupérer les filtres géographiques s'ils ont été fixés
filtre_niveau = st.session_state.get("niveau_admin", "")
filtre_collectivite = st.session_state.get("collectivite", "")

# Titre de l'onglet
st.markdown(
    """# 🔎 Actions
Quels sont les actions mises en place par les acteurs ?
"""
)

# 2 Onglets : Evènements, Evènements à venir
tab1, tab2 = st.tabs(
    [
        "Evènements",
        "Evènements à venir",
    ]
)

# Onglet 1 : Evènements
with tab1:
    if filtre_niveau == "" and filtre_collectivite == "":
        st.write(
            "Aucune sélection de territoire n'ayant été effectuée les données sont globales"
        )
    else:
        st.write(f"Votre territoire : {filtre_niveau} {filtre_collectivite}")

    # Définition d'une fonction pour charger les données du nombre de déchets
    @st.cache_data
    def load_df_dict_corr_dechet_materiau():
        return pd.read_csv(
            "https://github.com/dataforgoodfr/12_zero_dechet_sauvage/raw/1-"
            "exploration-des-donn%C3%A9es/Exploration_visualisation/data/dict_de"
            "chet_groupe_materiau.csv"
        )

    @st.cache_data
    def load_df_nb_dechet():
        return pd.read_csv(
            "https://github.com/dataforgoodfr/12_zero_dechet_sauvage/raw/2-"
            "nettoyage-et-augmentation-des-donn%C3%A9es/Exploration_visuali"
            "sation/data/data_releve_nb_dechet.csv"
        )

    # Définition d'une fonction pour charger les autres données
    @st.cache_data
    def load_df_other():
        df = pd.read_csv(
            "https://github.com/dataforgoodfr/12_zero_dechet_sauvage/raw/2-"
            "nettoyage-et-augmentation-des-donn%C3%A9es/Exploration_visuali"
            "sation/data/data_zds_enriched.csv"
        )

        # Ajout des colonnes DEP_CODE_NOM et COMMUNE_CODE_NOM qui concatenent le numéro INSEE et le nom de l'entité géographique (ex : 13 - Bouches du Rhône)
        df["DEP_CODE_NOM"] = df["DEP"] + " - " + df["DEPARTEMENT"]
        df["COMMUNE_CODE_NOM"] = df["INSEE_COM"] + " - " + df["commune"]

        return df

    # Appel des fonctions pour charger les données
    df_nb_dechet = load_df_nb_dechet()
    # df_dict_corr_dechet_materiau = load_df_dict_corr_dechet_materiau()

    # Appeler le dataframe filtré depuis le session state
    if "df_other_filtre" in st.session_state:
        df_other = st.session_state["df_other_filtre"].copy()
    else:
        df_other = load_df_other()

    if "df_other_metrics_raw" in st.session_state:
        df_other_metrics_raw = st.session_state["df_other_metrics_raw"].copy()
    else:
        df_other_metrics_raw = load_df_other()

    ####################
    # @Valerie : J'ai comment pour éviter les errreur
    # Les DF sont chargés au dessus comme dans l'onglet DATA
    # Je n'ai pas trouvé de référence à 'df_nb_dechets_filtre' dans l'onglet DATA
    ####################

    # Appeler les dataframes volumes et nb_dechets filtré depuis le session state
    # if ("df_other_filtre" not in st.session_state) or (
    #    "df_nb_dechets_filtre" not in st.session_state
    # ):
    #    st.write(
    #        """
    #            ### :warning: Merci de sélectionner une collectivité\
    #            dans l'onglet Home pour afficher les données. :warning:
    #            """
    #    )

    # df_nb_dechet = pd.read_csv(
    #    (
    #        "https://github.com/dataforgoodfr/12_zero_dechet_sauvage/raw/2-"
    #        "nettoyage-et-augmentation-des-donn%C3%A9es/Exploration_visuali"
    #        "sation/data/data_releve_nb_dechet.csv"
    #    )
    # )

    # df_other = pd.read_csv(
    #    (
    #        "https://github.com/dataforgoodfr/12_zero_dechet_sauvage/raw/2-"
    #        "nettoyage-et-augmentation-des-donn%C3%A9es/Exploration_visuali"
    #        "sation/data/data_zds_enriched.csv"
    #    )
    # )

    # else:
    #    df_other = st.session_state["df_other_filtre"].copy()
    #    df_nb_dechet = st.session_state["df_nb_dechets_filtre"].copy()

    # Copier le df pour la partie filtrée par milieu/lieu/année
    df_other_metrics_raw = df_other.copy()

    annee_liste = sorted(df_other["ANNEE"].unique().tolist(), reverse=True)

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

    # Ligne 1 : 3 cellules avec les indicateurs clés en haut de page
    l1_col1, l1_col2, l1_col3 = st.columns(3)

    # 1ère métrique : nombre de relevés
    cell1 = l1_col1.container(border=True)
    nb_collectes = f"{nb_collectes:,.0f}".replace(",", " ")
    cell1.metric("Nombre de collectes réalisées", f"{nb_collectes}")

    # 2ème métrique : Nombre de Participants
    # cell2 = l1_col2.container(border=True)
    # poids_total = f"{poids_total:,.0f}".replace(",", " ")

    # cell2.metric("Poids total collecté", f"{poids_total} kg")

    # 3ème métrique : Nombre de Structures
    # cell3 = l1_col3.container(border=True)
    # nb_collectes = f"{nb_collectes:,.0f}".replace(",", " ")
    # cell3.metric("Nombre de collectes réalisées", f"{nb_collectes}")

    # Ligne 2 : 2 cellules avec les indicateurs clés en haut de page
    l2_col1, l2_col2 = st.columns(2)

    # 1ère métrique : volume total de déchets collectés
    cell4 = l2_col1.container(border=True)
    # Trick pour séparer les milliers
    volume_total = f"{volume_total:,.0f}".replace(",", " ")
    cell4.metric("Volume de déchets collectés", f"{volume_total} litres")

    # 2ème métrique : poids
    cell5 = l2_col2.container(border=True)
    poids_total = f"{poids_total:,.0f}".replace(",", " ")

    cell5.metric("Poids total collecté", f"{poids_total} kg")

    # Ligne 3 : 2 graphiques en ligne : carte relevés et bar chart matériaux
    l3_col1, l3_col2 = st.columns(2)
    cell6 = l3_col1.container(border=True)
    cell7 = l3_col2.container(border=True)

    # with cell6:
    # Création de la carte

    with cell7:
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

    # Ligne 4 : 2 graphiques en ligne : bar chart milieux et bar chart types déchets
    l4_col1, l4_col2 = st.columns(2)
    cell8 = l4_col1.container(border=True)
    cell9 = l4_col2.container(border=True)

    # with cell8:
    #    # Création du graphique en barres avec Plotly Express
    #    fig3 = px.bar(
    #        df_volume,
    #        x="TYPE_MILIEU",
    #        y="nb_collectes",
    #        text="Nombre de Collectes",
    #        title="Nombre de Collectes par Types de Milieux",
    #        color="#48BEF0",
    #        color_discrete_map=colors_map,
    #        orientation='h',
    #    )

    # Amélioration du graphique
    #    fig3.update_traces(texttemplate="%{text:.2s}", textposition="inside")
    #    fig3.update_layout(
    #        autosize=True,
    #        uniformtext_minsize=8,
    #        uniformtext_mode="hide",
    #        xaxis_tickangle=90,
    #        showlegend=False,
    #    )

    # Affichage du graphique
    #    st.plotly_chart(fig3, use_container_width=True)

    # with cell9:
    #    # Création du graphique en barres avec Plotly Express
    #    fig4 = px.bar(
    #        df_volume,
    #        x="TYPE_DECHET",
    #        y="nb_collectes",
    #        text="Nombre de Collectes",
    #        title="Nombre de Collectes par Types de Déchets",
    #        color="#48BEF0",
    #        color_discrete_map=colors_map,
    #    )

    #    # Amélioration du graphique
    #    fig4.update_traces(texttemplate="%{text:.2s}", textposition="inside")
    #    fig4.update_layout(
    #        autosize=True,
    #        uniformtext_minsize=8,
    #        uniformtext_mode="hide",
    #        xaxis_tickangle=90,
    #        showlegend=False,
    #    )

    #    # Affichage du graphique
    #    st.plotly_chart(fig4, use_container_width=True)

    # Ligne 5 : 2 graphiques en ligne : line chart volume + nb collectes et Pie niveau de caractérisation
    l5_col1, l5_col2 = st.columns(2)
    cell10 = l5_col1.container(border=True)
    cell11 = l5_col2.container(border=True)

    # with cell10:
    # Création du graphique en barres volume + ligne nb de relevées avec Plotly Express

    # with cell11:
    # Création du graphique en donut avec Plotly Express


# onglet Evenements a venir
with tab2:
    st.write(f"Votre territoire : Pays - France")

    # Définition d'une fonction pour charger les evenements à venir
    @st.cache_data
    def load_df_events_clean() -> pd.DataFrame:
        return pd.read_csv(
            "https://github.com/dataforgoodfr/12_zero_dechet_sauvage/raw/2-"
            "nettoyage-et-augmentation-des-donn%C3%A9es/Exploration_visuali"
            "sation/data/export_events_cleaned.csv"
        )

    # Appel des fonctions pour charger les données
    df_events = load_df_events_clean()

    df_events.DATE = pd.to_datetime(df_events.DATE)

    # Filtrer les événements à venir
    df_events_a_venir = df_events[df_events.DATE > (datetime.now() - timedelta(days=5))]

    # Trie les events par date
    df_events_a_venir.sort_values(by="DATE", inplace=True)

    # Coord approximatives du centre de la France
    coord_centre_france = [46.603354, 1.888334]

    # Code couleurs de ZDS
    color_ZDS_bleu = "#003463"
    color_ZDS_rouge = "#e9003f"

    # Créer la carte
    map_events = folium.Map(
        location=coord_centre_france,
        zoom_start=6,
    )

    # Ajouter des marqueurs pour chaque événement à venir sur la carte
    for idx, row in df_events_a_venir.iterrows():
        folium.Marker(
            location=[row.COORD_GPS_Y, row.COORD_GPS_X],
            popup=folium.Popup(row.NOM_EVENEMENT, lazy=False),
            # tooltip=row.NOM_EVENEMENT,
            # icon=folium.Icon(icon_color=color_ZDS_bleu)
        ).add_to(map_events)

    # Afficher la liste des événements à venir avec la date affichée avant le nom
    st.subheader("Actions à venir :")

    with st.container(height=500, border=False):
        for idx, row in df_events_a_venir.iterrows():
            with st.container(border=True):
                # Bloc contenant la date
                date_block = f"<div style='font-weight:bold; color:{color_ZDS_rouge}; text-align: center;'>{row.DATE.day}<br>{row.DATE.strftime('%b')}</div>"
                # Bloc contenant le nom de l'événement
                event_block = (
                    f"<div style='font-weight:bold;'>{row.NOM_EVENEMENT}</div>"
                )
                # Bloc contenant le type d'événement et le nom de la structure
                type_structure_block = f"{row.TYPE_EVENEMENT} | {row.NOM_STRUCTURE}"

                # Ajout de chaque événement dans la liste
                st.write(
                    f"<div style='display:flex;'>{date_block}<div style='margin-left:10px;'>{event_block}<span>{type_structure_block}</span></div></div>",
                    unsafe_allow_html=True,
                )

    # Afficher la carte avec Streamlit
    st_folium = st.components.v1.html
    st_folium(
        folium.Figure().add_child(map_events).render(),
        width=800,
        height=800,
    )
