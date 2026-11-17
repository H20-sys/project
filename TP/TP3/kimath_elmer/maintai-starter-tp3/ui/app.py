"""Interface Streamlit de MaintAI : explorer les données, puis demander une prédiction à l'API.

Lancement (depuis la racine du projet) : python -m streamlit run ui/app.py

La page a deux onglets :
    - « Données » : indicateurs, taux de panne par tranche, nuage de points.
    - « Prédiction » : un formulaire envoie un relevé à l'API, qui répond par une probabilité de panne.

Rappel : Streamlit relance tout le script à chaque clic sur un widget.
"""
import httpx
import pandas as pd
import streamlit as st

from maintai.client import APIError, MaintaiClient
from maintai.config import FEATURES, get_settings

# Titre de l'onglet du navigateur, puis titre de la page
st.set_page_config(page_title="MaintAI", page_icon="🔧")
st.title("MaintAI · prédiction de panne")


@st.cache_data
def charger(path) -> pd.DataFrame:
    """Lit le fichier CSV des relevés et renvoie un tableau pandas.

    Le décorateur @st.cache_data garde le résultat en mémoire :
    le CSV n'est lu qu'une seule fois, pas à chaque clic.
    """
    # Lu une seule fois : Streamlit relance tout le script à chaque clic
    return pd.read_csv(path)


# Barre latérale : l'adresse de l'API et la clé (saisie masquée)
with st.sidebar:
    url = st.text_input("URL de l'API", "http://localhost:8000")
    cle = st.text_input("Clé API", type="password")

onglet_donnees, onglet_prediction = st.tabs(["Données", "Prédiction"])

# Sprint 1 : explorer les données
with onglet_donnees:
    df = charger(get_settings().data_path)
    # TODO TP3 sprint 1 :
    #   1. trois indicateurs côte à côte (st.columns, puis .metric) :
    #      le nombre de relevés, le taux de panne (df.failure.mean()), la température moyenne
    # failure vaut 0 ou 1 : sa moyenne est donc la part de pannes
    c1, c2, c3 = st.columns(3)
    c1.metric("Relevés", len(df))  # le test lit cet indicateur : il doit rester le premier
    c2.metric("Taux de panne", f"{df.failure.mean():.1%}")
    c3.metric("Température moyenne", f"{df.temperature_c.mean():.1f} °C")

    #   2. une liste déroulante (st.selectbox) pour choisir une variable parmi FEATURES
    variable = st.selectbox("Variable", FEATURES)

    #   3. le taux de panne par tranche de cette variable (pd.cut, groupby), en barres (st.bar_chart)
    # pd.cut range chaque valeur dans l'une des 10 tranches de même largeur
    tranches = pd.cut(df[variable], bins=10)
    # moyenne de failure par tranche = taux de panne de la tranche
    taux = df.groupby(tranches, observed=True).failure.mean()
    taux.index = [round(i.mid, 1) for i in taux.index]  # des nombres, pas du texte
    st.bar_chart(taux)

    #   4. un nuage de points température / vibration, coloré par panne (st.scatter_chart)
    # colonne « oui / non » : la couleur se lit mieux que 0 / 1
    points = df.assign(panne=df.failure.map({0: "non", 1: "oui"}))
    st.scatter_chart(points, x="temperature_c", y="vibration_mm_s", color="panne")


# Sprint 2 : demander une prédiction à l'API
with onglet_prediction:
    # Dans un formulaire, les curseurs ne relancent rien : seul le bouton « Prédire » relance
    with st.form("releve"):
        releve = {
            "temperature_c": st.slider("Température (°C)", -40.0, 150.0, 72.0),
            "vibration_mm_s": st.slider("Vibration (mm/s)", 0.0, 50.0, 6.0),
            "load_pct": st.slider("Charge (%)", 0.0, 100.0, 85.0),
            "runtime_hours": st.number_input("Heures de fonctionnement", 0, 100_000, 15000),
        }
        envoye = st.form_submit_button("Prédire")

    # envoye vaut True seulement pendant la relance provoquée par le bouton
    if envoye:
        # TODO TP3 sprint 2 :
        #   1. créer MaintaiClient(url, api_key=cle) et appeler .predict(releve)
        #   2. APIError → st.warning avec le code et le message ; httpx.HTTPError → st.error("API injoignable ...")
        #   3. sinon : st.metric("Probabilité de panne", f"{pct} %"), puis st.error (alerte) ou st.success (normal)
        try:
            client = MaintaiClient(url, api_key=cle or None)  # pas de clé saisie → None
            res = client.predict(releve)
        except APIError as e:
            # L'API a répondu, mais pas 200 (par exemple 401 : clé absente ou invalide)
            st.warning(f"Erreur {e.status_code} : {e.detail}")
        except httpx.HTTPError:
            # Aucune réponse : l'API est arrêtée ou l'adresse est fausse
            st.error("API injoignable : uvicorn est-il lancé ?")
        else:
            # 200 : on affiche le résultat (0.9475 → 95 %)
            pct = round(res["failure_probability"] * 100)
            st.metric("Probabilité de panne", f"{pct} %")
            if res["alert"]:
                st.error(f"ALERTE : au-dessus du seuil {res['threshold']}")
            else:
                st.success("Fonctionnement normal")