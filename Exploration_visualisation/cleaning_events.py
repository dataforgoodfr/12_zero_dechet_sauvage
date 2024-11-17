import pandas as pd

PATH = "./data/"

# import du fichier d'exportations des events
df_events = pd.read_excel(PATH + "export_events_14032024.xlsx")

# Supprime les événements annulés
df_events = df_events[df_events.ANNULE != 1]

# Convertit le type de la colonne 'DATE' en datetime
df_events.DATE = pd.to_datetime(df_events.DATE, yearfirst=True)

# Remplace les valeurs NaN par 0 dans le NIVEAU DE CARAC
df_events.NIVEAU_CARAC.fillna(0, inplace=True)
# change le type de NIVEAU_CARAC en int
df_events.NIVEAU_CARAC = df_events.NIVEAU_CARAC.astype("int64")

# COORD GPS :
# Supprime les crochets
# split les valeurs par la virgule pour obtenir les coordonnées X et Y
# convertit en float
df_events[["COORD_GPS_X", "COORD_GPS_Y"]] = (
    df_events.COORD_GPS_RDV.str.strip("[]").str.split(",", expand=True).astype(float)
)

# Majuscule sur TYPE_EVENEMENT
df_events.TYPE_EVENEMENT = df_events.TYPE_EVENEMENT.str.capitalize()

# Supprime les colonnes de contact des structures (anonymisation)
# Supprime la colonne COORD_GPS_RDV (inutile)
# Supprime la colonne ANNULE (déjà filtrée)
df_events = df_events.drop(
    [
        "REFERENT_STRUCTURE",
        "TELEPHONE_STRUCTURE",
        "COURRIEL_STRUCTURE",
        "COORD_GPS_RDV",
        "ANNULE",
    ],
    axis=1,
)


df_events.to_csv(PATH + "export_events_cleaned.csv", index=False, encoding="utf-8-sig")
