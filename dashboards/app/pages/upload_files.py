import streamlit as st
from st_pages import Page, show_pages
from streamlit.runtime.uploaded_file_manager import UploadedFile

# Configuration de la page
st.set_page_config(
    layout="wide", page_title="Dashboard Zéro Déchet Sauvage : onglet Structures"
)

st.markdown(
    """# 📁 Dépôt de fichiers
*Déposez un fichier et lancer son traitement !*

**Veuillez respecter les noms de fichiers suivant** :
- COLLECTES.csv
- STRUCTURES.csv
- SPOTS.csv
"""
)

uploaded_file = st.file_uploader("Déposez votre fichier", type="csv")

if (isinstance(uploaded_file, UploadedFile)) and ("csv" in uploaded_file.name):
    if st.button("OK"):
        st.success(f"Le fichier {uploaded_file.name} déposé !", icon="🚀")

else:
    pass
