import streamlit as st
import mysql.connector
import pandas as pd
import numpy as np
import plotly.express as px
import folium
from folium import IFrame
import math
import locale
import duckdb
import json

###########################################################
# Configuration de la page
###########################################################
st.set_page_config(
    layout="wide", page_title="Dashboard Zéro Déchet Sauvage : onglet Data"
)

# Titre de l'onglet
st.markdown(
    """# 🔎 Data
Visualisez les impacts sur les milieux naturels et secteurs/filières/marques à l’origine de cette pollution
"""
)


# 3 Onglets : Matériaux, Top déchets, Filières et marques
tab1, tab2, tab3 = st.tabs(
    [
        "**Matériaux :wood:**",
        "**Top Déchets :wastebasket:**",
        "**Secteurs économiques, filières et marques :womans_clothes:**",
    ]
)

# Définir les paramètres linguistiques FR pour l'affichage des nombres
locale.setlocale(locale.LC_NUMERIC, "fr_FR.utf8")

# Fonction pour améliorer l'affichage des nombres (milliers, millions, milliards)
def french_format(x: int) -> str:
    if x >= 1e9:
        y = x / 1e9
        y = locale.format_string("%.2f", y, grouping=True)
        return f"{y} milliards"
    elif x >= 1e6:
        y = x / 1e6
        y = locale.format_string("%.2f", y, grouping=True)
        return f"{y} millions"
    elif x >= 10:
        y = locale.format_string("%d", x, grouping=True)
        return f"{y}"
    else:
        y = locale.format_string("%.2f", x, grouping=True)
        return f"{y}"


###########################################################
# Import des données
###########################################################

# Importer le session.state pour récupérer les filtres géographiques
filtre_niveau = st.session_state.get("niveau_admin", "")
filtre_collectivite = st.session_state.get("collectivite", "")

## Import des fichiers de config des chartes graphiques
# Couleurs par matériaux charte graphique MERTERRE
with open("pages/ongletdata_colormap_materiaux.json", "r") as jsonfile1:
    colors_map = json.load(jsonfile1)

# Couleurs par secteur (charte Merterre)
with open("pages/ongletdata_colormap_secteurs.json", "r") as jsonfile2:
    colors_map_secteur = json.load(jsonfile2)


