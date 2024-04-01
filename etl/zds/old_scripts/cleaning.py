import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
import numpy as np


# # Import des données zero déchets sauvages
# data_zds = pd.read_excel('./data/data_zds_20240315_Corrigé.xlsx')
# #On ne garde que les lignes non nulles et dont le pays est la France
# data_zds = data_zds[~data_zds['ID_RELEVE'].isna()]
# data_zds = data_zds[(data_zds.LIEU_PAYS=='France') | (data_zds.LIEU_PAYS.isna())]


##### A) Complétion des champs géographique
# et rajout des aggrégations géographiques epci et bassin de vie

# Chemin vers le fichier Shapefile
# shapefile_path = "./data/open_data/COMMUNE.shp"

# # Importer le fichier Shapefile
# gdf = gpd.read_file(shapefile_path)

# # Convertir en format WGS 84 (EPSG:4326)
# gdf_wgs84 = gdf.to_crs(epsg=4326)


# On va rattacher chacun des points gps à la commune à laquelle il appartient
# geometry = [Point(xy) for xy in zip(data_zds.LIEU_COORD_GPS_X, data_zds.LIEU_COORD_GPS_Y)]
# gdf_data_zds = gpd.GeoDataFrame(data_zds, geometry=geometry, crs= gdf_wgs84.crs)

# Vérifier si les points GPS se trouvent à l'intérieur des géométries
# full_table = gpd.sjoin_nearest(gdf_data_zds,
#                                        gdf_wgs84,
#                                        distance_col= 'distance',
#                                        how="left")
# full_table['ID'].isna().sum()
# on a bien une commune par ligne
# On va ne considérer que valide les matchs dont la distance est inférieure à 0.1
# (il s'agit de degré de latitude longitude ce qui n'est pas transposable facilement en mètres)
# il s'agit de 99 lignes soit en dehors de la france soit dans les DOM-TOM que nous n'avons pour le moment pas
# full_table = full_table[full_table['distance']<0.1]

# On a 122 lignes pour lesquelles le nom de la ville identifiée
# n'est pas le même que celui initialement complété
# lorsque l'on regarde quelques lignes les communes sont voisines
# verif = full_table[(full_table.LIEU_VILLE != full_table.NOM) & (~full_table.LIEU_VILLE.isna())]
# villes_diff = verif[['ID_RELEVE', 'LIEU_PAYS','LIEU_VILLE', 'NOM', 'LIEU_COORD_GPS_X', 'LIEU_COORD_GPS_Y']]
# villes_diff.to_excel('./data/verif_villes.xlsx', index = False)

columns_to_keep = list(data_zds.columns) + ["NOM", "INSEE_COM"]

full_table = full_table[columns_to_keep]
full_table.rename(columns={"NOM": "commune"}, inplace=True)


# On va aller rajouter les codes / les libellés des EPCI, departement région
# et bassin de vie 2022
table_appartenance = pd.read_excel(
    "./data/open_data/table-appartenance-geo-communes-23.xlsx",
    sheet_name="COM",
    skiprows=5,
)
table_appartenance = table_appartenance[
    ["CODGEO", "DEP", "REG", "EPCI", "NATURE_EPCI", "BV2022"]
]
epci = pd.read_excel(
    "./data/open_data/Intercommunalite_Metropole_au_01-01-2023.xlsx",
    sheet_name="EPCI",
    skiprows=5,
)
table_appartenance = table_appartenance.merge(
    epci[["EPCI", "LIBEPCI"]], how="left", on="EPCI"
)
dep = pd.read_csv("./data/open_data/v_departement_2023.csv")
dep.rename(columns={"LIBELLE": "DEPARTEMENT"}, inplace=True)
table_appartenance = table_appartenance.merge(
    dep[["DEP", "DEPARTEMENT"]], how="left", on="DEP"
)
region = pd.read_csv("./data/open_data/v_region_2023.csv")
region.rename(columns={"LIBELLE": "REGION"}, inplace=True)
table_appartenance = table_appartenance.merge(
    region[["REG", "REGION"]], how="left", on="REG"
)
bassin_vie = pd.read_excel(
    "./data/open_data/BV2022_au_01-01-2023.xlsx", sheet_name="BV2022", skiprows=5
)
bassin_vie.rename(columns={"LIBBV2022": "BASSIN_DE_VIE"}, inplace=True)
table_appartenance = table_appartenance.merge(
    bassin_vie[["BV2022", "BASSIN_DE_VIE"]], how="left", on="BV2022"
)

