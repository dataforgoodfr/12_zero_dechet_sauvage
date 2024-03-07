
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point


# Import des données zero déchets sauvages
data_zds = pd.read_excel('./data/data_zds_20231218_CorrigéWOTO.xlsx')
#On ne garde que les lignes non nulles et dont le pays est la France
data_zds = data_zds[~data_zds['ID_RELEVE'].isna()]
data_zds = data_zds[data_zds.LIEU_PAYS=='France']
#On supprime la colonne protoxyde qui est vide est non expliquée
data_zds.drop(columns=['protoxyde'], inplace=True)


##### A) Complétion des champs géographique 
        # et rajout des aggrégations géographiques epci et bassin de vie

# Chemin vers le fichier Shapefile
shapefile_path = "./data/open_data/commune.shp"

# Importer le fichier Shapefile
gdf = gpd.read_file(shapefile_path)

# Convertir en format WGS 84 (EPSG:4326)
gdf_wgs84 = gdf.to_crs(epsg=4326)



# On va rattacher chacun des points gps à la commune à laquelle il appartient
geometry = [Point(xy) for xy in zip(data_zds.LIEU_COORD_GPS_X, data_zds.LIEU_COORD_GPS_Y)]
gdf_data_zds = gpd.GeoDataFrame(data_zds, geometry=geometry, crs= gdf_wgs84.crs)

# Vérifier si les points GPS se trouvent à l'intérieur des géométries
full_table = gpd.sjoin_nearest(gdf_data_zds, 
                                       gdf_wgs84, 
                                       how="left")
full_table['ID'].isna().sum()
# on a bien une commune par ligne

# On a 194 lignes pour lesquelles le nom de la ville identifiée 
# n'est pas le même que celui initialement complété
# lorsque l'on regarde quelques lignes les communes sont voisines
verif = full_table[full_table.LIEU_VILLE != full_table.NOM]
villes_diff = verif[['LIEU_PAYS','LIEU_VILLE', 'NOM']]

columns_to_keep = list(data_zds.columns) + ['NOM', 'INSEE_COM']

full_table = full_table[columns_to_keep]
full_table.rename(columns = {'NOM':'commune'}, inplace = True)



# On va aller rajouter les codes / les libellés des EPCI, departement région 
# et bassin de vie 2022
table_appartenance = pd.read_excel('./data/open_data/table-appartenance-geo-communes-23.xlsx',
                                   sheet_name = 'COM',
                                   skiprows = 5)
table_appartenance = table_appartenance[['CODGEO', 'DEP', 'REG', 'EPCI', 
                                         'NATURE_EPCI', 'BV2022']]
epci = pd.read_excel('./data/open_data/Intercommunalite_Metropole_au_01-01-2023.xlsx',
                     sheet_name = 'EPCI',
                     skiprows = 5)
table_appartenance = table_appartenance.merge(epci[['EPCI', 'LIBEPCI']], 
                                                    how = 'left',
                                                    on = 'EPCI')
dep = pd.read_csv('./data/open_data/v_departement_2023.csv')
dep.rename(columns={'LIBELLE':'DEPARTEMENT'}, inplace = True)
table_appartenance = table_appartenance.merge(dep[['DEP', 'DEPARTEMENT']],
                                              how = 'left',
                                              on = 'DEP')
region = pd.read_csv('./data/open_data/v_region_2023.csv')
region.rename(columns={'LIBELLE':'REGION'}, inplace = True)
table_appartenance = table_appartenance.merge(region[['REG', 'REGION']],
                                              how = 'left',
                                              on = 'REG')
bassin_vie = pd.read_excel('./data/open_data/BV2022_au_01-01-2023.xlsx',
                         sheet_name = 'BV2022',
                         skiprows = 5)
bassin_vie.rename(columns={'LIBBV2022':'BASSIN_DE_VIE'}, inplace = True)
table_appartenance = table_appartenance.merge(bassin_vie[['BV2022', 'BASSIN_DE_VIE']],
                                              how = 'left',
                                              on = 'BV2022')