# Authentification
if st.session_state["authentication_status"]:
    if filtre_niveau == "" and filtre_collectivite == "":
        with st.sidebar:
            st.warning("⚠️ Aucune sélection de territoire n'a été effectuée")
    else:
        with st.sidebar:
            st.info(
                f" Territoire sélectionné : **{filtre_niveau} {filtre_collectivite}**",
                icon="🌍",
            )
    # Définition d'une fonction pour charger les données du nombre de déchets@st.cache_data
    def load_df_dict_corr_dechet_materiau(_cnx: mysql.connector.connection.MySQLConnection) -> pd.DataFrame:
        query="SELECT * FROM dict_dechet_groupe_materiau;"
        df = pd.read_sql(query, _cnx)
        df.columns = [c.upper() for c in df.columns]
        return df

    # Appel des fonctions pour charger les données
    cnx = st.session_state["cnx"] 
    df_dict_corr_dechet_materiau = load_df_dict_corr_dechet_materiau(cnx)

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

    # Exclusion des ramassages de niveau 0 ou avec 100% de AUTRES
    def carac_exclusions(df):
        conditions = [
            df["NIVEAU_CARAC"] == 0,
            df["GLOBAL_VOLUME_AUTRE"] == df["VOLUME_TOTAL"],
        ]
        choices = ["Exclu - niveau 0", "Exclu - 100% Autre"]
        return np.select(conditions, choices, default="Inclus")

    # Appliquer la fonction au dataframe
    df_other["Exclusions"] = carac_exclusions(df_other)

    # Raccourcir les étiquettes de milieux trop longues
    df_other = df_other.replace(
        {
            "Zone naturelle ou rurale (hors littoral et montagne)": "Zone naturelle ou rurale"
        }
    )

    milieu_lieu_dict = (
        df_other.groupby("TYPE_MILIEU")["TYPE_LIEU"]
        .unique()
        .apply(lambda x: x.tolist())
        .to_dict()
    )

    annee_liste = sorted(df_other["ANNEE"].unique().tolist(), reverse=True)
    ###########################################################
    # Onglet 1 : Matériaux
    ###########################################################
    with tab1:

        # Transformation du dataframe pour les graphiques
        # Variables à conserver en ligne
        cols_identifiers = [
            "ID_RELEVE",
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
        volume_total_categorise_avant_exclusions = (
            df_other[cols_volume].sum().sum() / 1000
        )

        # Copie des données pour transfo
        df_volume = df_other.copy()

        # Retrait des lignes avec 100% de volume catégorisé en AUTRE
        df_volume_cleaned = df_volume[df_volume["Exclusions"] == "Inclus"]

        # Calcul des indicateurs clés de haut de tableau avant transformation
        # Volume en litres dans la base, converti en m3
        volume_total_m3 = df_volume["VOLUME_TOTAL"].sum() / 1000
        poids_total = df_volume["POIDS_TOTAL"].sum()
        volume_total_categorise_apres_exclusions_m3 = (
            df_volume_cleaned[cols_volume].sum().sum() / 1000
        )
        pct_volume_categorise = (
            volume_total_categorise_apres_exclusions_m3 / volume_total_m3
        )
        # Nb total de collecte incluant les 100% autres et les relevés de niveau 0
        nb_collectes_int = df_volume["ID_RELEVE"].nunique()
        # Nb de collectes excluant les 100% autres et les relevés de niveau 0
        nb_collectes_carac = df_volume_cleaned["ID_RELEVE"].nunique()

        # estimation du poids categorisée en utilisant pct_volume_categorise
        poids_total_categorise = round(poids_total * pct_volume_categorise)

        # Dépivotage du tableau pour avoir une base de données exploitable
        df_volume_cleaned = df_volume_cleaned.melt(
            id_vars=cols_identifiers,
            value_vars=cols_volume,
            var_name="Matériau",
            value_name="Volume",
        )

        # Nettoyage des lignes à 0 et conversion m3
        df_volume_cleaned = df_volume_cleaned[df_volume_cleaned["Volume"] != 0]
        df_volume_cleaned["Volume_m3"] = df_volume_cleaned["Volume"] / 1000

        # Nettoyer le nom du Type déchet pour le rendre plus lisible
        df_volume_cleaned["Matériau"] = (
            df_volume_cleaned["Matériau"].str.replace("GLOBAL_VOLUME_", "").str.title()
        )

        ## Création du dataframe groupé par type de matériau pour les visualisations
        df_totals_sorted = df_volume_cleaned.groupby(["Matériau"], as_index=False)[
            "Volume_m3"
        ].sum()
        df_totals_sorted = df_totals_sorted.sort_values(["Volume_m3"], ascending=False)

        # Remplacer "Verre" with "Verre/Céramique" dans df_totals_sorted
        df_totals_sorted["Matériau"] = df_totals_sorted["Matériau"].replace(
            "Verre", "Verre/Céramique"
        )
        df_totals_sorted["Matériau"] = df_totals_sorted["Matériau"].replace(
            "Papier", "Papier/Carton"
        )

        # Message d'avertissement en haut de page si nb de collectes < 5
        if nb_collectes_int < 5:
            st.warning("⚠️ Moins de 5 ramassages dans la base de données")

        ### 3 METRIQUES CLES
        # Création des colonnes
        l1_col1, l1_col2, l1_col3 = st.columns(3)

        # Pour avoir 3 cellules avec bordure, il faut nester un st.container dans chaque colonne
        # 1ère métrique : volume total de déchets collectés
        cell1 = l1_col1.container(border=True)
        # Trick pour séparer les milliers
        cell1.metric(
            "Volume de déchets collectés", french_format(volume_total_m3) + " m³"
        )

        # 2ème métrique : poids
        cell2 = l1_col2.container(border=True)
        cell2.metric("Poids total collecté", french_format(poids_total) + " kg")

        # 3ème métrique : nombre de relevés
        cell3 = l1_col3.container(border=True)
        cell3.metric("Nombre de ramassages", nb_collectes_int)

        # Périmètre des données
        volume_total_avant_exclusions_m3 = df_other["VOLUME_TOTAL"].sum() / 1000
        volume_exclu = (
            volume_total_categorise_avant_exclusions
            - volume_total_categorise_apres_exclusions_m3
        )
        volume_global_percentage_nul = (
            df_other[df_other["GLOBAL_POURCENTAGE_TOTAL"] == 0]["VOLUME_TOTAL"].sum()
            / 1000
        )

        # Encart méthodo pour expliquer les données retenues pour l'analyse
        with st.expander("Note sur les données utilisées dans cet onglet"):
            st.markdown(
                f"""
                - Il n’y a pas de correspondance entre le poids et le volume global\
                    de déchets indiqués car certaines organisations \
                    ne renseignent que le volume sans mention de poids \
                    (protocole de niveau 1) ou inversement.
                - Certaines collectes n'ont pas fait l'objet d'un comptage par matériau. Par conséquent, le volume utilisé pour l'analyse est de **{french_format(volume_total_categorise_apres_exclusions_m3)} m³**, calculé sur **{nb_collectes_carac} ramassages** \
                
                - Détails : 
                    - Volume total enregistré dans la base de données :  {french_format(volume_total_avant_exclusions_m3)} m³
                    - Volume correspondant aux collectes qui n'ont pas fait l'objet d'un comptage par matériau : {french_format(volume_global_percentage_nul)} m³
                    - Relevés de niveau 0 et relevés comptabilisant 100% de déchets 'AUTRES', exclus de l'analyse : {french_format(volume_exclu)} m³
                    - Volume final utilisé pour l'analyse par matériaux : {french_format(volume_total_categorise_apres_exclusions_m3)} m³
                    
                    """
            )
            # Afficher le nombre de relevés inclus ou exclus
            df_note_methodo = (
                df_volume.groupby(["Exclusions"], as_index=True)["ID_RELEVE"]
                .count()
                .sort_values(ascending=False)
            )
            df_note_methodo.rename("Nombre de relevés", inplace=True)

        ### GRAPHIQUES DONUT ET BAR CHART MATERIAUX
        with st.container(border=True):

            cell4, cell5 = st.columns(2)

            with cell4:

                # Création du diagramme en donut en utilisant le dictionnaire de couleurs pour la correspondance
                fig = px.pie(
                    df_totals_sorted,
                    values="Volume_m3",
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
                    direction="clockwise",
                    rotation=-90,
                )

                # Paramétrage de l'étiquette flottante
                fig.update_traces(
                    hovertemplate="<b>%{label}</b> : <b>%{value:.1f} m³</b>"
                    + "<br>%{percent:.1%} du volume total"
                )

                # Définir titre légende et changer séparateurs des nombres pour affichage FR
                fig.update_layout(
                    autosize=True, legend_title_text="Matériau", separators=", "
                )

                # Affichage du graphique
                st.plotly_chart(fig, use_container_width=True)

            with cell5:

                # Création du graphique en barres avec Plotly Express
                fig2 = px.bar(
                    df_totals_sorted,
                    x="Matériau",
                    y="Volume_m3",
                    text="Volume_m3",
                    title="Volume total par materiau (m³)",
                    color="Matériau",
                    color_discrete_map=colors_map,
                )

                # Amélioration du graphique
                fig2.update_traces(
                    texttemplate="%{text:.2f}",
                    textposition="inside",
                    textfont_size=14,
                )

                # Paramétrage de l'étiquette flottante
                fig2.update_traces(
                    hovertemplate="Matériau : %{label}<br>Volume : <b>%{value:.2f} m³</b>"
                )

                fig2.update_layout(
                    autosize=True,
                    uniformtext_minsize=10,
                    uniformtext_mode="hide",
                    xaxis_tickangle=-45,
                    showlegend=False,
                    yaxis_showgrid=False,
                    xaxis_title=None,
                    yaxis_title=None,
                    separators=", ",
                )
                fig2.update_xaxes(
                    tickfont=dict(size=14)
                )  # Taille des étiquettes en abcisse

                # Affichage du graphique
                st.plotly_chart(fig2, use_container_width=True)

        ### GRAPHIQUE PAR MILIEU DE COLLECTE

        # Calcul du dataframe groupé par milieu et matériau pour le graphique
        df_typemilieu = df_volume_cleaned.groupby(
            ["TYPE_MILIEU", "Matériau"], as_index=False
        ).agg({"Volume_m3": "sum", "ID_RELEVE": "count"})

        df_typemilieu = df_typemilieu.sort_values(
            ["TYPE_MILIEU", "Volume_m3"], ascending=True
        )

        # Calcul du nombre de collectes par milieu pour exclure les milieux à moins de 3 collectes
        df_nb_par_milieu = (
            df_other.groupby("TYPE_MILIEU", as_index=True)
            .agg(
                {
                    "ID_RELEVE": "count",
                }
            )
            .sort_values("TYPE_MILIEU", ascending=True)
        )

        # Exclure les milieux avec moins de 3 collectes
        milieux_a_exclure = df_nb_par_milieu[
            df_nb_par_milieu["ID_RELEVE"] <= 3
        ].index.to_list()
        df_nb_par_milieu = df_nb_par_milieu.drop(milieux_a_exclure, axis=0)
        df_typemilieu = df_typemilieu[
            ~df_typemilieu["TYPE_MILIEU"].isin(milieux_a_exclure)
        ]

        # Ne pas faire apparaître la catégorie "Multi-lieux"
        lignes_multi = df_typemilieu.loc[df_typemilieu["TYPE_MILIEU"] == "Multi-lieux"]
        df_typemilieu.drop(lignes_multi.index, axis=0, inplace=True)

        # Fusionner les dataframe pour obtenir le nb de collectes et le volume par milieu
        df_nb_par_milieu = pd.merge(
            df_nb_par_milieu,
            df_typemilieu.groupby("TYPE_MILIEU")["Volume_m3"].sum(),
            on="TYPE_MILIEU",
            how="left",
        )

        # Graphique à barre empilées du pourcentage de volume collecté par an et type de matériau
        fig3 = px.histogram(
            df_typemilieu,
            x="TYPE_MILIEU",
            y="Volume_m3",
            color="Matériau",
            barnorm="percent",
            title="Proportion de matériaux ramassés en fonction du milieu",
            color_discrete_map=colors_map,
            text_auto=True,
        )
        #  Format d'affichage
        # traceorder : inverse l'ordre de la légende pour correspondre au graph
        fig3.update_layout(
            bargap=0.2,
            height=600,
            yaxis_title="Proportion du volume ramassé (en %)",
            xaxis_title=None,
            legend={"traceorder": "reversed"},
            separators=", ",
        )

        fig3.update_xaxes(
            tickangle=-30,  # ORientation des étiquettes de l'axe X
            tickfont=dict(size=14),
        )  # Taille des étiquettes en ordonnée

        # Etiquettes et formats de nombres
        fig3.update_traces(
            texttemplate="%{y:.0f}%",
            textposition="inside",
            textfont_size=12,
        )
        # Paramétrer l'étiquette flottante
        fig3.update_traces(
            hovertemplate="Ce matériau représente<br>"
            + "<b>%{y:.1f} %</b> "
            + "du volume ramassé<br> dans "
            + "le milieu <b>%{x}</b>."
        )

        # Afficher le graphique
        with st.container(border=True):

            # Message d'avertissement si pas de données à afficher
            if len(df_typemilieu) != 0:

                # Afficher le graphique
                st.plotly_chart(fig3, use_container_width=True)

                # Ne pas faire apparaître la catégorie "Multi-lieux"
                lignes_multi = df_nb_par_milieu.loc[
                    df_nb_par_milieu.index == "Multi-lieux"
                ]
                df_nb_par_milieu.drop(lignes_multi.index, axis=0, inplace=True)

                # Renommage des colonnes pour l'affichage
                df_nb_par_milieu.rename(
                    {
                        "TYPE_MILIEU": "Milieu",
                        "ID_RELEVE": "Ramassages",
                    },
                    axis=1,
                    inplace=True,
                )

                # Convertir en int pour éviter les virgules à l'affichage
                df_nb_par_milieu = df_nb_par_milieu.astype("int")

                # Affichage du tableau
                st.write("**Nombre de ramassages par milieu**")
                st.table(df_nb_par_milieu.T)
                st.caption(
                    f"Les ramassages catégorisés en 'Multi-lieux' "
                    + f"ont été retirés de l'analyse. "
                    + f"Les milieux représentant moins de 3 ramassages ne sont pas affichés."
                )

            else:
                st.warning(
                    "⚠️ Aucune donnée à afficher par type de milieu (nombre de ramassages trop faible)"
                )

        ### GRAPHIQUE TREEMAP PAR MILIEU, LIEU ET ANNEE
        st.write("**Détail par année, type de milieu ou de lieu**")

        # Étape 1: Création des filtres

        with st.expander("Filtrer par année, type milieu ou type de lieu"):

            # Filtre par Année
            # Valeurs par défaut
            valeur_par_defaut_annee = "Toute la période"
            valeur_par_defaut_milieu = "Tous les milieux"
            valeur_par_defaut_lieu = "Tous les lieux"

            # Filtre par année
            selected_annee = st.selectbox(
                "Choisir une année:",
                options=[valeur_par_defaut_annee] + annee_liste,
            )
            filtered_data = df_other.copy()
            if selected_annee != valeur_par_defaut_annee:
                filtered_data = filtered_data[filtered_data["ANNEE"] == selected_annee]

            # Filtre par milieu
            milieux_liste = [valeur_par_defaut_milieu] + sorted(
                filtered_data["TYPE_MILIEU"].unique()
            )
            selected_type_milieu = st.selectbox(
                "Choisir un type de milieu:",
                options=milieux_liste,
            )

            if selected_type_milieu != valeur_par_defaut_milieu:
                filtered_data = filtered_data[
                    filtered_data["TYPE_MILIEU"] == selected_type_milieu
                ]

            # Filtre par lieu
            lieux_liste = [valeur_par_defaut_lieu] + sorted(
                filtered_data["TYPE_LIEU"].unique()
            )
            selected_type_lieu = st.selectbox(
                "Choisir un type de lieu:",
                options=lieux_liste,
            )

            if selected_type_lieu != valeur_par_defaut_lieu:
                filtered_data = filtered_data[
                    filtered_data["TYPE_LIEU"] == selected_type_lieu
                ]

            # Dataframe final filtré par année, milieu et lieu
            df_filtered = filtered_data.copy()

        # Message d'avertissement nb de collectes en dessous de 5
        if len(df_filtered) < 5:
            st.warning("⚠️ Moins de 5 ramassages dans la base de données")

        ### 3 METRIQUES AVEC FILTRES
        l5_col1, l5_col2, l5_col3 = st.columns(3)
        cell6 = l5_col1.container(border=True)
        cell7 = l5_col2.container(border=True)
        cell8 = l5_col3.container(border=True)

        poids_total_filtered = df_filtered["POIDS_TOTAL"].sum()
        # Volume litres converti en m3
        volume_total_filtered_m3 = df_filtered["VOLUME_TOTAL"].sum() / 1000

        cell6.metric(
            "Volume de déchets collectés",
            french_format(volume_total_filtered_m3) + " m³",
        )

        cell7.metric(
            "Poids total collecté", french_format(poids_total_filtered) + " kg"
        )

        nombre_collectes_filtered = len(df_filtered)
        cell8.metric("Nombre de ramassages", nombre_collectes_filtered)

        # Étape 3: Preparation dataframe pour graphe
        # Copie des données pour transfo
        df_volume2 = df_filtered.copy()

        # Retrait des lignes avec 100% de volume catégorisé en AUTRE
        df_volume2 = df_volume2[df_volume2["Exclusions"] == "Inclus"]

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
                margin=dict(t=50, l=25, r=25, b=25),
                autosize=True,
                height=600,
                separators=", ",  # Séparateurs décimales et milliers
            )
            fig4.update_traces(
                textinfo="label+value+percent root",
                texttemplate="<b>%{label}</b><br>%{value:.2f} m³<br>%{percentRoot}",
                textfont_size=16,
                hovertemplate="<b>%{label} : %{value:.2f} m³ </b>"
                + "<br>%{percentRoot:.1%} du volume total",
            )

            with st.container(border=True):
                st.plotly_chart(fig4, use_container_width=True)

        else:
            st.write("Aucune donnée à afficher pour les filtres sélectionnés.")

    ###########################################################
    # Onglet 2 : Top Déchets
    ###########################################################
    with tab2:

        # Préparation des datas pour l'onglet 2
        df_top_dechets = df_nb_dechet.copy()

        # Filtres
        with st.expander("Filtrer par année, type milieu ou type de lieu"):

            filtered_df = df_other.copy()  # Initialiser le df sans filtres

            # Definir options initiales sans filtres
            annee_options = [valeur_par_defaut_annee] + sorted(
                df_other["ANNEE"].unique().tolist(), reverse=True
            )
            milieu_options = [valeur_par_defaut_milieu]
            lieu_options = [valeur_par_defaut_lieu]

            annee = st.selectbox(
                "Choisir une année :",
                options=annee_options,
                index=0,  # Définir l'index
                key="topdechets_annee",  # définir key pour éviter conflits
            )

            # Appliquer les filtres sur les données
            if annee != valeur_par_defaut_annee:
                filtered_df = filtered_df[filtered_df["ANNEE"] == annee]

            # Mettre à jour les options de milieux selon le filtre année
            milieu_options += sorted(filtered_df["TYPE_MILIEU"].unique().tolist())

            milieu = st.selectbox(
                "Choisir un type de milieu :",
                options=milieu_options,
                index=0,  # Définir l'index
                key="topdechets_milieu",  # définir key pour éviter conflits
            )

            # Appliquer le filtre par milieu si une valeur est choisir
            if milieu != valeur_par_defaut_milieu:
                filtered_df = filtered_df[filtered_df["TYPE_MILIEU"] == milieu]

            # Mettre à jour les options de lieu selon le milieu choisi
            lieu_options += sorted(filtered_df["TYPE_LIEU"].unique().tolist())

            # Selection du lieu
            lieu = st.selectbox(
                "Choisir un type de lieu :",
                options=lieu_options,
                index=0,  # Default to the first option (valeur_par_defaut_lieu)
                key="topdechets_lieu",
            )

            # Appliquer filtre par lieu si choixi
            if lieu != valeur_par_defaut_lieu:
                filtered_df = filtered_df[filtered_df["TYPE_LIEU"] == lieu]

        # Récupérer les index de collectes pour filtrer le dataframe nb_dechets
        # Filtrer les données sur les ID_RELEVES
        df_top_dechets = pd.merge(
            df_top_dechets, filtered_df, on="ID_RELEVE", how="inner"
        )

        # Retrait des lignes avec 100% de volume catégorisé en AUTRE
        df_top_dechets = df_top_dechets[df_top_dechets["Exclusions"] == "Inclus"]

        # Calcul du nombre total de déchets catégorisés sur le territoier
        nb_total_dechets = df_top_dechets[
            (df_top_dechets["TYPE_REGROUPEMENT"] == "GROUPE")
        ]["NB_DECHET"].sum()

        nb_collec_top = df_top_dechets["ID_RELEVE"].nunique()

        # Message d'avertissement nb de collectes en dessous de 5
        if nb_collectes_int < 5:
            st.warning("⚠️ Moins de 5 ramassages dans la base de données")

        ### METRIQUES CLES EN HAUT DE PAGE

        l1_col1, l1_col2 = st.columns(2)

        # 1ère métrique : volume total de déchets collectés
        cell1 = l1_col1.container(border=True)

        # Trick pour séparer les milliers

        cell1.metric("Nombre de déchets comptés", french_format(nb_total_dechets))

        # 3ème métrique : nombre de relevés
        cell2 = l1_col2.container(border=True)
        cell2.metric("Nombre de ramassages", nb_collec_top)

        ### GRAPHIQUE TOP DECHETS

        # Filtre sur les données au niveau "GROUPE" uniquement
        df_top_dechets = df_top_dechets[
            df_top_dechets["TYPE_REGROUPEMENT"].isin(["GROUPE"])
        ]
        # Grouper par catégorie et ne garder que le top10 déchets en nombre cumulé
        df_top10_dechets = (
            df_top_dechets.groupby("CATEGORIE")
            .agg({"NB_DECHET": "sum"})
            .sort_values(by="NB_DECHET", ascending=False)
            .head(10)
        )

        # Preparation des datas pour l'onglet 3# ajout de la colonne materiau
        df_top10_dechets = df_top10_dechets.merge(
            df_dict_corr_dechet_materiau, on="CATEGORIE", how="left"
        )
        # Preparation de la figure barplot
        df_top10_dechets.reset_index(inplace=True)

        # Création du graphique en barres avec Plotly Express

        fig5 = px.bar(
            df_top10_dechets,
            y="CATEGORIE",
            x="NB_DECHET",
            labels={
                "CATEGORIE": "Dechet",
                "NB_DECHET": "Nombre total de déchets (échelle logarithmique)",
            },
            title="Top 10 des déchets ramassés",
            text="NB_DECHET",
            color="MATERIAU",
            color_discrete_map=colors_map,
            category_orders={"categorie": df_top10_dechets["CATEGORIE"].tolist()},
        )

        fig5.update_layout(
            xaxis_type="log",  # Echelle logarithmique
            showlegend=True,  # Afficher la légende
            height=700,  # Régler la hauteur du graphique
            uniformtext_minsize=10,  # Taille minimale du texte sur les barres
            uniformtext_mode="show",  # Règle d'affichage du texte sur les barres
            yaxis_title=None,  # Cache le titre de l'axe y
            legend=dict(
                yanchor="bottom",
                y=1.01,
                xanchor="right",
                x=0.95,
            ),  # Règle la position de la légende à partir du point d'ancrage choisi
            separators=", ",  # Formatte les nombres en français (séparateur décimale, séparateur milliers)
        )

        fig5.update_traces(
            texttemplate="%{text:,.0f}",  # Template du texte sur les barres
            textposition="inside",  # Position du texte sur les barres
            textfont_color="white",  # Couleur du texte
            textfont_size=14,  # Taille du texte
        )

        fig5.update_yaxes(tickfont=dict(size=14))  # Taille des étiquettes en abcisse

        fig5.update_traces(
            hovertemplate="%{y} : <b>%{x:,.0f} déchets</b>"
        )  # Template de l'infobulle, fait référence à x et y définis dans px.bar.

        # Suppression de la colonne categorie
        del df_top10_dechets["MATERIAU"]

        with st.container(border=True):
            st.plotly_chart(fig5, use_container_width=True)

            st.write("")
            st.caption(
                f"Note : Les chiffres ci-dessous sont calculés sur {nb_collec_top} ramassages \
                    ayant fait l’objet d’un comptage par type de déchets, soit {nb_total_dechets:.0f} déchets."
            )

        with st.container(border=True):

            st.write("**Lieux de ramassage des déchets dans le top 10**")

            # Ajout de la selectbox
            selected_dechet = st.selectbox(
                "Choisir un type de déchet :",
                df_top10_dechets["CATEGORIE"].unique().tolist(),
                index=0,
            )

            # Filtration sur le dechet top 10 sélectionné
            df_map_data = df_top_dechets[df_top_dechets["CATEGORIE"] == selected_dechet]

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

            # création de la carte avec Folium
            map_data = folium.Map(
                location=[(min_lat + max_lat) / 2, (min_lon + max_lon) / 2],
                zoom_start=zoom_admin,
                #  zoom_start=8,
                tiles="OpenStreetMap",
            )

            for index, row in df_map_data.iterrows():

                #    Calcul du rayon du marqueur en log base 2 pour réduire les écarts
                if row["NB_DECHET"] > 1:
                    radius = math.log2(row["NB_DECHET"] / 10) * 2

                else:
                    radius = 0.001

                # Formatter les valeurs avec séparateurs de miliers
                formatted_nb_dechet = locale.format_string(
                    "%.0f", row["NB_DECHET"], grouping=True
                )

                folium.CircleMarker(
                    location=(row["LIEU_COORD_GPS_Y"], row["LIEU_COORD_GPS_X"]),
                    radius=radius,  # Utilisation du rayon ajusté
                    popup=folium.Popup(
                        html=f"""
                                    Quantité : <b>{formatted_nb_dechet} </b><br>
                                    Date : <b>{row['_DATE']}</b><br>
                                    Commune : <b>{row['LIEU_VILLE']}</b><br>
                                    Zone : <b>{row['NOM_ZONE']}</b><br>
                                    """,
                        max_width=150,
                    ),
                    color="#3186cc",
                    fill=True,
                    fill_color="#3186cc",
                ).add_to(map_data)

                # Ajout légende
            legend_html = """
                <div style="
                    position: fixed; 
                    bottom: 50px; 
                    left: 50px; 
                    width: 150px; 
                    height: 90px; 
                    border:2px solid grey; 
                    z-index:9999; 
                    font-size:14px;
                    background-color:white;
                    opacity: 0.85;
                    ">
                    <div style="margin-bottom: 10px;"><b>Légende</b></div>
                    <div>
                        <svg height="60" width="200">
                            <circle cx="20" cy="20" r="10" stroke="#3186cc" stroke-width="1" fill="#3186cc" />
                            <text x="40" y="25" fill="black">Quantité: 100</text>
                            <circle cx="20" cy="50" r="15" stroke="#3186cc" stroke-width="1" fill="#3186cc" />
                            <text x="40" y="55" fill="black">Quantité: 150</text>
                        </svg>
                    </div>
                </div>
            """

            map_data.get_root().html.add_child(folium.Element(legend_html))

            # Affichage de la carte Folium dans Streamlit
            st_folium = st.components.v1.html
            st_folium(
                folium.Figure().add_child(map_data).render(),  # , width=1400
                height=750,
            )

    ###########################################################
    # Onglet 3 : Secteurs et marques
    ###########################################################
    with tab3:

        # Préparation des données
        df_dechet_copy = df_nb_dechet.copy()
        filtered_df = df_other.copy()

        # Étape 1: Création des filtres

        with st.expander("Filtrer par année, type milieu ou type de lieu"):

            # Définir options initiales
            annee_options = [valeur_par_defaut_annee] + sorted(
                df_other["ANNEE"].unique().tolist(), reverse=True
            )
            milieu_options = [valeur_par_defaut_milieu]
            lieu_options = [valeur_par_defaut_lieu]

            # Sélectionner l'année
            annee = st.selectbox(
                "Choisir une année :",
                options=annee_options,
                index=0,  # Default to the first option (valeur_par_defaut_annee)
                key="secteurs_annee",
            )

            # Appliquer le filtre
            if annee != valeur_par_defaut_annee:
                filtered_df = filtered_df[filtered_df["ANNEE"] == annee]

            # Mettre à jour les valeurs des milieux selon l'année choisie
            milieu_options += sorted(filtered_df["TYPE_MILIEU"].unique().tolist())

            # Sélection du milieu
            milieu = st.selectbox(
                "Choisir un type de milieu :",
                options=milieu_options,
                index=0,  # Valeur par défaut : valeur_par_defaut_milieu
                key="secteurs_milieu",
            )

            # Appliquer le filtre par milieu
            if milieu != valeur_par_defaut_milieu:
                filtered_df = filtered_df[filtered_df["TYPE_MILIEU"] == milieu]

            # Mettre à jour les valeurs des lieux selon le milieu choisi
            lieu_options += sorted(filtered_df["TYPE_LIEU"].unique().tolist())

            # Sélectionner ie lieu
            lieu = st.selectbox(
                "Choisir un type de lieu :",
                options=lieu_options,
                index=0,  # VAleur par défaut : valeur_par_defaut_lieu
                key="secteurs_lieu",
            )

            # Appliquer le filtre par lieu
            if lieu != valeur_par_defaut_lieu:
                filtered_df = filtered_df[filtered_df["TYPE_LIEU"] == lieu]

        # Filtration des données pour nb_dechets
        df_init = pd.merge(df_dechet_copy, filtered_df, on="ID_RELEVE", how="inner")

        # Data pour le plot secteur : filtrer par type_regroup et niveau 4

        secteur_df = duckdb.query(
            (
                "SELECT * "
                "FROM df_init "
                "WHERE TYPE_REGROUPEMENT='SECTEUR' AND NIVEAU_CARAC = 4 AND CATEGORIE NOT IN ('VIDE', 'INDÉTERMINÉ');"
            )
        ).to_df()

        # Calcul du nombre de secteurs VIDE et INDETERMINE
        nb_vide_indetermine = duckdb.query(
            (
                "SELECT sum(NB_DECHET)"
                "FROM df_init "
                "WHERE TYPE_REGROUPEMENT='SECTEUR' AND NIVEAU_CARAC = 4 AND CATEGORIE IN ('VIDE', 'INDÉTERMINÉ');"
            )
        ).fetchone()[0]

        top_secteur_df = (
            secteur_df.groupby("CATEGORIE")["NB_DECHET"]
            .sum()
            .sort_values(ascending=True)
        )
        top_secteur_df = top_secteur_df.reset_index()
        top_secteur_df.columns = ["Secteur", "Nombre de déchets"]
        top_secteur_df["Nombre de déchets"] = top_secteur_df[
            "Nombre de déchets"
        ].astype(int)
        # Calcul du pourcentage
        top_secteur_df["Pourcentage"] = (
            top_secteur_df["Nombre de déchets"]
            / top_secteur_df["Nombre de déchets"].sum()
        )

        # Data pour le plot responsabilités
        rep_df = duckdb.query(
            (
                "SELECT * "
                "FROM df_init "
                "WHERE TYPE_REGROUPEMENT='REP' AND NIVEAU_CARAC = 4 AND CATEGORIE NOT IN ('VIDE', 'INDÉTERMINÉ');"
            )
        ).to_df()  # Filtre sur le regroupement REP et le niveau 4, exclusion des vides et indeterminés

        # Calcul du nombre de secteurs VIDE et INDETERMINE
        nb_vide_indetermine_REP = duckdb.query(
            (
                "SELECT sum(NB_DECHET)"
                "FROM df_init "
                "WHERE TYPE_REGROUPEMENT='REP' AND NIVEAU_CARAC = 4 AND CATEGORIE IN ('VIDE', 'INDÉTERMINÉ');"
            )
        ).fetchone()[0]

        top_rep_df = (
            rep_df.groupby("CATEGORIE")["NB_DECHET"].sum().sort_values(ascending=True)
        )
        top_rep_df = top_rep_df.reset_index()
        top_rep_df.columns = ["Responsabilité élargie producteur", "Nombre de déchets"]

        # Data pour le plot marque
        marque_df = duckdb.query(
            (
                "SELECT * "
                "FROM df_init "
                "WHERE TYPE_REGROUPEMENT='MARQUE' AND NIVEAU_CARAC >= 2 AND CATEGORIE NOT IN ('VIDE', 'INDÉTERMINÉ');"
            )
        ).to_df()  # Filtre sur le regroupement REP et le niveau 4, exclusion des vides et indeterminés

        # Calcul du nombre de secteurs VIDE et INDETERMINE
        nb_vide_indetermine_marque = duckdb.query(
            (
                "SELECT sum(NB_DECHET)"
                "FROM df_init "
                "WHERE TYPE_REGROUPEMENT='MARQUE' AND NIVEAU_CARAC = 4 AND CATEGORIE IN ('VIDE', 'INDÉTERMINÉ');"
            )
        ).fetchone()[0]

        top_marque_df = (
            marque_df.groupby("CATEGORIE")["NB_DECHET"]
            .sum()
            .sort_values(ascending=True)
        )
        top_marque_df = top_marque_df.reset_index()
        top_marque_df.columns = ["Marque", "Nombre de déchets"]
        top_marque_df["Nombre de déchets"] = top_marque_df["Nombre de déchets"].astype(
            int
        )

        # Chiffres clés secteurs
        nb_dechet_secteur = secteur_df["NB_DECHET"].sum()
        nb_secteurs = secteur_df["CATEGORIE"].nunique()
        collectes_sect = secteur_df["ID_RELEVE"].nunique()

        # Chiffres clés filières REP
        nb_dechet_rep = rep_df["NB_DECHET"].sum()
        collectes_rep = rep_df["ID_RELEVE"].nunique()
        nb_rep = rep_df["CATEGORIE"].nunique()

        # Chiffres clés marques
        nb_dechet_marque = marque_df["NB_DECHET"].sum()
        nb_marques = marque_df["CATEGORIE"].nunique()
        collectes_marque = marque_df["ID_RELEVE"].nunique()

        ### GRAPHIQUE PAR SECTEUR
        st.write("**Analyse par secteur économique** (relevés de niveau 4 uniquement)")

        # Message d'avertissement si le nombre de collectes est en dessous de 5
        if 0 < collectes_sect < 5:
            st.warning("⚠️ Moins de 5 ramassages dans la base de données")

        if len(secteur_df) != 0:
            # Ligne 1 : 3 cellules avec les indicateurs clés en haut de page
            l1_col1, l1_col2, l1_col3 = st.columns(3)
            # Pour avoir 3 cellules avec bordure, il faut nester un st.container dans chaque colonne (pas d'option bordure dans st.column)
            # 1ère métrique : volume total de déchets collectés
            cell1 = l1_col1.container(border=True)

            # Trick pour séparer les milliers
            cell1.metric("Nombre de déchets comptés", french_format(nb_dechet_secteur))

            # 2ème métrique : poids
            cell2 = l1_col2.container(border=True)
            cell2.metric(
                "Nombre de secteurs concernés",
                french_format(nb_secteurs),
            )

            # 3ème métrique : nombre de collectes
            cell3 = l1_col3.container(border=True)
            cell3.metric(
                "Nombre de ramassages",
                collectes_sect,
            )

            # Ligne 2 : 3 cellules avec les indicateurs clés en bas de page

            fig_secteur = px.bar(
                top_secteur_df.tail(10).sort_values(
                    by="Nombre de déchets", ascending=False
                ),
                x="Nombre de déchets",
                y="Secteur",
                color="Secteur",
                title="Top 10 des secteurs économiques identifiés dans les déchets comptés",
                hover_data=["Pourcentage"],
                labels={
                    "Nombre de déchets": "Nombre total de déchets (échelle logarithmique)",
                },
                orientation="h",
                color_discrete_map=colors_map_secteur,
                text_auto=True,
            )
            # Passage de l'absisse en LOG pour meilleure lecture
            fig_secteur.update_layout(xaxis_type="log")
            fig_secteur.update_traces(
                texttemplate="%{value:,.0f}",
                textposition="inside",
                textfont_size=14,
            )
            fig_secteur.update_layout(
                height=700,
                uniformtext_minsize=10,
                uniformtext_mode="hide",
                showlegend=False,
                yaxis_title=None,
                separators=", ",
            )
            fig_secteur.update_yaxes(
                tickfont=dict(size=14)
            )  # Taille des étiquettes en ordonnée

            # Paramétrage de l'infobulle
            fig_secteur.update_traces(
                hovertemplate="Secteur : <b>%{y}</b><br> Quantité : <b>%{x:,.0f} déchets</b><br> Proportion : <b>%{customdata[0]:.0%}</b>"
            )

            with st.container(border=True):
                st.plotly_chart(fig_secteur, use_container_width=True)

                # Message d'avertissement Nombre de dechets dont le secteur n'a pas été determine
                if nb_vide_indetermine != 0 and nb_vide_indetermine != None:
                    st.caption(
                        "Note : cette analyse exclut "
                        + str(nb_vide_indetermine)
                        + " déchets dont le secteur est indeterminé (fragments ou secteur non identifié)"
                    )
        else:
            st.warning(
                "⚠️ Aucune donnée à afficher par secteur (nombre de ramassages trop faible)"
            )

        ### GRAPHIQUE A BARRE PAR FILIERE REP

        st.write(
            "**Analyse par filière de Responsabilité Élargie du Producteur** (relevés de niveau 4 uniquement)"
        )
        # Message d'avertissement si le nombre de collectes est en dessous de 5
        if 0 < collectes_rep < 5:
            st.warning("⚠️ Moins de 5 ramassages dans la base de données")

        if len(rep_df) != 0:
            l3_col1, l3_col2, l3_col3 = st.columns(3)
            # Pour avoir 3 cellules avec bordure, il faut nester un st.container dans chaque colonne (pas d'option bordure dans st.column)

            # 1ère métrique : nombre de dechets catégorisés repartis par responsabilités
            cell6 = l3_col1.container(border=True)
            cell6.metric(
                "Nombre de déchets comptés",
                french_format(nb_dechet_rep),
            )

            # 2ème métrique : nombre de responsabilités
            cell7 = l3_col2.container(border=True)
            cell7.metric(
                "Nombre de filières REP identifiées",
                french_format(nb_rep),
            )

            cell8 = l3_col3.container(border=True)  # Nb de collectes
            cell8.metric(
                "Nombre de ramassages",
                collectes_rep,
            )

            with st.expander("Qu'est-ce que la Responsabilité Élargie du Producteur ?"):
                st.write(
                    "La Responsabilité Élargie du Producteur (REP) est une obligation qui impose aux entreprises de payer une contribution financière"
                    + " pour la prise en charge de la gestion des déchets issus des produits qu’ils mettent sur le marché selon le principe pollueur-payeur."
                    + " Pour ce faire, elles doivent contribuer financièrement à la collecte, du tri et au recyclage de ces produits, "
                    + "généralement à travers les éco-organismes privés, agréés par l’Etat, comme CITEO pour les emballages. "
                    + "L’État a depuis 1993 progressivement mis en place 25 filières REP, qui regroupent de grandes familles de produits "
                    + "(emballages ménagers, tabac, textile, ameublement, …)."
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
                margin=dict(t=50, l=25, r=25, b=25),
                autosize=True,
                height=500,
                separators=", ",
            )
            figreptree.update_traces(
                textinfo="label+value+percent root",
                texttemplate="<b>%{label}</b><br>%{value:,.0f} déchets<br>%{percentRoot} du total",
                textfont=dict(size=16),
                hovertemplate="%{label}<br>"
                + "Quantité de déchets : <b>%{value:,.0f}</b><br>"
                + "Part des déchets catégorisés : <b>%{percentRoot:.1%}</b>",
            )

            with st.container(border=True):
                st.plotly_chart(figreptree, use_container_width=True)

                # Message d'avertissement Nombre de déchets dont la REP n'a pas été determine
                if nb_vide_indetermine_REP != 0 and nb_vide_indetermine_REP != None:
                    st.caption(
                        "Note : Cette analyse exclut  "
                        + str(french_format(nb_vide_indetermine_REP))
                        + " déchets dont la filière REP n'a pas pu être determinée."
                    )
        else:
            st.warning(
                "⚠️ Aucune donnée à afficher par filière REP (nombre de ramassages trop faible)"
            )

        ### GRAPHIQUE PAR MARQUE

        st.write("**Analyse par marque** (relevés de niveaux 2 à 4)")

        # Message d'avertissement si le nombre de collectes est en dessous de 5
        if 0 < collectes_marque < 5:
            st.warning("⚠️ Moins de 5 ramassages dans la base de données")

        if len(top_marque_df) != 0:

            l2_col1, l2_col2, l2_col3 = st.columns(3)
            cell4 = l2_col1.container(border=True)

            # 1er métrique : nombre de dechets categorises par marques

            cell4.metric(
                "Nombre de déchets comptés",
                french_format(nb_dechet_marque),
            )

            # 2ème métrique : nombre de marques identifiées lors des collectes
            cell5 = l2_col2.container(border=True)
            cell5.metric(
                "Nombre de marques concernées",
                french_format(nb_marques),
            )

            cell12 = l2_col3.container(border=True)  # Nb de collectes
            cell12.metric(
                "Nombre de ramassages",
                collectes_marque,
            )

            # Configuration du graphique à barres
            fig_marque = px.bar(
                top_marque_df.tail(10).sort_values(
                    by="Nombre de déchets", ascending=True
                ),
                x="Nombre de déchets",
                y="Marque",
                title="Top 10 des marques identifiées dans les déchets comptés",
                color_discrete_sequence=["#1951A0"],
                orientation="h",
                text_auto=True,
            )

            fig_marque.update_layout(
                # xaxis_type="log", # Pas besoin d'échelle log ici
                height=700,
                uniformtext_minsize=10,
                uniformtext_mode="hide",
                yaxis_title=None,
                separators=", ",
            )
            # Paramétrage de la taille de police et de l'infobulle
            fig_marque.update_traces(
                textfont_size=14,
                texttemplate="%{value:,.0f}",
                hovertemplate="Marque : <b>%{y}</b><br> Quantité : <b>%{x:,.0f} déchets</b>",
            )
            fig_marque.update_yaxes(
                tickfont=dict(size=14)
            )  # Taille des étiquettes en ordonnée

            with st.container(border=True):
                st.plotly_chart(fig_marque, use_container_width=True)

                # Message d'avertissement pour les déchets non catégorisés
                if (
                    nb_vide_indetermine_marque != None
                    and nb_vide_indetermine_marque != 0
                ):
                    st.caption(
                        "Note : cette analyse exclut  "
                        + str(french_format(nb_vide_indetermine_marque))
                        + " déchets dont la marque n'a pas pu être determinée."
                    )
        else:
            st.warning(
                "⚠️ Aucune donnée à afficher par marque (nombre de ramassages trop faible)"
            )


else:
    st.markdown("## 🚨 Veuillez vous connecter pour accéder à l'onglet 🚨")
