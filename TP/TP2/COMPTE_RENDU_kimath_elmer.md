# Compte rendu · TP1 : une API de prédiction pour MaintAI

**Groupe :** …  ·  **Membres :*KIMATH Elmer* …  ·  **Date :** …

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP1.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Mise en place

Dernière ligne de `python -m pytest`, juste après la mise en place (rien n'est encore écrit) :

```
FAILED tests/test_api.py::test_predict_returns_probability - assert 422 == 200
FAILED tests/test_api.py::test_high_risk_reading_raises_alert - KeyError: 'alert'
FAILED tests/test_api.py::test_503_when_model_missing - assert 422 == 503
=============== 3 failed, 10 passed, 1 warning in 4.54s ================
```

Dans `tests/test_api.py`, 4 tests sur 7 passent déjà alors que rien n'est écrit. Lesquels ? Pour les deux tests qui attendent un code 422, expliquez pourquoi ils passent « pour une mauvaise raison » (indice : regardez `extra="forbid"` dans `schemas.py`).

Les 4 tests qui passent sont `test_health`, `test_openapi_documents_predict`, `test_out_of_range_value_is_rejected` et `test_missing_field_is_rejected`.
Les deux tests 422 passent pour une mauvaise raison : le schéma est vide et `extra="forbid"` refuse tous les champs. Tout relevé donne donc un 422, même un relevé valide.

## 2. Le schéma d'entrée (`maintai/api/schemas.py`)

| Variable | Type | Minimum (`ge`) | Maximum (`le`) | Justification physique (pas le min / max des données) |
|---|---|---|---|---|
| `temperature_c` | float | -40 | 150 | En dessous de -40 °C ou au-dessus de 150 °C, un moteur industriel est hors plage de capteur. |
| `vibration_mm_s` | float | 0 | 50 | Une vibration ne peut pas être négative, et 50 mm/s est déjà une vibration destructrice. |
| `load_pct` | float | 0 | 100 | Un pourcentage de charge reste entre 0 et 100. |
| `runtime_hours` | float | 0 | 100000 | Les heures ne peuvent pas être négatives, et 100 000 h (environ 11 ans) couvre la vie d'une machine. |

Après avoir écrit `schemas.py` seul, que donne `python -m pytest`, et quel est le message d'erreur des tests qui échouent ? Pourquoi est-ce un bon signe ?

```
FAILED tests/test_api.py::test_predict_returns_probability - assert 422 == 200
FAILED tests/test_api.py::test_high_risk_reading_raises_alert - KeyError: 'alert'
FAILED tests/test_api.py::test_503_when_model_missing - assert 422 == 503
=============== 3 failed, 10 passed, 1 warning in 4.61s ================
```

Les relevés valides ne sont plus refusés par le schéma : ils arrivent jusqu'à `predict()`. Les tests échouent maintenant parce que `predict()` n'est pas encore écrite. C'est un bon signe : la validation fonctionne, et il ne reste que la fonction à écrire.

## 3. La fonction `predict()` (`maintai/api/main.py`)

Votre code :

```python
@router.post("/predict", response_model=PredictionOut)
def predict(reading: SensorReading) -> PredictionOut:
    # TODO (TP1) : Récupérez le predictor dans state ; s'il est absent, levez HTTPException 503 ; sinon renvoyez sa prédiction pour reading.model_dump()
    predictor = state.get("predictor")
    if predictor is None:
        raise HTTPException(status_code=503, detail="Modèle non chargé")
    return predictor.predict(reading.model_dump())
```

Pourquoi répondre **503** et pas 500 quand le modèle manque ?

Le 503 veut dire « service indisponible pour le moment » : le serveur marche, mais le modèle n'est pas prêt. Le 500 veut dire « bug inattendu dans le code ». Ici, le problème est connu et temporaire (il faut entraîner le modèle).

Pourquoi le modèle est-il chargé **une seule fois**, au démarrage, et pas à chaque requête ?

Charger un fichier de modèle prend du temps. Le faire à chaque requête ralentirait toutes les réponses. Au démarrage, on le charge une fois et on le garde en mémoire dans `state`.

## 4. Les tests

Dernière ligne de `python -m pytest` à la fin du TP :

```

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
============================= 19 passed, 1 warning in 2.88s =============================
```

## 5. L'API en marche

Après `python -m maintai.dataset` et `python -m maintai.train`, lancez `uvicorn maintai.api.main:app --reload`, puis envoyez ces requêtes depuis `/docs` (ou avec `curl.exe`).

| Requête | Code obtenu | Réponse (le corps JSON) |
|---|---|---|
| `GET /health` | | |
| `POST /v1/predict` avec `{"temperature_c": 72.5, "vibration_mm_s": 6.1, "load_pct": 85, "runtime_hours": 15000}` | | |
| `POST /v1/predict` avec une température de 500 | | |
| `POST /v1/predicte` (faute de frappe dans l'adresse) | | |

Dans `/docs`, où voit-on les bornes que vous avez choisies ?

Dans `/docs`, on les voit dans le schéma `SensorReading` (en bas, section « Schemas », ou dans le corps de la requête de `POST /v1/predict`). Chaque champ affiche son minimum et son maximum.

## 6. Questions de compréhension

1. REST et FastAPI : quelle est la différence ?
   REST est un style de conception d'API qui utilise HTTP. FastAPI est un outil Python pour construire une API qui suit ce style.
2. Le schéma Pydantic sert à trois choses. Lesquelles ?
   Il valide les données reçues, il documente l'API dans `/docs`, et il convertit le JSON en objet Python.
3. Dans `http://localhost:8000/v1/predict`, que désignent `localhost`, `8000` et `/v1/predict` ?
   `localhost` désigne la machine locale (mon ordinateur). `8000` est le port sur lequel uvicorn écoute. `/v1/predict` est la route de l'API : la version 1, puis la ressource « predict ».
4. Pourquoi `/v1` dans l'adresse ?
   Cela indique la version de l'API. On pourra publier une `/v2` sans casser les programmes qui utilisent la v1.
5. Dans la commande `uvicorn maintai.api.main:app`, que désignent `maintai.api.main` et `app` ?
   `maintai.api.main` est le module Python (le fichier `maintai/api/main.py`), et `app` est l'objet FastAPI défini dans ce fichier.

## 7. Le rendu Git

- Lien de la pull request : …
- Le tag `tp1` existe sur GitHub : oui / non
- Qui a relu la pull request, et quel commentaire a-t-il laissé ?
  …

## 8. Ce qui reste flou

Prédire hors de la plage d'entraînement. Nos bornes acceptent une charge jusqu'à 150 % et 300 000 h, mais le modèle n'a vu que 20 à 100 % de charge et 0 à 20 000 h. L'API renvoie alors une probabilité sans prévenir qu'elle extrapole. Faut-il le signaler au client, par exemple avec un champ dans la réponse ?
Sortir de localhost. L'API ne tourne que sur notre PC, sans protection. Comment l'ouvrir à un autre programme sur le réseau, et comment la clé API ( X-API-Key, séance 5) empêchera-t-elle n'importe qui de l'appeler ?
Versionner le modèle. model_version n'est que la date d'entraînement. Comment savoir avec quelles données et quels réglages un modèle a été produit, et revenir à l'ancien s'il est moins bon (MLflow, séance 7) ?
Les outils d'installation. Nous avons eu à la fois requirements.txt(pip) et pyproject.toml(uv), avec des versions de FastAPI différentes (0.141.1 contre 0.162.0) : nous ne savons pas encore laquelle doit faire référence.
…