full_table = full_table.merge(table_appartenance,
                              how = 'left',
                              left_on = 'INSEE_COM',
                              right_on = 'CODGEO')
full_table.drop(columns=['CODGEO'], inplace=True)

##### B) Suppression des 0 non surs
        # Pour toutes les relevés de niveau 1 on considère que les 0 dans les colonnes NB_DECHET_GROUPE sont en réalité des valeurs nulles
        # collectes de niveau 2 : les 0 sont des valeurs nulles sauf pour les 4 types de déchets obligatoires
        # collectes de niveau 3 : les 0 sont des valeurs nulles sauf pour les 32 types de déchets obligatoires
columns = data_zds.columns
liste_columns_dechets = [c for c in columns if 'NB_DECHET_GROUPE_' in c]

liste_nom_dechets = [c.replace('NB_DECHET_GROUPE_', '') for c in columns if 'NB_DECHET_GROUPE_' in c]

dechets_oblig_niveau_2 = ['BOUTEILLES EN PLASTIQUE ALIMENTAIRE', 
                          'CANETTES', 
                          'BOUTEILLES EN VERRE', 
                          'PNEUS']
dechets_oblig_niveau_3 = ['APPAREILS MÉNAGERS', 'AUTRES DÉCHETS DE LA PÊCHE', 'BALLONS DE BAUDRUCHE', 'BÂTONS DE SUCETTE', 
                          'BATTERIES', 'BOÎTES D’APPÂTS', 'BOUTEILLES EN PLASTIQUE ALIMENTAIRE', 'CARTOUCHES DE CHASSE',
                          'BOUCHONS PLASTIQUE', 'BOUTEILLES EN VERRE', 'BOUTEILLES ET CONTENANTS NON ALIMENTAIRES', 'BRIQUETS', 'CHAUSSURES', 
                          'CORDAGES ET FICELLES', 'COTONS-TIGES', 'EMBALLAGES MÉDICAMENTS', 'ETIQUETTES DE BOUTEILLE',
                          'FILETS DE PÊCHE', 'FILS DE PÊCHE', 'GOBELETS EN PLASTIQUE', 'JOUETS', 'MÉDIAS FILTRANTS',
                          'MOUSSES SYNTHÉTIQUES', 'PAILLES EN PLASTIQUE', 'PLOMBS ET HAMEÇONS', 'PROTECTIONS HYGIÉNIQUES',
                          'SACS PLASTIQUE', 'TIRETTES ET CAPSULES', 'VAISSELLES EN PLASTIQUE', 'VÊTEMENTS']

col_dechets_non_oblig_niveau_2 = ['NB_DECHET_GROUPE_'+ c for c in liste_nom_dechets if c not in dechets_oblig_niveau_2]

for c in col_dechets_non_oblig_niveau_2:
    full_table.loc[full_table.NIVEAU_CARAC==2, c] = full_table.loc[full_table.NIVEAU_CARAC==2, c].apply(lambda x: None if x==0 else x)
print(full_table[full_table.NIVEAU_CARAC==2][col_dechets_non_oblig_niveau_2].isna().sum())


col_dechets_non_oblig_niveau_3 = ['NB_DECHET_GROUPE_'+ c for c in liste_nom_dechets if c not in dechets_oblig_niveau_3]

for c in col_dechets_non_oblig_niveau_3:
    full_table.loc[full_table.NIVEAU_CARAC==3, c] = full_table.loc[full_table.NIVEAU_CARAC==3, c].apply(lambda x: None if x==0 else x)
print(full_table[full_table.NIVEAU_CARAC==3][col_dechets_non_oblig_niveau_3].isna().sum())


b = full_table[full_table.NIVEAU_CARAC==1][liste_columns_dechets].isna().sum()
for c in liste_columns_dechets:
    full_table.loc[full_table.NIVEAU_CARAC==1, c] = full_table.loc[full_table.NIVEAU_CARAC==1, c].apply(lambda x: None if x==0 else x)
print(full_table[full_table.NIVEAU_CARAC==1][liste_columns_dechets].isna().sum())



full_table.to_excel('./data/data_zds_enriched.xlsx', index=False)