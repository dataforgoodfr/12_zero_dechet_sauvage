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

if st.session_state["authentication_status"]:
    if filtre_niveau == "" and filtre_collectivite == "":
        st.write("Aucune sélection de territoire n'a été effectuée")
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
        dans l'onglet Accueil pour afficher les données. :warning:
        """
        )
        st.stop()
    else:
        df_other = st.session_state["df_other_filtre"].copy()
        df_nb_dechet = st.session_state["df_nb_dechets_filtre"].copy()

    # Copier le df pour la partie filtrée par milieu/lieu/année
    df_other_metrics_raw = df_other.copy()

    # Fonction pour améliorer l'affichage des nombres (milliers, millions, milliards)
    def frenchify(x: int) -> str:
        if x > 1e9:
            y = x / 1e9
            return f"{y:,.2f} milliards".replace(".", ",")
        if x > 1e6:
            y = x / 1e6
            return f"{y:,.2f} millions".replace(".", ",")
        else:
            return f"{x:,.0f}".replace(",", " ")

    # 3 Onglets : Matériaux, Top déchets, Filières et marques
    tab1, tab2, tab3 = st.tabs(
        [
            "Matériaux :wood:",
            "Top Déchets :wastebasket:",
            "Secteurs, marques et filières REP :womans_clothes:",
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
        # Volume en litres dans la base, converti en m3
        volume_total_m3 = df_volume["VOLUME_TOTAL"].sum() / 1000
        poids_total = df_volume["POIDS_TOTAL"].sum()
        volume_total_categorise_m3 = df_volume[cols_volume].sum().sum() / 1000
        pct_volume_categorise = volume_total_categorise_m3 / volume_total_m3
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
        df_totals_sorted = df_volume.groupby(["Matériau"], as_index=False)[
            "Volume"
        ].sum()
        df_totals_sorted = df_totals_sorted.sort_values(["Volume"], ascending=False)
        # replace "Verre" with "Verre/Céramique" in df_totals_sorted
        df_totals_sorted["Matériau"] = df_totals_sorted["Matériau"].replace(
            "Verre", "Verre/Céramique"
        )
        df_totals_sorted["Matériau"] = df_totals_sorted["Matériau"].replace(
            "Papier", "Papier/Carton"
        )

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
        cell1.metric("Volume de déchets collectés", frenchify(volume_total_m3) + " m³")

        # 2ème métrique : poids
        cell2 = l1_col2.container(border=True)
        cell2.metric("Poids total collecté", frenchify(poids_total) + " kg")

        # 3ème métrique : nombre de relevés
        cell3 = l1_col3.container(border=True)
        cell3.metric("Nombre de ramassages", frenchify(nb_collectes_int))

        # Message d'avertissement nb de collectes en dessous de 5
        if nb_collectes_int <= 5:
            st.warning(
                "⚠️ Faible nombre de ramassages ("
                + str(nb_collectes_int)
                + ") dans la base de données."
            )

        st.caption(
            f"Note : Il n’y a pas de correspondance entre le poids et le volume global\
                    de déchets indiqués car certaines organisations \
                    ne renseignent que le volume sans mention de poids \
                    (protocole de niveau 1) ou inversement. De plus, \
                    les chiffres ci-dessous sont calculés sur XX ramassages \
                    ayant fait l’objet d’une estimation des volumes \
                    par matériau, soit un volume total de {volume_total_categorise_m3:.0f} m³."
        )

        # Ligne 2 : 2 graphiques en ligne : donut et bar chart matériaux

        with st.container(border=False):

            cell4, cell5 = st.columns(2)

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

                # Réglage du texte affiché, format et taille de police
                fig.update_traces(
                    textinfo="percent",
                    texttemplate="%{percent:.0%}",
                    textfont_size=14,
                )
                fig.update_layout(autosize=True, legend_title_text="Matériau")

                # Affichage du graphique
                st.plotly_chart(fig, use_container_width=True)

            with cell5:
                # Conversion des volumes en m3
                df_totals_sorted["Volume_m3"] = df_totals_sorted["Volume"] / 1000
                # Création du graphique en barres avec Plotly Express
                fig2 = px.bar(
                    df_totals_sorted,
                    x="Matériau",
                    y="Volume_m3",
                    text="Volume_m3",
                    title="Volume total par materiau (en m³)",
                    color="Matériau",
                    color_discrete_map=colors_map,
                )

                # Amélioration du graphique
                fig2.update_traces(
                    texttemplate="%{text:.2s}",
                    textposition="inside",
                    textfont_size=14,
                )
                fig2.update_layout(
                    autosize=True,
                    # uniformtext_minsize=8,
                    uniformtext_mode="hide",
                    xaxis_tickangle=-45,
                    showlegend=False,
                    yaxis_showgrid=False,
                    xaxis_title=None,
                    yaxis_title=None,
                )

                # Affichage du graphique
                st.plotly_chart(fig2, use_container_width=True)

        # Ligne 3 : Graphe par milieu de collecte

        # Grouper par année et type de matériau
        df_typemilieu = df_volume.groupby(["TYPE_MILIEU", "Matériau"], as_index=False)[
            "Volume"
        ].sum()
        df_typemilieu = df_typemilieu.sort_values(
            ["TYPE_MILIEU", "Volume"], ascending=False
        )

        # Raccourcir les étiquettes trop longues
        df_typemilieu = df_typemilieu.replace(
            {
                "Zone naturelle ou rurale (hors littoral et montagne)": "Zone naturelle ou rurale"
            }
        )

        # Graphique à barre empilées du pourcentage de volume collecté par an et type de matériau
        fig3 = px.histogram(
            df_typemilieu,
            x="TYPE_MILIEU",
            y="Volume",
            color="Matériau",
            barnorm="percent",
            title="Proportion de chaque matériau en volume selon le milieu de collecte",
            color_discrete_map=colors_map,
            text_auto=True,
        )
        # Format d'affichage
        fig3.update_layout(
            bargap=0.2,
            height=600,
            yaxis_title="Proportion du volume collecté (en %)",
            xaxis_title=None,
        )
        fig3.update_xaxes(tickangle=-30)
        # Etiquettes et formats de nombres
        fig3.update_traces(
            texttemplate="%{y:.0f}%",
            textposition="inside",
            hovertemplate="<b>%{x}</b><br>Part du volume collecté dans ce milieu: %{y:.0f} %",
            textfont_size=12,
        )

        # Afficher le graphique
        with st.container(border=False):
            st.plotly_chart(fig3, use_container_width=True)

        # Ligne 3 : Graphe par milieu , lieu et année
        st.write("**Filtrer les données par année, type de milieu ou type de lieu**")

        # Étape 1: Création des filtres

        df_other_metrics = df_other_metrics_raw.copy()
        df_other_metrics = df_other_metrics.fillna(0)

        with st.expander("Filtrer par année, type milieu ou type de lieu"):

            # Filtre par Année
            # Valeur par défaut sous forme de liste pour concaténation avec données
            valeur_par_defaut_annee = "Toute la période"

            selected_annee = st.selectbox(
                "Choisir une année:",
                options=[valeur_par_defaut_annee] + annee_liste,
            )
            if selected_annee != valeur_par_defaut_annee:
                filtered_data_milieu = df_other[
                    df_other["ANNEE"] == selected_annee
                ].copy()
                filtered_metrics_milieu = df_other_metrics[
                    df_other_metrics["ANNEE"] == selected_annee
                ].copy()
            else:
                filtered_data_milieu = df_other.copy()
                filtered_metrics_milieu = df_other_metrics.copy()

            # Filtre par milieu

            valeur_par_defaut_milieu = "Tous les milieux"

            selected_type_milieu = st.selectbox(
                "Choisir un type de milieu:",
                options=[valeur_par_defaut_milieu]
                + list(filtered_data_milieu["TYPE_MILIEU"].unique()),
            )

            if selected_type_milieu != valeur_par_defaut_milieu:
                filtered_data_lieu = filtered_data_milieu[
                    filtered_data_milieu["TYPE_MILIEU"] == selected_type_milieu
                ]
                filtered_metrics_milieu = filtered_metrics_milieu[
                    filtered_metrics_milieu["TYPE_MILIEU"] == selected_type_milieu
                ]
            else:
                filtered_data_lieu = filtered_data_milieu.copy()
                filtered_metrics_milieu = df_other_metrics.copy()

            # Filtre par type de lieu

            valeur_par_defaut_lieu = "Tous les lieux"

            selected_type_lieu = st.selectbox(
                "Choisir un type de lieu:",
                options=[valeur_par_defaut_lieu]
                + list(filtered_data_lieu["TYPE_LIEU"].unique()),
            )

        if (
            selected_annee == valeur_par_defaut_annee
            and selected_type_milieu == valeur_par_defaut_milieu
            and selected_type_lieu == valeur_par_defaut_lieu
        ):
            df_filtered = df_other.copy()
            df_filtered_metrics = df_other_metrics_raw.copy()
        elif (
            selected_type_milieu == valeur_par_defaut_milieu
            and selected_type_lieu == valeur_par_defaut_lieu
        ):
            df_filtered = df_other[df_other["ANNEE"] == selected_annee].copy()
            df_filtered_metrics = df_other_metrics_raw[
                df_other_metrics["ANNEE"] == selected_annee
            ].copy()
        elif (
            selected_annee == valeur_par_defaut_annee
            and selected_type_lieu == valeur_par_defaut_lieu
            and selected_type_milieu != valeur_par_defaut_milieu
        ):
            df_filtered = df_other[
                df_other["TYPE_MILIEU"] == selected_type_milieu
            ].copy()
            df_filtered_metrics = df_other_metrics_raw[
                df_other_metrics["TYPE_MILIEU"] == selected_type_milieu
            ].copy()

        elif (
            selected_annee == valeur_par_defaut_annee
            and selected_type_lieu != valeur_par_defaut_lieu
            and selected_type_milieu == valeur_par_defaut_milieu
        ):
            df_filtered = df_other[df_other["TYPE_LIEU"] == selected_type_lieu].copy()
            df_filtered_metrics = df_other_metrics_raw[
                df_other_metrics["TYPE_LIEU"] == selected_type_lieu
            ].copy()

        elif (
            selected_annee == valeur_par_defaut_annee
            and selected_type_lieu != valeur_par_defaut_lieu
            and selected_type_milieu != valeur_par_defaut_milieu
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
            selected_annee != valeur_par_defaut_annee
            and selected_type_lieu != valeur_par_defaut_lieu
            and selected_type_milieu == valeur_par_defaut_milieu
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
            selected_annee != valeur_par_defaut_annee
            and selected_type_lieu == valeur_par_defaut_lieu
            and selected_type_milieu != valeur_par_defaut_milieu
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
        # Volume litres converti en m3
        volume_total_filtered_m3 = df_filtered_metrics["VOLUME_TOTAL"].sum() / 1000

        cell6.metric(
            "Volume de déchets collectés", frenchify(volume_total_filtered_m3) + " m³"
        )

        cell7.metric("Poids total collecté", frenchify(poids_total_filtered) + " kg")

        nombre_collectes_filtered = len(df_filtered)
        cell8.metric("Nombre de ramassages", frenchify(nombre_collectes_filtered))

        # Message d'avertissement nb de collectes en dessous de 5
        if len(df_filtered) <= 5:
            st.warning(
                "⚠️ Faible nombre de ramassages disponibles dans la base de données : "
                + str(len(df_filtered))
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
        df_totals_sorted2 = df_volume2.groupby(["Matériau"], as_index=False)[
            "Volume"
        ].sum()
        df_totals_sorted2 = df_totals_sorted2.sort_values(["Volume"], ascending=False)
        # Conversion litres en m
        df_totals_sorted2["Volume_m3"] = df_totals_sorted2["Volume"] / 1000

        # Étape 4: Création du Graphique

        if not df_filtered.empty:

            fig4 = px.treemap(
                df_totals_sorted2,
                path=["Matériau"],
                values="Volume_m3",
                title="Répartition des matériaux en volume (données filtrées)",
                color="Matériau",
                color_discrete_map=colors_map,
            )
            fig4.update_layout(
                margin=dict(t=50, l=25, r=25, b=25), autosize=True, height=600
            )
            fig4.update_traces(
                textinfo="label+value",
                texttemplate="<b>%{label}</b><br>%{value:.1f} m³",
                textfont_size=16,
                hovertemplate="<b>Matériau : %{label}</b><br>Volume = %{value:.1f} m³",
            )

            with st.container(border=False):
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

        # Ligne 1 : 3 cellules avec les indicateurs clés en haut de page
        l1_col1, l1_col2, l1_col3 = st.columns(3)
        # Pour avoir 3 cellules avec bordure, il faut nester un st.container dans chaque colonne (pas d'option bordure dans st.column)
        # 1ère métrique : volume total de déchets collectés
        cell1 = l1_col1.container(border=True)
        # Trick pour séparer les milliers

        cell1.metric("Nombre de déchets catégorisés", frenchify(nb_total_dechets))

        # 2ème métrique : équivalent volume catégorisé
        cell2 = l1_col2.container(border=True)
        cell2.metric(
            "Equivalent en volume ",
            frenchify(volume_total_categorise_m3) + " m³",
        )

        # 3ème métrique : nombre de relevés
        cell3 = l1_col3.container(border=True)
        cell3.metric("Nombre de ramassages", frenchify(nb_collectes_int))

        # Message d'avertissement nb de collectes en dessous de 5
        if nb_collectes_int <= 5:
            st.warning(
                "⚠️ Le nombre de ramassages "
                + str(nb_collectes_int)
                + " est trop faible pour l'analyse."
            )

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
            labels={
                "categorie": "Dechet",
                "nb_dechet": "Nombre total de déchets (échelle logarithmique)",
            },
            title="Top 10 des déchets ramassés",
            text="nb_dechet",
            color="Materiau",
            color_discrete_map=colors_map,
            category_orders={"categorie": df_top10_dechets["categorie"].tolist()},
        )
        fig5.update_layout(xaxis_type="log")
        # suppression de la légende des couleurs
        fig5.update_layout(
            showlegend=True,
            height=700,
            uniformtext_minsize=8,
            uniformtext_mode="hide",
            yaxis_title=None,
            # Position de la légende
            legend=dict(
                yanchor="bottom",
                y=1.01,
                xanchor="right",
                x=0.95,
            ),
        )

        # Amélioration du visuel du graphique
        fig5.update_traces(
            # texttemplate="%{text:.2f}",
            textposition="inside",
            textfont_color="white",
            textfont_size=18,
        )

        # Suppression de la colonne categorie
        del df_top10_dechets["Materiau"]

        with st.container(border=True):
            st.plotly_chart(fig5, use_container_width=True)

            st.write("")
            st.caption(
                f"Note : Analyse basée sur les ramassages qui ont fait l'objet d'un comptage détaillé par déchet,\
         soit {volume_total_categorise_m3} m³ équivalent à {pct_volume_categorise:.0%} du volume collecté\
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
            # Initialisation du zoom sur la carte
            if filtre_niveau == "Commune":
                zoom_admin = 12
            elif filtre_niveau == "EPCI":
                zoom_admin = 13
            elif filtre_niveau == "Département":
                zoom_admin = 10
            else:
                zoom_admin = 8

            # Calcul des limites à partir de vos données
            min_lat = df_map_data["LIEU_COORD_GPS_Y"].min()
            max_lat = df_map_data["LIEU_COORD_GPS_Y"].max()
            min_lon = df_map_data["LIEU_COORD_GPS_X"].min()
            max_lon = df_map_data["LIEU_COORD_GPS_X"].max()

            map_data = folium.Map(
                location=[(min_lat + max_lat) / 2, (min_lon + max_lon) / 2],
                zoom_start=zoom_admin,
                #  zoom_start=8,
                tiles="OpenStreetMap",
            )

            # Facteur de normalisation pour ajuster la taille des bulles
            normalisation_facteur = 1000

            for index, row in df_map_data.iterrows():
                # Application de la normalisation
                radius = row["nb_dechet"] / normalisation_facteur

                # Application d'une limite minimale pour le rayon si nécessaire
                radius = max(radius, 5)

                folium.CircleMarker(
                    location=(row["LIEU_COORD_GPS_Y"], row["LIEU_COORD_GPS_X"]),
                    radius=radius,  # Utilisation du rayon ajusté
                    popup=f"{row['NOM_ZONE']}, {row['LIEU_VILLE']}, {row['DATE']} : {row['nb_dechet']} {selected_dechet}",
                    color="#3186cc",
                    fill=True,
                    fill_color="#3186cc",
                ).add_to(map_data)

            # Affichage de la carte Folium dans Streamlit
            st_folium = st.components.v1.html
            st_folium(
                folium.Figure().add_child(map_data).render(),  # , width=1400
                height=750,
            )
    # Onglet 3 : Secteurs et marques
    with tab3:
        st.write("")

        # Préparation des données
        df_dechet_copy = df_nb_dechet.copy()
        df_filtre_copy = df_other.copy()

        # Étape 1: Création des filtres

        with st.expander("Filtrer par année, type milieu ou type de lieu"):

            # Filtre par année
            selected_annee_onglet_3 = st.selectbox(
                "Choisir une année:",
                options=[valeur_par_defaut_annee] + annee_liste,
                key="année_select",
            )
            if selected_annee_onglet_3 != valeur_par_defaut_annee:
                filtered_data_milieu = df_other[
                    df_other["ANNEE"] == selected_annee_onglet_3
                ]
            else:
                filtered_data_milieu = df_other.copy()

            # Filtre par type de milieu
            selected_type_milieu_onglet_3 = st.selectbox(
                "Choisir un type de milieu:",
                options=[valeur_par_defaut_milieu]
                + list(filtered_data_milieu["TYPE_MILIEU"].unique()),
                key="type_milieu_select",
            )

            if selected_type_milieu_onglet_3 != valeur_par_defaut_milieu:
                filtered_data_lieu = filtered_data_milieu[
                    filtered_data_milieu["TYPE_MILIEU"] == selected_type_milieu_onglet_3
                ]
            else:
                filtered_data_lieu = filtered_data_milieu

            # Filtre par lieu
            selected_type_lieu_onglet_3 = st.selectbox(
                "Choisir un type de lieu:",
                options=[valeur_par_defaut_lieu]
                + list(filtered_data_lieu["TYPE_LIEU"].unique()),
                key="type_lieu_select",
            )

        if (
            selected_annee_onglet_3 == valeur_par_defaut_annee
            and selected_type_milieu_onglet_3 == valeur_par_defaut_milieu
            and selected_type_lieu_onglet_3 == valeur_par_defaut_lieu
        ):
            df_filtered = df_other.copy()
        elif (
            selected_type_milieu_onglet_3 == valeur_par_defaut_milieu
            and selected_type_lieu_onglet_3 == valeur_par_defaut_lieu
        ):
            df_filtered = df_other[df_other["ANNEE"] == selected_annee_onglet_3].copy()
        elif (
            selected_annee_onglet_3 == valeur_par_defaut_annee
            and selected_type_lieu_onglet_3 == valeur_par_defaut_lieu
            and selected_type_milieu_onglet_3 != valeur_par_defaut_milieu
        ):
            df_filtered = df_other[
                df_other["TYPE_MILIEU"] == selected_type_milieu_onglet_3
            ].copy()
        elif (
            selected_annee_onglet_3 == valeur_par_defaut_annee
            and selected_type_lieu_onglet_3 != valeur_par_defaut_lieu
            and selected_type_milieu_onglet_3 == valeur_par_defaut_milieu
        ):
            df_filtered = df_other[
                df_other["TYPE_LIEU"] == selected_type_lieu_onglet_3
            ].copy()
        elif (
            selected_annee_onglet_3 == valeur_par_defaut_annee
            and selected_type_lieu_onglet_3 != valeur_par_defaut_lieu
            and selected_type_milieu_onglet_3 != valeur_par_defaut_milieu
        ):
            df_filtered = df_other[
                (df_other["TYPE_LIEU"] == selected_type_lieu_onglet_3)
                & (df_other["TYPE_MILIEU"] == selected_type_milieu_onglet_3)
            ].copy()
        elif (
            selected_annee_onglet_3 != valeur_par_defaut_annee
            and selected_type_lieu_onglet_3 != valeur_par_defaut_lieu
            and selected_type_milieu_onglet_3 == valeur_par_defaut_milieu
        ):
            df_filtered = df_other[
                (df_other["ANNEE"] == selected_annee_onglet_3)
                & (df_other["TYPE_LIEU"] == selected_type_lieu_onglet_3)
            ].copy()
        elif (
            selected_annee_onglet_3 != valeur_par_defaut_annee
            and selected_type_lieu_onglet_3 == valeur_par_defaut_lieu
            and selected_type_milieu_onglet_3 != valeur_par_defaut_milieu
        ):
            df_filtered = df_other[
                (df_other["ANNEE"] == selected_annee_onglet_3)
                & (df_other["TYPE_MILIEU"] == selected_type_milieu_onglet_3)
            ].copy()

        elif selected_type_lieu_onglet_3 == valeur_par_defaut_lieu:
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
            secteur_df.groupby("categorie")["nb_dechet"]
            .sum()
            .sort_values(ascending=True)
        )
        top_secteur_df = top_secteur_df.reset_index()
        top_secteur_df.columns = ["Secteur", "Nombre de déchets"]
        top_secteur_df["Nombre de déchets"] = top_secteur_df[
            "Nombre de déchets"
        ].astype(int)

        # Data pour le plot marque
        marque_df = df_init[df_init["type_regroupement"].isin(["MARQUE"])]
        top_marque_df = (
            marque_df.groupby("categorie")["nb_dechet"]
            .sum()
            .sort_values(ascending=True)
        )
        top_marque_df = top_marque_df.reset_index()
        top_marque_df.columns = ["Marque", "Nombre de déchets"]
        top_marque_df["Nombre de déchets"] = top_marque_df["Nombre de déchets"].astype(
            int
        )

        # Data pour le plot responsabilités
        rep_df = df_init[df_init["type_regroupement"].isin(["REP"])]
        top_rep_df = (
            rep_df.groupby("categorie")["nb_dechet"].sum().sort_values(ascending=True)
        )
        top_rep_df = top_rep_df.reset_index()
        top_rep_df.columns = ["Responsabilité élargie producteur", "Nombre de déchets"]

        # Chiffres clés
        nb_dechet_secteur = secteur_df["nb_dechet"].sum()
        nb_secteurs = len(top_secteur_df["Secteur"].unique())
        nb_dechet_marque = marque_df["nb_dechet"].sum()
        nb_marques = len(top_marque_df["Marque"].unique())
        collectes = len(df_filtered)
        nb_dechet_rep = rep_df["nb_dechet"].sum()
        nb_rep = len(top_rep_df["Responsabilité élargie producteur"].unique())

        # Metriques et graphs secteurs
        # Retrait des categoriés "VIDE" et "INDERTERMINE" si présentes et recupération des valeurs
        nb_vide_indetermine = 0
        if "VIDE" in top_secteur_df["Secteur"].unique():
            df_vide_indetermine = top_secteur_df[top_secteur_df["Secteur"] == "VIDE"]
            nb_vide_indetermine = df_vide_indetermine["Nombre de déchets"].sum()
        elif "INDÉTERMINÉ" in top_secteur_df["Secteur"].unique():
            df_vide_indetermine = top_secteur_df[
                top_secteur_df["Secteur"] == "INDÉTERMINÉ"
            ]
            nb_vide_indetermine += df_vide_indetermine["Nombre de déchets"].sum()
        else:
            pass

        top_secteur_df = top_secteur_df[top_secteur_df["Secteur"] != "INDÉTERMINÉ"]
        top_secteur_df = top_secteur_df[top_secteur_df["Secteur"] != "VIDE"]

        # Ligne 1 : 3 cellules avec les indicateurs clés en haut de page
        l1_col1, l1_col2, l1_col3 = st.columns(3)
        # Pour avoir 3 cellules avec bordure, il faut nester un st.container dans chaque colonne (pas d'option bordure dans st.column)
        # 1ère métrique : volume total de déchets collectés
        cell1 = l1_col1.container(border=True)

        # Trick pour séparer les milliers
        cell1.metric(
            "Nombre de déchets avec secteur identifié", frenchify(nb_dechet_secteur)
        )

        # 2ème métrique : poids
        cell2 = l1_col2.container(border=True)
        cell2.metric(
            "Nombre de secteurs identifiés dans les déchets collectés",
            frenchify(nb_secteurs) + " secteurs",
        )

        # 3ème métrique : nombre de collectes
        cell3 = l1_col3.container(border=True)
        cell3.metric(
            "Nombre de ramassages",
            frenchify(collectes),
        )

        # Message d'avertissement nb de collectes en dessous de 5
        if collectes <= 5:
            st.warning(
                "⚠️ Faible nombre de ramassages ("
                + str(collectes)
                + ") dans la base de données."
            )

        # Ligne 2 : 3 cellules avec les indicateurs clés en bas de page
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
            top_secteur_df.tail(10).sort_values(
                by="Nombre de déchets", ascending=False
            ),
            x="Nombre de déchets",
            y="Secteur",
            color="Secteur",
            title="Top 10 des secteurs économiques identifiés dans les déchets comptés",
            labels={
                "Nombre de déchets": "Nombre total de déchets (échelle logarithmique)",
            },
            orientation="h",
            color_discrete_map=colors_map_secteur,
            text_auto=True,
        )
        # add log scale to x axis
        fig_secteur.update_layout(xaxis_type="log")
        fig_secteur.update_traces(
            texttemplate="%{value:.0f}",
            textposition="inside",
            textfont_size=14,
        )
        fig_secteur.update_layout(
            height=700,
            uniformtext_mode="hide",
            showlegend=False,
            yaxis_title=None,
        )
        with st.container(border=True):
            st.plotly_chart(fig_secteur, use_container_width=True)

        # Message d'avertissement Nombre de dechets dont le secteur n'a pas été determine
        if nb_vide_indetermine != 0:
            st.warning(
                "⚠️ Il y a "
                + str(frenchify(nb_vide_indetermine))
                + " déchets dont le secteur n'a pas été determiné dans les déchets collectés."
            )

        # Metriques et graphes marques
        l2_col1, l2_col2 = st.columns(2)
        cell4 = l2_col1.container(border=True)

        # 1er métrique : nombre de dechets categorises par marques

        cell4.metric(
            "Nombre de déchets dont la marque est identifiée",
            frenchify(nb_dechet_marque) + " déchets",
        )

        # 2ème métrique : nombre de marques identifiées lors des collectes
        cell5 = l2_col2.container(border=True)
        cell5.metric(
            "Nombre de marques identifiées",
            frenchify(nb_marques) + " marques",
        )

        fig_marque = px.bar(
            top_marque_df.tail(10).sort_values(by="Nombre de déchets", ascending=True),
            x="Nombre de déchets",
            y="Marque",
            title="Top 10 des marques identifiées dans les déchets comptés",
            labels={
                "Nombre de déchets": "Nombre total de déchets (échelle logarithmique)",
            },
            color_discrete_sequence=["#1951A0"],
            orientation="h",
            text_auto=False,
            text=top_marque_df.tail(10)["Marque"]
            + " : "
            + top_marque_df.tail(10)["Nombre de déchets"].astype(str),
        )
        # add log scale to x axis
        fig_marque.update_layout(xaxis_type="log")
        fig_marque.update_traces(textfont_size=14)
        fig_marque.update_layout(
            height=700,
            uniformtext_minsize=8,
            uniformtext_mode="hide",
            yaxis_title=None,
        )

        with st.container(border=True):
            st.plotly_chart(fig_marque, use_container_width=True)

        with st.container(border=True):
            st.caption(
                "La Responsabilité Élargie du Producteur (REP) est une obligation qui impose aux entreprises de payer une contribution financière"
                + " pour la prise en charge de la gestion des déchets issus des produits qu’ils mettent sur le marché selon le principe pollueur-payeur."
                + " Pour ce faire, elles doivent contribuer financièrement à la collecte, du tri et au recyclage de ces produits, "
                + "généralement à travers les éco-organismes privés, agréés par l’Etat, comme CITEO pour les emballages. "
                + "L’État a depuis 1993 progressivement mis en place 25 filières REP, qui regroupent de grandes familles de produits "
                + "(emballages ménagers, tabac, textile, ameublement, …)."
            )

        # Metriques et graphes Responsabilité elargie producteurs
        l3_col1, l3_col2 = st.columns(2)
        # Pour avoir 3 cellules avec bordure, il faut nester un st.container dans chaque colonne (pas d'option bordure dans st.column)
        # Suppression de la catégorie "VIDE"
        nb_vide_rep = 0
        if "VIDE" in top_rep_df["Responsabilité élargie producteur"].unique():
            df_vide_rep = top_rep_df[
                top_rep_df["Responsabilité élargie producteur"] == "VIDE"
            ]
            nb_vide_rep = df_vide_rep["Nombre de déchets"].sum()
        else:
            pass
        top_rep_df = top_rep_df[
            top_rep_df["Responsabilité élargie producteur"] != "VIDE"
        ]

        # 1ère métrique : nombre de dechets catégorisés repartis par responsabilités
        cell6 = l3_col1.container(border=True)
        cell6.metric(
            "Nombre de déchets catégorisés par filière REP",
            frenchify(nb_dechet_rep),
        )

        # 2ème métrique : nombre de responsabilités
        cell7 = l3_col2.container(border=True)
        cell7.metric(
            "Nombre de filières REP identifiées",
            frenchify(nb_rep) + " filières",
        )

        # Treemap REP
        figreptree = px.treemap(
            top_rep_df.tail(10).sort_values(by="Nombre de déchets", ascending=True),
            path=["Responsabilité élargie producteur"],
            values="Nombre de déchets",
            title="Top 10 des filières REP relatives aux déchets les plus ramassés",
            color="Responsabilité élargie producteur",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        figreptree.update_layout(
            margin=dict(t=50, l=25, r=25, b=25), autosize=True, height=600
        )
        figreptree.update_traces(
            textinfo="label+value",
            texttemplate="<b>%{label}</b><br>%{value:.0f} items",
            textfont=dict(size=16),
            hovertemplate="<b>%{label}</b><br>Nombre de déchets : %{value:.0f}",
        )

        with st.container(border=True):
            st.plotly_chart(figreptree, use_container_width=True)

        # Message d'avertissement Nombre de déchets dont la REP n'a pas été determine
        if nb_vide_rep != 0:
            st.warning(
                "⚠️ Il y a "
                + str(frenchify(nb_vide_rep))
                + " déchets dont la filière REP n'a pas été determinée dans les déchets collectés."
            )


else:
    st.markdown("## 🚨 Veuillez vous connecter pour accéder à l'onglet 🚨")
