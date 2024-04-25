import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import streamlit as st
import folium
from babel.dates import format_date, Locale

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
    """# 👊 Actions
Visualisez les actions réalisées et celles à venir
"""
)

if st.session_state["authentication_status"]:
    if filtre_niveau == "" and filtre_collectivite == "":
        st.write("Aucune sélection de territoire n'a été effectuée")
    else:
        st.write(f"Votre territoire : {filtre_niveau} {filtre_collectivite}")

    # Définition d'une fonction pour charger les evenements à venir
    def load_df_events_clean() -> pd.DataFrame:
        return pd.read_csv(
            "https://github.com/dataforgoodfr/12_zero_dechet_sauvage/raw/2-"
            "nettoyage-et-augmentation-des-donn%C3%A9es/Exploration_visuali"
            "sation/data/export_events_cleaned.csv"
        )

    # Appel des fonctions pour charger les données
    df_events = load_df_events_clean()

    # Appeler les dataframes volumes et nb_dechets filtré depuis le session state
    if "df_other_filtre" not in st.session_state:
        st.write(
            """
        ### :warning: Merci de sélectionner une collectivité\
        dans l'onglet Accueil pour afficher les données. :warning:
        """
        )
        st.stop()
    else:
        df_other = st.session_state["df_other_filtre"].copy()

    # 2 Onglets : Evènements, Evènements à venir
    tab1, tab2 = st.tabs(
        [
            "Ramassages réalisés ✔️",
            "Evènements à venir 🗓️",
        ]
    )

    # Locale du package Babel
    locale = Locale("fr", "FR")

    # Onglet 1 : Evènements
    with tab1:
        # Convertit la colonne de date en datetime
        df_other["DATE"] = pd.to_datetime(df_other["DATE"])

        # Liste des années pour le filtre
        annee_liste = sorted(df_other["ANNEE"].unique().tolist(), reverse=True)

        # Filtre par année:
        options = [
            f"Toute la période ({min(annee_liste)}-{max(annee_liste)})"
        ] + annee_liste
        annee_choisie = st.selectbox("Choisissez l'année:", options, index=0)

        # Selection d'une année dans le filtre -> affichage du second filtre MOIS
        if isinstance(annee_choisie, int):

            # Dict de mois
            mois_dict = {
                "January": 1,
                "February": 2,
                "March": 3,
                "April": 4,
                "May": 5,
                "June": 6,
                "July": 7,
                "August": 8,
                "September": 9,
                "October": 10,
                "November": 11,
                "December": 12,
            }

            # Liste des mois uniques pour l'année sélectionnée
            mois_liste = sorted(
                df_other[df_other["ANNEE"] == annee_choisie]["DATE"]
                .dt.strftime("%B")
                .unique()
                .tolist(),
                key=lambda x: mois_dict[x],
            )

            # Plage des index pour le filtre par mois
            range_mois_index = range(len(mois_liste) + 1)

            # Creation du select avec les mois de l'année choisie
            mois_choisi_index = st.selectbox(
                "Choisissez le mois:",
                range_mois_index,
                format_func=lambda x: f"Tous les mois de {annee_choisie}"
                if x == 0
                else str.capitalize(
                    format_date(
                        datetime(2022, mois_dict[mois_liste[x - 1]], 1),
                        format="MMMM",
                        locale=locale,
                    )
                ),
                index=0,
            )

            # Filtrer le DataFrame par année et mois sélectionnés
            if mois_choisi_index != 0:  # mois choisi
                mois_choisi = mois_liste[mois_choisi_index - 1]
                df_other_filtre = df_other[
                    (df_other["ANNEE"] == annee_choisie)
                    & (df_other["DATE"].dt.month == mois_dict[mois_choisi])
                ].copy()
            else:  # que l'année choisie
                df_other_filtre = df_other[df_other["ANNEE"] == annee_choisie].copy()
        else:  # pas d'année choisie
            df_other_filtre = df_other.copy()

        # Copie des données pour transfo
        df_ramassages = df_other_filtre.copy()

        # Calcul des indicateurs clés de haut de tableau avant transformation
        volume_total = df_ramassages["VOLUME_TOTAL"].sum()
        poids_total = df_ramassages["POIDS_TOTAL"].sum()
        nombre_participants = df_ramassages["NB_PARTICIPANTS"].sum()
        nb_collectes = len(df_ramassages)
        nombre_structures = df_ramassages["ID_STRUCTURE"].nunique()

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
        cell3.metric("Nombre de structures participantes", f"{nombre_structures}")

        # Ligne 2 : Carte
        # Initialisation du zoom sur la carte
        if filtre_niveau == "Commune":
            zoom_admin = 12
        elif filtre_niveau == "EPCI":
            zoom_admin = 13
        elif filtre_niveau == "Département":
            zoom_admin = 10
        else:
            zoom_admin = 8

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
                zoom_start=zoom_admin,
                #    zoom_start=8,
                tiles="OpenStreetMap",
            )
            # Facteur de normalisation pour ajuster la taille des bulles
            normalisation_facteur = 200
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
        df_carac_counts = df_carac_counts.sort_values(by="NIVEAU_CARAC")
        df_carac_counts.columns = ["NIVEAU_CARAC", "counts"]
        colors = px.colors.sequential.Blues[3:][::-1]

        fig1_actions = px.pie(
            df_carac_counts,
            values="counts",
            names="NIVEAU_CARAC",
            title="Répartition des niveaux de caractérisation",
            hole=0.5,
            color_discrete_sequence=colors,
            category_orders={"NIVEAU_CARAC": [0, 1, 2, 3, 4]},
        )
        fig1_actions.update_traces(
            textposition="inside", texttemplate="%{label}<br>%{percent:.1%}"
        )

        # préparation du dataframe et figure releves types de déchets
        df_type_dechet = df_other_filtre.copy()
        df_type_dechet_counts = (
            df_type_dechet["TYPE_DECHET"].value_counts().reset_index()
        )
        df_type_dechet_counts.columns = ["TYPE_DECHET", "counts"]
        df_type_dechet_counts_sorted = df_type_dechet_counts.sort_values(
            by="counts", ascending=False
        )
        fig2_actions = px.bar(
            df_type_dechet_counts_sorted,
            y="counts",
            x="TYPE_DECHET",
            title="Nombre de relevés par types de déchets",
            text="counts",
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

        # Ligne 4 : 2 graphiques en ligne : bar chart types milieux et bar chart types de lieux
        # préparation du dataframe et figure releves types de milieux
        df_milieux = df_other_filtre.copy()
        df_milieux_counts = df_milieux["TYPE_MILIEU"].value_counts().reset_index()
        df_milieux_counts.columns = ["TYPE_MILIEU", "counts"]
        df_milieux_counts_sorted = df_milieux_counts.sort_values(
            by="counts", ascending=True
        )

        # Retirer le texte entre parenthèses et les parenthèses elles-mêmes
        df_milieux_counts_sorted.TYPE_MILIEU = (
            df_milieux_counts_sorted.TYPE_MILIEU.str.replace(
                r"\([^()]*\)", "", regex=True
            ).str.strip()
        )

        fig3_actions = px.bar(
            df_milieux_counts_sorted,
            y="TYPE_MILIEU",
            x="counts",
            title="Nombre de relevés par types de milieux",
            text="counts",
            orientation="h",
        )
        fig3_actions.update_layout(xaxis_title="", yaxis_title="")

        # préparation du dataframe et figure releves types de lieux 2
        df_type_lieu2 = df_other_filtre.copy()
        df_type_lieu2_counts = df_type_lieu2["TYPE_LIEU2"].value_counts().reset_index()
        df_type_lieu2_counts.columns = ["TYPE_LIEU2", "counts"]
        df_type_lieu2_counts_sorted = df_type_lieu2_counts.sort_values(
            by="counts", ascending=False
        )

        # Retirer le texte entre parenthèses et les parenthèses elles-mêmes
        df_type_lieu2_counts_sorted.TYPE_LIEU2 = (
            df_type_lieu2_counts_sorted.TYPE_LIEU2.str.replace(
                r"\([^()]*\)", "", regex=True
            ).str.strip()
        )

        fig4_actions = px.bar(
            df_type_lieu2_counts_sorted,
            y="counts",
            x="TYPE_LIEU2",
            title="Nombre de relevés par types de lieu",
            text="counts",
        )
        fig4_actions.update_layout(xaxis_title="", yaxis_title="")
        fig4_actions.update_xaxes(tickangle=45)

        l4_col1, l4_col2 = st.columns(2)
        cell6 = l4_col1.container(border=True)
        cell7 = l4_col2.container(border=True)

        # Affichage barplot
        with cell6:
            st.plotly_chart(fig3_actions, use_container_width=True)
        # Affichage barplot
        with cell7:
            st.plotly_chart(fig4_actions, use_container_width=True)

        # préparation du dataframe et figure volume + nb collectes volume + nb collectes par mois
        # Créer une liste ordonnée des noms de mois dans l'ordre souhaité
        mois_ordre = [
            str.capitalize(format_date(dt, format="MMMM", locale=locale))
            for dt in pd.date_range(start="2022-01-01", end="2022-12-01", freq="MS")
        ]

        df_mois = df_other_filtre.copy()
        df_mois["DATE"] = pd.to_datetime(df_mois["DATE"])
        df_mois["MOIS"] = df_mois["DATE"].dt.month
        df_mois_counts = df_mois["MOIS"].value_counts().reset_index()
        df_mois_counts.columns = ["MOIS", "counts"]

        fig5_actions = px.bar(
            df_mois_counts,
            y="counts",
            x="MOIS",
            title="Nombre de relevés par mois",
            text="counts",
        )
        fig5_actions.update_layout(xaxis_title="", yaxis_title="")
        # Utiliser la liste mois_ordre comme étiquettes sur l'axe x
        fig5_actions.update_xaxes(tickvals=list(range(1, 13)), ticktext=mois_ordre)

        with st.container(border=True):
            # Affichage barplot
            st.plotly_chart(fig5_actions, use_container_width=True)

    # onglet Evenements a venir
    with tab2:
        #  Copie des données pour transfo
        df_events_a_venir = df_events.copy()

        # Convertit la col DATE en datetime pour formatage
        df_events_a_venir.DATE = pd.to_datetime(df_events.DATE)

        # Filtrer les événements à venir (jour de consultation -5 jours: pour afficher les possibles evenements en cours)
        df_events_a_venir = df_events_a_venir[
            df_events_a_venir.DATE > (datetime.now() - timedelta(days=5))
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

        # Ajout des marqueurs pour chaque événement à venir sur la carte
        for idx, row in df_events_a_venir.iterrows():
            # Personnalisation des Popup des markers

            # Vide si pas d'evenement d'envergure
            event_envg = (
                ""
                if pd.isna(row.EVENEMENT_ENVERGURE)
                else f'<div><span style="font-weight: bold;">Opération</span> : {row.EVENEMENT_ENVERGURE}</div>'
            )

            html = f"""
                <div style="font-family: LATO REGULAR, sans-serif; font-size: 12px;">
                    <p>
                        <div style="color: gray; font-size: 10px;">
                            {row.TYPE_EVENEMENT}
                        </div>
                        <div style="font-family: MONTSERRAT BOLD; font-weight: bold; font-size: 14px;">
                            {row.NOM_EVENEMENT}
                        </div>
                        <br>
                        <div style="font-weight: bold; color: gray;">
                            {str.capitalize(format_date(row.DATE, format="full", locale=locale))}
                        </div>
                    </p>
                    <p>
                        {event_envg}
                        <div><span style="font-weight: bold">Organisé par</span> : {row.NOM_STRUCTURE}</div>
                    </p>
                </div>
            """

            iframe = folium.IFrame(html=html, width=300, height=120)
            popup = folium.Popup(iframe, parse_html=True, max_width=300)

            folium.Marker(
                location=[row.COORD_GPS_Y, row.COORD_GPS_X],
                popup=popup,
                tooltip=row.NOM_VILLE,
                # icon=folium.Icon(icon_color=color_ZDS_bleu)
            ).add_to(map_events)

        # Afficher la liste des événements à venir avec la date affichée avant le nom
        st.subheader("Actions à venir :")

        carte, liste = st.columns(2)

        # Afficher la carte
        with carte:
            with st.container(border=True):
                st_folium = st.components.v1.html
                st_folium(
                    folium.Figure().add_child(map_events).render(),
                    # width=650, ne pas spécifié de largeur pour garder le coté responsive de la carte avec la liste à coté
                    height=600,
                )

        with liste:
            with st.container(
                height=600, border=False
            ):  # Container avec hauteur fixe => Scrollbar si beaucoup d'events
                for idx, row in df_events_a_venir.iterrows():
                    with st.container(border=True):
                        # Bloc contenant la date
                        date_block = f"<div style='font-weight:bold; color:{color_ZDS_rouge}; text-align: center;'>{row.DATE.day}<br>{str.capitalize(locale.months['format']['wide'][row.DATE.month - 1])}</div>"
                        # Bloc contenant le nom de l'événement
                        event_block = (
                            f"<div style='font-weight:bold;'>{row.NOM_EVENEMENT}</div>"
                        )
                        # Bloc contenant le type d'événement et le nom de la structure
                        type_structure_block = (
                            f"{row.TYPE_EVENEMENT} | {row.NOM_STRUCTURE}"
                        )

                        # Ajout de chaque événement dans la liste
                        st.write(
                            f"<div style='display:flex;'>{date_block}<div style='margin-left:10px;'>{event_block}<span>{type_structure_block}</span></div></div>",
                            unsafe_allow_html=True,
                        )

else:
    st.markdown("## 🚨 Veuillez vous connecter pour accéder à l'onglet 🚨")
