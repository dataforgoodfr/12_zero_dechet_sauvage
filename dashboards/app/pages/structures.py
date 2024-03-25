import streamlit as st
import altair as alt
import duckdb
import pandas as pd

st.markdown(
    """# 🔭 Structures
*Quels sont les acteurs impliqués sur mon territoire ?*
"""
)

df_nb_dechet = pd.read_csv(
    (
        "https://github.com/dataforgoodfr/12_zero_dechet_sauvage/raw/2-"
        "nettoyage-et-augmentation-des-donn%C3%A9es/Exploration_visuali"
        "sation/data/data_releve_nb_dechet.csv"
    )
)

df_other = pd.read_csv(
    (
        "https://github.com/dataforgoodfr/12_zero_dechet_sauvage/raw/2-"
        "nettoyage-et-augmentation-des-donn%C3%A9es/Exploration_visuali"
        "sation/data/data_zds_enriched.csv"
    )
)

res_aggCategory_filGroup = duckdb.query(
    (
        "SELECT categorie, sum(nb_dechet) AS total_dechet "
        "FROM df_nb_dechet "
        "WHERE type_regroupement = 'GROUPE' "
        "GROUP BY categorie "
        "HAVING sum(nb_dechet) > 10000 "
        "ORDER BY total_dechet DESC;"
    )
).to_df()

# st.bar_chart(data=res_aggCategory_filGroup, x="categorie", y="total_dechet")

st.altair_chart(
    alt.Chart(res_aggCategory_filGroup)
    .mark_bar()
    .encode(
        x=alt.X("categorie", sort=None, title=""),
        y=alt.Y("total_dechet", title="Total de déchet"),
    ),
    use_container_width=True,
)