full_table = full_table.merge(
    table_appartenance, how="left", left_on="INSEE_COM", right_on="CODGEO"
)
full_table.drop(columns=["CODGEO"], inplace=True)

##### B) Suppression des 0 non surs
# Pour toutes les relevés de niveau 1 on considère que les 0 dans les colonnes NB_DECHET_GROUPE sont en réalité des valeurs nulles
# collectes de niveau 2 : les 0 sont des valeurs nulles sauf pour les 4 types de déchets obligatoires
# collectes de niveau 3 : les 0 sont des valeurs nulles sauf pour les 32 types de déchets obligatoires
columns = data_zds.columns
liste_columns_dechets = [c for c in columns if "NB_DECHET_GROUPE_" in c]

liste_nom_dechets = [
    c.replace("NB_DECHET_GROUPE_", "") for c in columns if "NB_DECHET_GROUPE_" in c
]

dechets_oblig_niveau_2 = [
    "BOUTEILLES EN PLASTIQUE ALIMENTAIRE",
    "CANETTES",
    "BOUTEILLES EN VERRE",
    "PNEUS",
]
dechets_oblig_niveau_3 = [
    "APPAREILS MÉNAGERS",
    "AUTRES DÉCHETS DE LA PÊCHE",
    "BALLONS DE BAUDRUCHE",
    "BÂTONS DE SUCETTE",
    "BATTERIES",
    "BOÎTES D’APPÂTS",
    "BOUTEILLES EN PLASTIQUE ALIMENTAIRE",
    "CARTOUCHES DE CHASSE",
    "BOUCHONS PLASTIQUE",
    "BOUTEILLES EN VERRE",
    "BOUTEILLES ET CONTENANTS NON ALIMENTAIRES",
    "BRIQUETS",
    "CHAUSSURES",
    "CORDAGES ET FICELLES",
    "COTONS-TIGES",
    "EMBALLAGES MÉDICAMENTS",
    "ETIQUETTES DE BOUTEILLE",
    "FILETS DE PÊCHE",
    "FILS DE PÊCHE",
    "GOBELETS EN PLASTIQUE",
    "JOUETS",
    "MÉDIAS FILTRANTS",
    "MOUSSES SYNTHÉTIQUES",
    "PAILLES EN PLASTIQUE",
    "PLOMBS ET HAMEÇONS",
    "PROTECTIONS HYGIÉNIQUES",
    "SACS PLASTIQUE",
    "TIRETTES ET CAPSULES",
    "VAISSELLES EN PLASTIQUE",
    "VÊTEMENTS",
]

col_dechets_non_oblig_niveau_2 = [
    "NB_DECHET_GROUPE_" + c
    for c in liste_nom_dechets
    if c not in dechets_oblig_niveau_2
]

for c in col_dechets_non_oblig_niveau_2:
    full_table.loc[full_table.NIVEAU_CARAC == 2, c] = full_table.loc[
        full_table.NIVEAU_CARAC == 2, c
    ].apply(lambda x: np.nan if x == 0 else x)


col_dechets_non_oblig_niveau_3 = [
    "NB_DECHET_GROUPE_" + c
    for c in liste_nom_dechets
    if c not in dechets_oblig_niveau_3 and c not in dechets_oblig_niveau_2
]

for c in col_dechets_non_oblig_niveau_3:
    full_table.loc[full_table.NIVEAU_CARAC == 3, c] = full_table.loc[
        full_table.NIVEAU_CARAC == 3, c
    ].apply(lambda x: np.nan if x == 0 else x)

