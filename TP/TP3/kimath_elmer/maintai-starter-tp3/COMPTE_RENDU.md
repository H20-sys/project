# Compte rendu · TP3 : une interface Streamlit pour MaintAI

**Groupe :** …  ·  **Membres :** KIMATH ELMER  ·  **Date :** 10/11/2026

---

## 1. Mise en place (dans `TP/TP3`)

Dernière ligne de `python -m pytest` juste après la mise en place :

```
5 failed, 18 passed
```

Quels fichiers de tests échouent, et quelle erreur donnent-ils ?

`tests/test_client.py` échoue avec `NotImplementedError`, car `predict` n'est pas écrit. `tests/test_ui.py` échoue car la page n'a pas encore les indicateurs ni la prédiction.

## 2. Lancer Streamlit

Lancez d'abord `streamlit run ui/app.py`. Que s'affiche-t-il dans le navigateur ?

```
ModuleNotFoundError: No module named 'maintai'
Traceback:
File "C:\Users\lenovo\Desktop\EMSI\DevAppIntelligent\maintai-starter-tp3\ui\app.py", line 9, in <module>
    from maintai.client import APIError, MaintaiClient
```

Lancez ensuite `python -m streamlit run ui/app.py`. Pourquoi cette commande fonctionne-t-elle et pas la première ?

Avec `streamlit run`, Python cherche d'abord dans le dossier du script (`ui/`), et `maintai/` n'y est pas. Avec `python -m`, Python ajoute le dossier courant (`TP3`) à sa liste de recherche, et `maintai/` est dedans.

## 3. Sprint 1 : l'onglet « Données »

Votre code de l'onglet « Données » :

```python
c1, c2, c3 = st.columns(3)
c1.metric("Relevés", len(df))
c2.metric("Taux de panne", f"{df.failure.mean():.1%}")
c3.metric("Température moyenne", f"{df.temperature_c.mean():.1f} °C")

variable = st.selectbox("Variable", FEATURES)

tranches = pd.cut(df[variable], bins=10)
taux = df.groupby(tranches, observed=True).failure.mean()
taux.index = [round(i.mid, 1) for i in taux.index]
st.bar_chart(taux)

points = df.assign(panne=df.failure.map({0: "non", 1: "oui"}))
st.scatter_chart(points, x="temperature_c", y="vibration_mm_s", color="panne")
```

| Indicateur | Valeur affichée |
|---|---|
| Relevés | 5000 |
| Taux de panne | (recopie ce que ta page affiche) |
| Température moyenne | (recopie ce que ta page affiche) |

Choisissez `vibration_mm_s` dans la liste. Comment évolue le taux de panne quand la vibration augmente ?

(Écris ce que tu vois sur tes barres. En général, le taux de panne monte quand la vibration monte.)

Ajoutez un `print("relance")` en haut de `ui/app.py`, puis déplacez un curseur. Que voyez-vous dans le terminal, et qu'est-ce que cela montre sur le fonctionnement de Streamlit ?

Le terminal affiche « relance » à chaque changement de widget. Cela montre que Streamlit relance tout le script, de la première à la dernière ligne, à chaque interaction.

À quoi sert `@st.cache_data` sur la fonction `charger` ?

Il garde le tableau en mémoire. Le CSV est lu une seule fois, pas à chaque clic, donc la page reste rapide.

## 4. Sprint 2 : l'onglet « Prédiction »

Votre méthode `predict` (`maintai/client.py`) :

```python
def predict(self, reading: dict) -> dict:
    headers = {"X-API-Key": self.api_key} if self.api_key else {}
    r = self.http.post("/v1/predict", json=reading, headers=headers)
    if r.status_code != 200:
        raise APIError(r.status_code, r.json().get("detail"))
    return r.json()
```

Dernière ligne de `python -m pytest` à la fin du sprint 2 :

```
23 passed, 1 warning in 30.02s
```

| Essai | Ce qu'affiche Streamlit |
|---|---|
| valeurs par défaut, bonne clé | Probabilité de panne : 95 % et le message d'alerte rouge |
| valeurs par défaut, fausse clé | Avertissement jaune : « Erreur 401 : ... » |
| API arrêtée (Ctrl+C dans le terminal d'uvicorn) | Erreur rouge : « API injoignable : uvicorn est-il lancé ? » |

Le port 8501 n'est pas dans `MAINTAI_CORS_ORIGINS`, et pourtant la prédiction fonctionne. Pourquoi ?

CORS est une règle du navigateur. Ici, le navigateur n'appelle jamais l'API : c'est le serveur Streamlit (Python, avec httpx) qui l'appelle. Il n'y a donc pas de demande de permission, et la clé reste vérifiée par l'API.

## 5. Questions de compréhension

1. Dans la page web du TP2, qui envoie la requête à l'API ? Et dans Streamlit ?
   Dans le TP2, c'est le navigateur (avec `fetch`). Dans Streamlit, c'est le serveur Streamlit en Python.
2. Pourquoi les tests de `test_client.py` n'ont-ils pas besoin d'uvicorn ?
   Le client reçoit le client de test (`http=client`). La requête va directement à l'application, sans serveur.
3. Page HTML + JavaScript (TP2) ou Streamlit (TP3) : laquelle choisiriez-vous pour une démonstration à un client ? Et pour l'application d'un technicien de maintenance ? Pourquoi ?
   Pour la démo, Streamlit : elle est prête vite et suffit pour montrer les données et la prédiction. Pour le technicien, plutôt la page HTML : on peut la rendre plus simple et plus adaptée à son usage, mais elle demande plus de travail.

## 6. Le rendu Git

- Lien de la pull request : …
- Le tag `tp3` existe sur GitHub : oui / non
- `git status` avant le commit : `.env`, `data/` ou `models/` apparaissaient-ils ? oui / non

## 7. Ce qui reste flou

…