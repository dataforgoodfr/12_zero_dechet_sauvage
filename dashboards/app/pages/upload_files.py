import streamlit as st
from st_pages import Page, show_pages
from streamlit.runtime.uploaded_file_manager import UploadedFile
import os

# Configuration de la page
st.set_page_config(
    layout="wide", page_title="Dashboard Zéro Déchet Sauvage : onglet Structures"
)

expected_files = ["COLLECTES.csv", "STRUCTURES.csv", "SPOTS.csv"]

st.markdown(
    f"""# 📁 Dépôt de fichiers
*Déposez un fichier et lancer son traitement !*

**Veuillez respecter les noms de fichiers suivant** :
- {expected_files[0]}
- {expected_files[1]}
- {expected_files[2]}
"""
)

uploaded_file = st.file_uploader("Déposez votre fichier", type="csv")

if (isinstance(uploaded_file, UploadedFile)) and ("csv" in uploaded_file.name):
    if st.button("OK"):
        if uploaded_file.name in expected_files:
            with open(f"/data/{uploaded_file.name}", "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success(f"Le fichier {uploaded_file.name} déposé !", icon="🚀")
        else:
            st.error("Veuillez respecter le nom de fichier !", icon="🚨")

else:
    pass
