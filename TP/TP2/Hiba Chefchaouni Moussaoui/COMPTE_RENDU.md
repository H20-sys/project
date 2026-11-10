# Compte rendu · TP2 : tester, sécuriser et appeler l'API MaintAI

**Groupe :** G2  ·  **Membres :** Hiba Chefchaouni Moussaoui  ·  **Date :**03/11/2026

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP2.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Activité 1 : casser son API (dans `TP/TP1`)

Vos cinq requêtes, le code que vous aviez **prévu**, puis le code **obtenu** dans `/docs` :

| Requête | Ce qui ne va pas | Code prévu | Code obtenu |
|---|---|---|---|
| 1 | champ manquant |422 |422 |
| 2 | valeur absurde |422 |422 |
| 3 | texte au lieu d'un nombre |422 |422 |
| 4 | champ en trop |422 |422 |
| 5 | mauvaise route |404 |404 |

Une de vos prévisions était-elle fausse ? Laquelle, et pourquoi ?
non
…

Dernière ligne de `python -m pytest` avec `tests/test_casser.py` (dans `TP/TP1`) :

```
========================= 5 passed, 1 warning in 2.27s ==================
```

À quoi sert `@pytest.mark.parametrize` ? Combien de tests pytest compte-t-il pour votre fonction, et pourquoi ?
elle sert a rendre les test dans une liste pour les rassembler
…

## 2. ruff

Sortie de `ruff check .` dans `TP/TP1` :

```
r-tp1> ruff check .
I001 [*] Import block is un-sorted or un-formatted
 --> maintai\api\demo_api.py:1:1
  |
1 | / from fastapi import FastAPI 
2 | | from pydantic import BaseModel, Field
  | |_____________________________________^
3 |
4 |   app = FastAPI()
  |
help: Organize imports
  |
  - from fastapi import FastAPI 
1 + from fastapi import FastAPI
2 | from pydantic import BaseModel, Field
  |

UP017 [*] Use `datetime.UTC` alias
  --> maintai\train.py:58:36
   |
56 |         "target": TARGET,
57 |         "threshold": settings.threshold,
58 |         "trained_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
   |                                    ^^^^^^^^^^^^
59 |         "sklearn_version": sklearn.__version__,
60 |     }
   |
help: Convert to `datetime.UTC` alias
   |
5  | import json
   - from datetime import datetime, timezone
6  + from datetime import datetime, timezone, UTC
7  |
--------------------------------------------------------------------------------
57 |         "threshold": settings.threshold,
   -         "trained_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
58 +         "trained_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
59 |         "sklearn_version": sklearn.__version__,
   |

Found 2 errors.
[*] 2 fixable with `--fix`.
```

Quelle différence entre `ruff check .` et `python -m pytest` ? Que vérifie chacun ?
ruf check. vérifie la qualitée du code et python -m pytest verifie le fonctionement du code
…

## 3. Mise en place du TP2 (dans `TP/TP2`)

Dernière ligne de `python -m pytest` juste après la mise en place :

```
(collez ici)
```

Quels sont les deux tests qui échouent, et que reçoivent-ils au lieu de 401 ?

…

## 4. La clé API (sprint 1)

Votre fonction `require_api_key()` (`maintai/api/security.py`) :

```python
(collez ici le corps de la fonction)
```

Votre ligne `router = ...` dans `maintai/api/main.py` :

```python
(collez ici)
```

Après avoir écrit `security.py` seul (sans toucher au router), combien de tests échouent ? Pourquoi ?

…

Dernière ligne de `python -m pytest` à la fin du sprint 1 :

```
(collez ici)
```

Lancez `uvicorn maintai.api.main:app --reload --env-file .env`, puis envoyez ces requêtes (avec `/docs` ou `curl.exe`) :

| Requête | Code obtenu | Réponse (le corps JSON) |
|---|---|---|
| `GET /health`, sans clé | | |
| `POST /v1/predict`, relevé normal, sans clé | | |
| `POST /v1/predict`, relevé normal, fausse clé | | |
| `POST /v1/predict`, relevé normal, bonne clé | | |
| `POST /v1/predict`, 500 °C, sans clé | | |
| `POST /v1/predict`, 500 °C, bonne clé | | |

500 °C sans clé et 500 °C avec la clé ne donnent pas le même code. Pourquoi ?

…

Relancez uvicorn **sans** `--env-file .env` et envoyez un relevé avec votre clé. Quel code obtenez-vous, et pourquoi ce n'est pas 401 ?

…

## 5. La page web (sprint 2)

Votre code `fetch` (le contenu du `addEventListener` dans `web/index.html`) :

```javascript
(collez ici)
```

Ce qu'affiche la page (servie sur le port 5500) :

| Essai | Ce qu'affiche la page |
|---|---|
| relevé normal, bonne clé | |
| 500 °C, bonne clé | |
| relevé normal, fausse clé | |

**Expérience CORS.** Servez la page sur le port 5501. Que dit la page, et que dit la console (F12) ?

…

Pourquoi `curl.exe` obtient-il une réponse alors que la page du port 5501 est bloquée ?

…

## 6. Les tests de l'activité 1 dans le TP2

Copiez `test_casser.py` dans `TP/TP2/tests`. Sans `headers=HEADERS`, combien de tests échouent, et avec quel code ? Lequel des cinq cas passe quand même, et pourquoi ?

…

Dernière ligne de `python -m pytest` avec `headers=HEADERS` :

```
(collez ici)
```

## 7. Questions de compréhension

1. Quelle différence entre 401 et 422 ? Et entre 401 et 403 ?
   …
2. Pourquoi la clé n'est-elle ni dans le code ni dans Git ? Que contiennent `.env` et `.env.example`, et lequel est commité ?
   …
3. Pourquoi la clé voyage-t-elle dans un en-tête et pas dans l'URL ?
   …
4. Que fait `secrets.compare_digest` de plus qu'un simple `==` ?
   …
5. Qu'est-ce qu'une « origine » ? `http://localhost:5500` et `http://localhost:8000` sont-elles la même origine ?
   …

## 8. Le rendu Git

- Lien de la pull request : …
- Le tag `tp2` existe sur GitHub : oui / non
- `git status` avant le commit : le fichier `.env` apparaissait-il ? oui / non
- Qui a relu la pull request, et quel commentaire a-t-il laissé ?
  …

## 9. Ce qui reste flou

…
