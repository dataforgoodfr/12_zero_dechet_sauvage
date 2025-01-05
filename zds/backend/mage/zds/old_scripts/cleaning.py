# # Import des données zero déchets sauvages
# #On ne garde que les lignes non nulles et dont le pays est la France


# et rajout des aggrégations géographiques epci et bassin de vie

# Chemin vers le fichier Shapefile

# # Importer le fichier Shapefile


# On va rattacher chacun des points gps à la commune à laquelle il appartient

# Vérifier si les points GPS se trouvent à l'intérieur des géométries
# full_table = gpd.sjoin_nearest(gdf_data_zds,
#                                        gdf_wgs84,
#                                        how="left")
# on a bien une commune par ligne
# On va ne considérer que valide les matchs dont la distance est inférieure à 0.1
# (il s'agit de degré de latitude longitude ce qui n'est pas transposable facilement en mètres)
# il s'agit de 99 lignes soit en dehors de la france soit dans les DOM-TOM que nous n'avons pour le moment pas

# On a 122 lignes pour lesquelles le nom de la ville identifiée
# n'est pas le même que celui initialement complété
# lorsque l'on regarde quelques lignes les communes sont voisines

#


# On va aller rajouter les codes / les libellés des EPCI, departement région
# et bassin de vie 2022
#     "./data/open_data/table-appartenance-geo-communes-23.xlsx",

#     "./data/open_data/Intercommunalite_Metropole_au_01-01-2023.xlsx",


full_table = full_table.merge(
    table_appartenance,
    how="left",
    left_on="INSEE_COM",
    right_on="CODGEO",
)
full_table.drop(columns=["CODGEO"], inplace=True)

# Pour toutes les relevés de niveau 1 on considère que les 0 dans les colonnes NB_DECHET_GROUPE sont en réalité des valeurs nulles
# collectes de niveau 2 : les 0 sont des valeurs nulles sauf pour les 4 types de déchets obligatoires
# collectes de niveau 3 : les 0 sont des valeurs nulles sauf pour les 32 types de déchets obligatoires
columns = data_zds.columns
liste_columns_dechets = [c for c in columns if "NB_DECHET_GROUPE_" in c]

liste_nom_dechets = [
    c.replace("NB_DECHET_GROUPE_", "") for c in columns if "NB_DECHET_GROUPE_" in c
]

#     "BOUTEILLES EN PLASTIQUE ALIMENTAIRE",
#     "CANETTES",
#     "BOUTEILLES EN VERRE",
#     "PNEUS",
#     "APPAREILS MÉNAGERS",
#     "AUTRES DÉCHETS DE LA PÊCHE",
#     "BALLONS DE BAUDRUCHE",
#     "BÂTONS DE SUCETTE",
#     "BATTERIES",
#     "BOÎTES D`APPÂTS",
#     "BOUTEILLES EN PLASTIQUE ALIMENTAIRE",
#     "CARTOUCHES DE CHASSE",
#     "BOUCHONS PLASTIQUE",
#     "BOUTEILLES EN VERRE",
#     "BOUTEILLES ET CONTENANTS NON ALIMENTAIRES",
#     "BRIQUETS",
#     "CHAUSSURES",
#     "CORDAGES ET FICELLES",
#     "COTONS-TIGES",
#     "EMBALLAGES MÉDICAMENTS",
#     "ETIQUETTES DE BOUTEILLE",
#     "FILETS DE PÊCHE",
#     "FILS DE PÊCHE",
#     "GOBELETS EN PLASTIQUE",
#     "JOUETS",
#     "MÉDIAS FILTRANTS",
#     "MOUSSES SYNTHÉTIQUES",
#     "PAILLES EN PLASTIQUE",
#     "PLOMBS ET HAMEÇONS",
#     "PROTECTIONS HYGIÉNIQUES",
#     "SACS PLASTIQUE",
#     "TIRETTES ET CAPSULES",
#     "VAISSELLES EN PLASTIQUE",
#     "VÊTEMENTS",

#     "NB_DECHET_GROUPE_" + c
#     for c in liste_nom_dechets
#     if c not in dechets_oblig_niveau_2
#
# for c in col_dechets_non_oblig_niveau_2:
#     full_table.loc[full_table.NIVEAU_CARAC == 2, c] = full_table.loc[
#     ].apply(lambda x: np.nan if x == 0 else x)


#     "NB_DECHET_GROUPE_" + c
#     for c in liste_nom_dechets
#     if c not in dechets_oblig_niveau_3 and c not in dechets_oblig_niveau_2
#
# for c in col_dechets_non_oblig_niveau_3:
#     full_table.loc[full_table.NIVEAU_CARAC == 3, c] = full_table.loc[
#     ].apply(lambda x: np.nan if x == 0 else x)

# for c in liste_columns_dechets:
#     full_table.loc[full_table.NIVEAU_CARAC.isin([0, 1]), c] = full_table.loc[
#     ].apply(lambda x: np.nan if x == 0 else x)

# La colonne étiquette de bouteille n'existait pas avant la version 2.
# Les 0 doivent donc être remplacés par des Nan
# full_table["NB_DECHET_GROUPE_ETIQUETTES DE BOUTEILLE"] = np.where(
#     & (full_table["VERSION_PROTOCOLE"] == 1),
#     np.nan,

# Les colonnes DCSMM ne sont complétées que pour les relevés de niveau 4.
# Les 0 doivent donc être remplacés par des nan dans toutes ces colonnes.

#     c
#     for c in full_table.columns
#     if "NB_DECHET_DCSMM_" in c and "GENERIQUE" not in c and "SPECIFIQUE" not in c
# for c in liste_columns_dcsmm:
#     full_table[c] = np.where(


# On reformatte la table wide -> long
#     table_reshape,


# def type_regroupement_from_variable(var):
#     if "_GROUPE_" in var:


# def clean_variable_name(var):
#         "NB_DECHET_GROUPE_",
#         "NB_DECHET_DCSMM_GENERIQUE_",
#         "NB_DECHET_DCSMM_SPECIFIQUE_",
#         "NB_DECHET_DCSMM_",
#         "NB_DECHET_MARQUE_",
#         "NB_DECHET_REP_",
#         "NB_DECHET_SECTEUR_",
#     for p in prefix:


# table_dechet["type_regroupement"] = table_dechet["variable"].apply(
#     type_regroupement_from_variable

# On retire toutes les lignes contenant des 0 qui correspondent au type de regroupement MARQUE

# On retire toutes les lignes contenant des 0 pour les type de regroupement SECTEUR et REP si le niveau de protocole n'est pas 4
#     ~(
#         & (table_dechet.type_regroupement.isin(["SECTEUR", "REP"]))
#         & (table_dechet.NIVEAU_CARAC < 4)

table_dechet[["ID_RELEVE", "type_regroupement", "categorie", "nb_dechet"]].to_csv(
    "./data/data_releve_nb_dechet.csv",
    index=False,
)

full_table[[c for c in full_table.columns if "NB_DECHET_" not in c]].to_csv(
    "./data/data_zds_enriched.csv",
    index=False,
)