for c in liste_columns_dechets:
    full_table.loc[full_table.NIVEAU_CARAC.isin([0, 1]), c] = full_table.loc[
        full_table.NIVEAU_CARAC.isin([0, 1]), c
    ].apply(lambda x: np.nan if x == 0 else x)

# La colonne étiquette de bouteille n'existait pas avant la version 2.
# Les 0 doivent donc être remplacés par des Nan
full_table["NB_DECHET_GROUPE_ETIQUETTES DE BOUTEILLE"] = np.where(
    (full_table["NB_DECHET_GROUPE_ETIQUETTES DE BOUTEILLE"] == 0)
    & (full_table["VERSION_PROTOCOLE"] == 1),
    np.nan,
    full_table["NB_DECHET_GROUPE_ETIQUETTES DE BOUTEILLE"],
)

# Les colonnes DCSMM ne sont complétées que pour les relevés de niveau 4.
# Les 0 doivent donc être remplacés par des nan dans toutes ces colonnes.

liste_columns_dcsmm = [
    c
    for c in full_table.columns
    if "NB_DECHET_DCSMM_" in c and "GENERIQUE" not in c and "SPECIFIQUE" not in c
]
for c in liste_columns_dcsmm:
    full_table[c] = np.where(
        (full_table[c] == 0) & (full_table["NIVEAU_CARAC"] < 4), np.nan, full_table[c]
    )


# On reformatte la table wide -> long
table_reshape = full_table[
    ["ID_RELEVE", "NIVEAU_CARAC"] + [c for c in full_table.columns if "NB_DECHET_" in c]
]
table_dechet = pd.melt(
    table_reshape,
    id_vars=["ID_RELEVE", "NIVEAU_CARAC"],
    value_vars=[c for c in full_table.columns if "NB_DECHET_" in c],
    value_name="nb_dechet",
)
table_dechet = table_dechet[~table_dechet.nb_dechet.isna()]


def type_regroupement_from_variable(var):
    if "_GROUPE_" in var:
        return "GROUPE"
    elif "_MARQUE_" in var:
        return "MARQUE"
    elif "_DCSMM_GENERIQUE_" in var:
        return "DCSMM_GENERIQUE"
    elif "_DCSMM_SPECIFIQUE_" in var:
        return "DCSMM_SPECIFIQUE"
    elif "_DCSMM_" in var:
        return "DCSMM"
    elif "_SECTEUR_" in var:
        return "SECTEUR"
    elif "_REP_" in var:
        return "REP"


def clean_variable_name(var):
    prefix = [
        "NB_DECHET_GROUPE_",
        "NB_DECHET_DCSMM_GENERIQUE_",
        "NB_DECHET_DCSMM_SPECIFIQUE_",
        "NB_DECHET_DCSMM_",
        "NB_DECHET_MARQUE_",
        "NB_DECHET_REP_",
        "NB_DECHET_SECTEUR_",
    ]
    for p in prefix:
        var = var.replace(p, "")
    return var


table_dechet["type_regroupement"] = table_dechet["variable"].apply(
    type_regroupement_from_variable
)
table_dechet["categorie"] = table_dechet["variable"].apply(clean_variable_name)

# On retire toutes les lignes contenant des 0 qui correspondent au type de regroupement MARQUE
table_dechet = table_dechet.loc[
    (table_dechet.type_regroupement != "MARQUE") | (table_dechet.nb_dechet != 0)
]
# On retire toutes les lignes contenant des 0 pour les type de regroupement SECTEUR et REP si le niveau de protocole n'est pas 4
table_dechet = table_dechet.loc[
    ~(
        (table_dechet.nb_dechet == 0)
        & (table_dechet.type_regroupement.isin(["SECTEUR", "REP"]))
        & (table_dechet.NIVEAU_CARAC < 4)
    )
]

table_dechet[["ID_RELEVE", "type_regroupement", "categorie", "nb_dechet"]].to_csv(
    "./data/data_releve_nb_dechet.csv", index=False
)

full_table[[c for c in full_table.columns if "NB_DECHET_" not in c]].to_csv(
    "./data/data_zds_enriched.csv", index=False
)
