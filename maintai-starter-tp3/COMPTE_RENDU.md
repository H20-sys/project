# Compte rendu · TP3 : une interface Streamlit pour MaintAI

**Groupe :*G2* …  ·  **Membres :*khalid sammar* …  ·  **Date :*10/11/2026* …

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP3.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Mise en place (dans `TP/TP3`)

5 failed, 18 passed
```
Les fichiers tests/test_client.py et tests/test_ui.py échouent.
test_client.py lève AttributeError: 'MaintaiClient' object has no attribute 'predict' (la méthode predict était vide au départ).
test_ui.py lève aussi AttributeError car l'onglet Prédiction n'appelle pas encore l'API.```


…

## 2. Lancer Streamlit

Lancez d'abord `streamlit run ui/app.py`. Que s'affiche-t-il dans le navigateur ?

```::::::::
ModuleNotFoundError: No module named 'maintai'

File "C:\Users\HP\Downloads\TP3\maintai-starter-tp3\ui\app.py", line 9, in <module>
    from maintai.client import APIError, MaintaiClient
```

Lancez ensuite `python -m streamlit run ui/app.py`. Pourquoi cette commande fonctionne-t-elle et pas la première ?
:::::::::::
streamlit run ui/app.py lance le script avec comme dossier de travail ui/ : Python cherche maintai dans ui/, ne le trouve pas, et lève ModuleNotFoundError.

python -m streamlit run ui/app.py ajoute le dossier courant (TP/TP3) à sys.path. Comme maintai/ est dans TP/TP3, Python le trouve et la page s'affiche.

C'est pour ça que le polycopié écrit python -m streamlit run ui/app.py au TP3, et que pip install -e . au TP4 rendra la commande sans python -m possible.
…

## 3. Sprint 1 : l'onglet « Données »

Votre code de l'onglet « Données » (de `c1, c2, c3 = ...` jusqu'au nuage de points) :

```python
with onglet_donnees:
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
    st.scatter_chart(df_plot, x="temperature_c", y="vibration_mm_s", color="panne")```

| Indicateur | Valeur affichée |
|---|---|
| Relevés | 5000
|
| Taux de panne |13.6%
 |
| Température moyenne | 59.8 °C
|

Choisissez `vibration_mm_s` dans la liste. Comment évolue le taux de panne quand la vibration augmente ?
::::::::::::::
Le taux de panne augmente fortement avec la vibration : il est quasi nul pour les faibles vibrations (~0-3 mm/s) et atteint environ 37 % pour les vibrations élevées (~15-18 mm/s). C'est donc la vibration qui est la variable la plus prédictive des pannes, bien plus que la température.
…

Ajoutez un `print("relance")` en haut de `ui/app.py`, puis déplacez un curseur. Que voyez-vous dans le terminal, et qu'est-ce que cela montre sur le fonctionnement de Streamlit ?
:::::::::::
Dans le terminal, on voit relance s'afficher à chaque mouvement du curseur (et en fait à chaque interaction avec un widget). Cela montre que Streamlit relance TOUT le script de haut en bas à chaque interaction. C'est pour ça qu'on utilise @st.cache_data (pour ne pas relire le CSV à chaque fois) et st.form (pour que les curseurs ne relancent rien tant qu'on n'a pas cliqué sur « Prédire »).
…

À quoi sert `@st.cache_data` sur la fonction `charger` ?
:::::::::::
Sans @st.cache_data, la fonction charger serait relancée à chaque clic et relirait le CSV complet (5000 lignes) à chaque fois → page lente. Avec le décorateur, Streamlit mémorise le résultat du premier appel et le réutilise pour les relances suivantes → le CSV n'est lu qu'une seule fois.
…

## 4. Sprint 2 : l'onglet « Prédiction »

Votre méthode `predict` (`maintai/client.py`) :

```python
def predict(self, releve: dict) -> dict:
      headers = {"X-API-Key": self.api_key} if self.api_key else {}
      r = self.http.post("/v1/predict", json=releve, headers=headers)
      if r.status_code != 200:
          raise APIError(r.status_code, r.json().get("detail"))
      return r.json()```

