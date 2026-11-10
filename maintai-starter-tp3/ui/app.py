"""Interface Streamlit de MaintAI : explorer les données, puis demander une prédiction à l'API.

Lancement (depuis la racine du projet) : python -m streamlit run ui/app.py
"""
import httpx
import pandas as pd
import streamlit as st

from maintai.client import APIError, MaintaiClient
from maintai.config import FEATURES, get_settings

st.set_page_config(page_title="MaintAI", page_icon="🔧")
st.title("MaintAI · prédiction de panne")


@st.cache_data
def charger(path) -> pd.DataFrame:
    # Lu une seule fois : Streamlit relance tout le script à chaque clic
    return pd.read_csv(path)


with st.sidebar:
    url = st.text_input("URL de l'API", "http://localhost:8000")
    cle = st.text_input("Clé API", type="password")

onglet_donnees, onglet_prediction = st.tabs(["Données", "Prédiction"])
client = MaintaiClient(url=url, api_key=cle)
# Sprint 1 : explorer les données
with onglet_donnees:
    df = charger(get_settings().data_path)
    # TODO with onglet_donnees:
    # 1. Trois indicateurs côte à côte
    c1, c2, c3 = st.columns(3)
    c1.metric("Relevés", len(df))
    c2.metric("Taux de panne", f"{df['failure'].mean():.1%}")
    c3.metric("Température moyenne", f"{df['temperature_c'].mean():.1f} °C")

    # 2. Liste déroulante
    variable = st.selectbox("Variable", FEATURES)

    # 3. Taux de panne par tranche, en barres
    tranches = pd.cut(df[variable], bins=10)
    taux = df.groupby(tranches, observed=True)["failure"].mean()
    taux.index = [round(i.mid) for i in taux.index]
    st.bar_chart(taux)

    # 4. Nuage de points température / vibration, coloré par panne
    df_plot = df.copy()
    df_plot["panne"] = df_plot["failure"].map({0: "non", 1: "oui"})
    st.scatter_chart(df_plot, x="temperature_c", y="vibration_mm_s", color="panne")
    st.info("Sprint 1 : les indicateurs et les graphiques viendront ici.")


# Sprint 2 : demander une prédiction à l'API
with onglet_prediction:
    with st.form("releve"):
        releve = {
            "temperature_c": st.slider("Température (°C)", -40.0, 150.0, 72.0),
            "vibration_mm_s": st.slider("Vibration (mm/s)", 0.0, 50.0, 6.0),
            "load_pct": st.slider("Charge (%)", 0.0, 100.0, 85.0),
            "runtime_hours": st.number_input("Heures de fonctionnement", 0, 100_000, 15000),
        }
        envoye = st.form_submit_button("Prédire")

if envoye:
    try:
        resultat = client.predict(releve)
    except APIError as e:
        st.warning(f"Erreur {e.code} : {e.detail}")
    except httpx.HTTPError:
        st.error("API injoignable : uvicorn est-il lancé ?")
    else:
        pct = round(resultat["failure_probability"] * 100)
        st.metric("Probabilité de panne", f"{pct} %")
        if resultat["alert"]:
            st.error(f"ALERTE : au-dessus du seuil ({resultat['threshold']})")
        else:
            st.success("Pas d'alerte : sous le seuil")
        st.info("Sprint 2 : la prédiction s'affichera ici.")
