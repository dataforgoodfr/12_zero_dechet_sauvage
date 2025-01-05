from pathlib import Path
import yaml
from yaml.loader import SafeLoader
import streamlit as st
import streamlit_authenticator as stauth

st.markdown(
    """
# Bienvenue 👋
#### Visualiser les collectes de déchets qui ont lieu sur votre territoire !
""",
)

p_cred = Path(".credentials.yml")
with p_cred.open() as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config["credentials"],
    config["cookie"]["name"],
    config["cookie"]["key"],
    config["cookie"]["expiry_days"],
    config["pre-authorized"],
)

try:
    (
        email_of_registered_user,
        username_of_registered_user,
        name_of_registered_user,
    ) = authenticator.register_user(
        pre_authorization=False,
        fields={
            "Form name": "S'enregistrer",
            "Email": "Email",
            "Username": "Identifiant",
            "Password": "Mot de passe",
            "Repeat password": "Répeter le mot de passe",
            "Register": "S'enregistrer",
        },
    )
    if email_of_registered_user:
        with open(".credentials.yml", "w") as file:
            yaml.dump(config, file, default_flow_style=False)
        st.success("Utilisateur enregistré")
except Exception as e:
    st.error(e)
