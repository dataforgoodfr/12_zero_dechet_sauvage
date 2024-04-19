import streamlit as st
import altair as alt
import pandas as pd
import duckdb

st.markdown(
    """# 👊 Actions
*Quels sont les actions mises en place par les acteurs ?*
"""
)

# Session state
session_state = st.session_state

# Récupérer les filtres géographiques s'ils ont été fixés
filtre_niveau = st.session_state.get("niveau_admin", "")
filtre_collectivite = st.session_state.get("collectivite", "")

if st.session_state["authentication_status"]:
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

    # Appeler les dataframes volumes et nb_dechets filtré depuis le session state
    if "df_other_filtre" not in st.session_state:
        st.write(
            """
                ### :warning: Merci de sélectionner une collectivité\
                dans l'onglet Home pour afficher les données. :warning:
                """
        )
        st.stop()
    else:
        df_other = st.session_state["df_other_filtre"].copy()

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

        # Filtre par année:
        options = ["Aucune sélection"] + list(df_other["ANNEE"].unique())
        annee_choisie = st.selectbox("Choisissez l'année:", options, index=0)

        if annee_choisie == "Aucune sélection":
            df_other_filtre = df_other.copy()

        if annee_choisie != "Aucune sélection":
            df_other_filtre = df_other[df_other["ANNEE"] == annee_choisie].copy()

        # Copie des données pour transfo
        df_events = df_other_filtre.copy()

        # Calcul des indicateurs clés de haut de tableau avant transformation
        volume_total = df_events["VOLUME_TOTAL"].sum()
        poids_total = df_events["POIDS_TOTAL"].sum()
        nombre_participants = df_events["NB_PARTICIPANTS"].sum()
        nb_collectes = len(df_events)
        nombre_structures = df_events["ID_STRUCTURE"].nunique()

        # Ligne 1 : 3 cellules avec les indicateurs clés en haut de page
        l1_col1, l1_col2, l1_col3 = st.columns(3)

        # 1ère métrique : nombre de relevés
        cell1 = l1_col1.container(border=True)
        nb_collectes = f"{nb_collectes:,.0f}".replace(",", " ")
        cell1.metric("Nombre de collectes réalisées", f"{nb_collectes}")

        # 2ème métrique : Nombre de Participants
        cell2 = l1_col2.container(border=True)
        nombre_participants = f"{nombre_participants:,.0f}".replace(",", " ")
        cell2.metric("Nombre de participants", f"{nombre_participants}")

        # 3ème métrique : Nombre de Structures
        cell3 = l1_col3.container(border=True)
        nombre_structures = f"{nombre_structures:,.0f}".replace(",", " ")
        cell3.metric("Nombre de structures", f"{nombre_structures}")

        # Ligne 2 : Carte
        with st.container():
            # Création du DataFrame de travail pour la carte
            df_map_evnenements = df_other_filtre.copy()
            # Création de la carte centrée autour d'une localisation
            # Calcul des limites à partir de vos données
            min_lat = df_map_evnenements["LIEU_COORD_GPS_Y"].min()
            max_lat = df_map_evnenements["LIEU_COORD_GPS_Y"].max()
            min_lon = df_map_evnenements["LIEU_COORD_GPS_X"].min()
            max_lon = df_map_evnenements["LIEU_COORD_GPS_X"].max()

            map_evenements = folium.Map(
                location=[(min_lat + max_lat) / 2, (min_lon + max_lon) / 2],
                zoom_start=8,
                tiles="OpenStreetMap",
            )
            # Facteur de normalisation pour ajuster la taille des bulles
            normalisation_facteur = 100
            for index, row in df_map_evnenements.iterrows():
                # Application de la normalisation
                radius = row["NB_PARTICIPANTS"] / normalisation_facteur

                # Application d'une limite minimale pour le rayon si nécessaire
                radius = max(radius, 5)

                folium.CircleMarker(
                    location=(row["LIEU_COORD_GPS_Y"], row["LIEU_COORD_GPS_X"]),
                    radius=radius,  # Utilisation du rayon ajusté
                    popup=f"{row['NOM_ZONE']}, {row['LIEU_VILLE']}, {row['NOM_EVENEMENT']}, {row['DATE']}  : nombre de participants : {row['NB_PARTICIPANTS']}",
                    color="#3186cc",
                    fill=True,
                    fill_color="#3186cc",
                ).add_to(map_evenements)

            # Affichage de la carte Folium dans Streamlit
            st_folium = st.components.v1.html
            st_folium(
                folium.Figure().add_child(map_evenements).render(),  # , width=1400
                height=750,
            )

        # Ligne 3 : 1 graphique donut chart et un graphique barplot horizontal nombre de relevés par types de milieux
        # préparation du dataframe et figure niveaux de caracterisation

        df_carac = df_other_filtre.copy()
        df_carac_counts = df_carac["NIVEAU_CARAC"].value_counts().reset_index()
        df_carac_counts.columns = ["NIVEAU_CARAC", "counts"]

        fig1_actions = px.pie(
            df_carac_counts,
            values="counts",
            names="NIVEAU_CARAC",
            title="Répartition des niveaux de caractérisation",
            hole=0.5,
        )
        fig1_actions.update_traces(textposition="inside", textinfo="percent+label")

        # préparation du dataframe et figure releves types de milieux

        df_milieux = df_other_filtre.copy()
        df_milieux_counts = df_milieux["TYPE_MILIEU"].value_counts().reset_index()
        df_milieux_counts.columns = ["TYPE_MILIEU", "counts"]
        df_milieux_counts_sorted = df_milieux_counts.sort_values(
            by="counts", ascending=True
        )

        fig2_actions = px.bar(
            df_milieux_counts_sorted,
            y="TYPE_MILIEU",
            x="counts",
            title="Nombre de relevés par types de milieux",
            text="counts",
            orientation="h",
        )
        fig2_actions.update_layout(xaxis_title="", yaxis_title="")

        l3_col1, l3_col2 = st.columns(2)
        cell4 = l3_col1.container(border=True)
        cell5 = l3_col2.container(border=True)

        # Affichage donut
        with cell4:
            st.plotly_chart(fig1_actions, use_container_width=True)

        # Affichage barplot
        with cell5:
            st.plotly_chart(fig2_actions, use_container_width=True)

        # Ligne 3 : 2 graphiques en ligne : carte relevés et bar chart matériaux
        l3_col1, l3_col2 = st.columns(2)
        cell6 = l3_col1.container(border=True)
        cell7 = l3_col2.container(border=True)

        # Ligne 4 : 2 graphiques en ligne : bar chart milieux et bar chart types déchets
        l4_col1, l4_col2 = st.columns(2)
        cell8 = l4_col1.container(border=True)
        cell9 = l4_col2.container(border=True)

        # Ligne 5 : 2 graphiques en ligne : line chart volume + nb collectes et Pie niveau de caractérisation
        l5_col1, l5_col2 = st.columns(2)
        cell10 = l5_col1.container(border=True)
        cell11 = l5_col2.container(border=True)

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
        df_events_a_venir = df_events[
            df_events.DATE > (datetime.now() - timedelta(days=5))
        ]

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
else:
    st.markdown("## 🚨 Veuillez vous connecter pour accéder à l'onglet 🚨")