Dernière ligne de `python -m pytest` à la fin du sprint 2 :

```
========================= short test summary info =========================
FAILED tests/test_ui.py::test_ui_shows_the_prediction - AssertionError: assert '59.7 °C' == '95 %'
================ 1 failed, 22 passed, 1 warning in 10.96s =================
================== 23 passed, 1 warning in 15.21s ==================

Avec l'API lancée (`uvicorn maintai.api.main:app --reload --env-file .env`) :

| Essai | Ce qu'affiche Streamlit |
|---|---|
| valeurs par défaut, bonne clé | « Probabilité de panne : 95 % » et message rouge « ALERTE : au-dessus du seuil (0.3) »|
| valeurs par défaut, fausse clé | Message jaune « Erreur 401 : Clé API absente ou invalide »|
| API arrêtée (Ctrl+C dans le terminal d'uvicorn) | Message rouge « API injoignable : uvicorn est-il lancé ? »|

Le port 8501 n'est pas dans `MAINTAI_CORS_ORIGINS`, et pourtant la prédiction fonctionne. Pourquoi ?
:::::::::::::::::
CORS est une règle appliquée par le navigateur, pas par le serveur. Au TP2, c'est le navigateur (page sur le port 5500) qui faisait le fetch vers l'API → il vérifiait CORS et bloquait. Au TP3, c'est Python (le serveur Streamlit sur le port 8501) qui fait la requête vers l'API : il n'y a pas de navigateur dans la boucle pour faire la vérification CORS. Le port 8501 n'est donc pas dans MAINTAI_CORS_ORIGINS, mais ça marche quand même. La clé API, elle, reste bien vérifiée par l'API.



## 5. Questions de compréhension

1. Dans la page web du TP2, qui envoie la requête à l'API ? Et dans Streamlit ?
TP2 (page web) : c'est le navigateur qui envoie la requête HTTP à l'API (via fetch), car le JavaScript s'exécute dans le navigateur.

TP3 (Streamlit) : c'est le serveur Python de Streamlit qui envoie la requête à l'API (via MaintaiClient, qui utilise httpx). Le navigateur ne fait qu'afficher la page générée par Streamlit.
   …
2. Pourquoi les tests de `test_client.py` n'ont-ils pas besoin d'uvicorn ?
Parce que les tests injectent un faux client HTTP (starlette.testclient.TestClient) directement dans MaintaiClient(http=client). Ce client de test parle directement à l'application FastAPI en mémoire, sans passer par un serveur uvicorn, sans socket, sans réseau. C'est plus rapide et ça ne dépend pas d'un port. C'est pour ça que MaintaiClient doit utiliser self.http.post(...) et non httpx.post(...).
   …
3. Page HTML + JavaScript (TP2) ou Streamlit (TP3) : laquelle choisiriez-vous pour une démonstration à un client ? Et pour l'application d'un technicien de maintenance ? Pourquoi ?
::::::::::::
Pour une démonstration à un client : Streamlit. Il permet de faire une démo visuelle (indicateurs, graphiques, formulaire) très rapidement, sans écrire de HTML/CSS/JS. Le client voit immédiatement les données et peut jouer avec les curseurs.

Pour l'application d'un technicien de maintenance : plutôt Streamlit aussi, tant que l'application reste simple. Si elle devient un vrai outil métier (plusieurs pages, authentification, intégration dans un SI existant), une page web dédiée (HTML/JS + framework) sera plus adaptée (contrôle total, performances, intégration).

Le vrai critère est : rapidité de mise en œuvre vs. contrôle total du rendu.
   …

## 6. Le rendu Git

- Lien de la pull request : …
- Le tag `tp3` existe sur GitHub : oui / non
- `git status` avant le commit : `.env`, `data/` ou `models/` apparaissaient-ils ? oui / non

## 7. Ce qui reste flou

…
