# Compte rendu · TP1 : une API de prédiction pour MaintAI

**Groupe :** Grp 2  ·  **Membres :** Soufiane Jaouhari, Hiba Chefchaouni Moussaoui, Khalid Sammar, Kimath Elmer  ·  **Date :** 27/10/2026

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP1.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Mise en place

Dernière ligne de `python -m pytest`, juste après la mise en place (rien n'est encore écrit) :

```
=================== 3 failed, 10 passed, 1 warning in 3.40s ===================
```

Dans `tests/test_api.py`, 4 tests sur 7 passent déjà alors que rien n'est écrit. Lesquels ? Pour les deux tests qui attendent un code 422, expliquez pourquoi ils passent « pour une mauvaise raison » (indice : regardez `extra="forbid"` dans `schemas.py`).

Les 4 tests qui passent : `test_health`, `test_out_of_range_value_is_rejected`, `test_missing_field_is_rejected` et `test_openapi_documents_predict`. Les deux tests 422 passent pour une mauvaise raison. Le schéma `SensorReading` ne déclare aucun champ, et `extra="forbid"` refuse tout champ inconnu : **tous** les champs du JSON sont donc inconnus, et **tout** relevé est refusé avec 422 (« Extra inputs are not permitted »), même un relevé valide. Le 422 de la température de 500 °C ne vient pas d'une borne `le=150`, et celui du relevé sans `load_pct` ne vient pas de la détection du champ manquant : les autres champs sont simplement refusés comme inconnus. Ces tests passeraient même avec de mauvaises bornes. `test_health` et `test_openapi_documents_predict` ne dépendent ni du schéma ni du corps de `predict()`.

## 2. Le schéma d'entrée (`maintai/api/schemas.py`)

| Variable | Type | Minimum (`ge`) | Maximum (`le`) | Justification physique (pas le min / max des données) |
|---|---|---|---|---|
| `temperature_c` | float | -40 | 150 | -40 °C : atelier non chauffé ou site extérieur en hiver. Au-delà de 150 °C, l'isolation des bobinages (classe F, 155 °C) est détruite : la valeur vient d'un capteur en panne. |
| `vibration_mm_s` | float | 0 | 100 | Une vibration efficace (RMS) ne peut pas être négative. L'ISO 10816 juge une machine dangereuse dès 7 à 11 mm/s, et les capteurs industriels mesurent jusqu'à 50 ou 100 mm/s : une machine très abîmée est acceptée, et déclenche une alerte. |
| `load_pct` | float | 0 | 150 | 0 % : machine à vide. Une surcharge temporaire au-dessus de 100 % est possible, et c'est un cas à risque qu'il ne faut pas refuser. Au-delà de 150 %, la protection thermique coupe le moteur. |
| `runtime_hours` | float | 0 | 300 000 | Un compteur cumulé est positif. 300 000 h font environ 34 ans en 24 h/24, au-delà de la durée de vie d'un moteur industriel. Type `float` : 15 000,5 h doit être accepté. |

Après avoir écrit `schemas.py` seul, que donne `python -m pytest`, et quel est le message d'erreur des tests qui échouent ? Pourquoi est-ce un bon signe ?

```
FAILED tests/test_api.py::test_predict_returns_probability - NotImplementedError
FAILED tests/test_api.py::test_high_risk_reading_raises_alert - NotImplemente...
FAILED tests/test_api.py::test_503_when_model_missing - NotImplementedError
======================== 3 failed, 10 passed in 4.23s =========================
```

Toujours 3 échecs, mais l'erreur n'est plus un 422 : c'est `NotImplementedError`, levée dans `predict()`. C'est un bon signe : les relevés valides passent maintenant la validation et arrivent jusqu'à la fonction. Il ne manque plus que son corps. Et les deux tests 422 passent désormais pour la bonne raison : la borne `le=150` et le champ obligatoire `load_pct`.

## 3. La fonction `predict()` (`maintai/api/main.py`)

Votre code :

```python
    predictor = state.get("predictor")
    if predictor is None:
        # Le service est indisponible (pas de modèle), ce n'est pas un bug du code : 503, pas 500
        raise HTTPException(
            status_code=503,
            detail="Modèle non chargé : lancez python -m maintai.train, puis redémarrez l'API.",
        )
    return PredictionOut(**predictor.predict(reading.model_dump()))
```

Pourquoi répondre **503** et pas 500 quand le modèle manque ?

Le code 500 signifie « bug dans le code du serveur ». Ici, le code est correct : c'est une ressource, le modèle, qui manque. Le code 503 (service indisponible) le dit précisément. Le client sait qu'il peut réessayer plus tard, l'opérateur lit dans `detail` ce qu'il doit faire, et la supervision ne confond pas une panne de configuration avec un bug.

Pourquoi le modèle est-il chargé **une seule fois**, au démarrage, et pas à chaque requête ?

Charger le modèle (`joblib.load`) lit un fichier sur le disque et reconstruit tout le pipeline : c'est lent par rapport à une prédiction. Le refaire à chaque requête ajouterait ce temps à chaque réponse et des lectures disque inutiles. Chargé une fois dans `state`, le modèle reste en mémoire : chaque requête ne fait que la prédiction, toutes utilisent la même version du modèle, et un modèle absent est repéré dès le démarrage (`/health` renvoie `"model_loaded": false`).

## 4. Les tests

Dernière ligne de `python -m pytest` à la fin du TP :

```
======================== 13 passed, 1 warning in 2.52s ========================
```

## 5. L'API en marche

Après `python -m maintai.dataset` et `python -m maintai.train`, lancez `uvicorn maintai.api.main:app --reload`, puis envoyez ces requêtes depuis `/docs` (ou avec `curl.exe`).

| Requête | Code obtenu | Réponse (le corps JSON) |
|---|---|---|
| `GET /health` | 200 | `{"status":"ok","model_loaded":true}` |
| `POST /v1/predict` avec `{"temperature_c": 72.5, "vibration_mm_s": 6.1, "load_pct": 85, "runtime_hours": 15000}` | 200 | `{"failure_probability":0.9553,"alert":true,"threshold":0.3,"model_version":"2026-10-27T17:38:23Z"}` |
| `POST /v1/predict` avec une température de 500 | 422 | `{"detail":[{"type":"less_than_equal","loc":["body","temperature_c"],"msg":"Input should be less than or equal to 150","input":500,"ctx":{"le":150.0}}]}` |
| `POST /v1/predicte` (faute de frappe dans l'adresse) | 404 | `{"detail":"Not Found"}` |

Dans `/docs`, où voit-on les bornes que vous avez choisies ?

Dans la route `POST /v1/predict`, onglet « Schema » du corps de la requête, et en bas de la page, dans la section « Schemas », sous `SensorReading`. Chaque champ y affiche son type (`number`), sa description et sa plage (minimum et maximum). Elles viennent de `/openapi.json`, que FastAPI génère à partir du schéma Pydantic.

## 6. Questions de compréhension

1. REST et FastAPI : quelle est la différence ?
   REST est un ensemble de règles pour concevoir une API web : des URL claires, les méthodes HTTP (GET lit, POST envoie), des codes de statut précis, du JSON en entrée et en sortie, une version dans l'URL. FastAPI est une bibliothèque Python qui sert à écrire une API respectant ces règles. On écrit une API REST *avec* FastAPI, et uvicorn la fait tourner.
2. Le schéma Pydantic sert à trois choses. Lesquelles ?
   (1) **Valider** chaque requête avant d'appeler la fonction : 422 avec le champ et la raison si une valeur est invalide. (2) **Documenter** : FastAPI construit `/docs` (types, bornes, descriptions, exemple). (3) **Donner un objet Python typé** : `reading.temperature_c` est un `float` déjà vérifié, et `reading.model_dump()` le transforme en dictionnaire pour le modèle.
3. Dans `http://localhost:8000/v1/predict`, que désignent `localhost`, `8000` et `/v1/predict` ?
   `localhost` est la machine elle-même : le serveur tourne sur notre PC. `8000` est le port où uvicorn écoute. `/v1/predict` est la route, un chemin défini dans le code Python (et non un dossier sur le disque), précédé de la version de l'API.
4. Pourquoi `/v1` dans l'adresse ?
   C'est la version du contrat de l'API. Si l'on change les entrées ou les sorties, on publie une `/v2` sans casser les clients existants, qui continuent d'appeler `/v1`.
5. Dans la commande `uvicorn maintai.api.main:app`, que désignent `maintai.api.main` et `app` ?
   `maintai.api.main` est le module Python, c'est-à-dire le fichier `maintai/api/main.py` écrit avec des points et sans `.py`. `app` est la variable de ce fichier qui contient l'application : `app = FastAPI(...)`.

## 7. Le rendu Git

- Lien de la pull request : *(à compléter après l'ouverture de la PR : `https://github.com/<compte>/<depot>/pull/<n>`)*
- Le tag `tp1` existe sur GitHub : *(à compléter après `git tag tp1` puis `git push --tags` : oui / non)*
- Qui a relu la pull request, et quel commentaire a-t-il laissé ?
  *(à compléter : nom du relecteur parmi Hiba Chefchaouni Moussaoui, Khalid Sammar, Kimath Elmer, et son commentaire)*

## 8. Ce qui reste flou

- **Prédire hors de la plage d'entraînement.** Nos bornes acceptent une charge jusqu'à 150 % et 300 000 h, mais le modèle n'a vu que 20 à 100 % de charge et 0 à 20 000 h. L'API renvoie alors une probabilité sans prévenir qu'elle extrapole. Faut-il le signaler au client, par exemple avec un champ dans la réponse ?
- **Sortir de `localhost`.** L'API ne tourne que sur notre PC, sans protection. Comment l'ouvrir à un autre programme sur le réseau, et comment la clé API (`X-API-Key`, séance 5) empêchera-t-elle n'importe qui de l'appeler ?
- **Versionner le modèle.** `model_version` n'est que la date d'entraînement. Comment savoir avec quelles données et quels réglages un modèle a été produit, et revenir à l'ancien s'il est moins bon (MLflow, séance 7) ?
- **Les outils d'installation.** Nous avons eu à la fois `requirements.txt` (pip) et `pyproject.toml` (uv), avec des versions de FastAPI différentes (0.141.1 contre 0.162.0) : nous ne savons pas encore lequel doit faire référence.
