# Compte rendu · TP2 : tester, sécuriser et appeler l'API MaintAI

**Groupe :** Grp 2  ·  **Membres :** Soufiane Jaouhari, Hiba Chefchaouni Moussaoui, Khalid Sammar, Kimath Elmer  ·  **Date :** 03/11/2026

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP2.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Activité 1 : casser son API (dans `TP/TP1`)

Vos cinq requêtes, le code que vous aviez **prévu**, puis le code **obtenu** dans `/docs` :

| Requête | Ce qui ne va pas | Code prévu | Code obtenu |
|---|---|---|---|
| 1 · `VALID` sans `load_pct` | champ manquant | 422 | 422 |
| 2 · `{**VALID, "load_pct": 250}` | valeur absurde | 422 | 422 |
| 3 · `{**VALID, "temperature_c": "chaud"}` | texte au lieu d'un nombre | 422 | 422 |
| 4 · `{**VALID, "humidite_pct": 40}` | champ en trop | 422 | 422 |
| 5 · `POST /v1/predicte` | mauvaise route | 404 | 404 |

(`VALID` = `{"temperature_c": 60.0, "vibration_mm_s": 2.0, "load_pct": 50.0, "runtime_hours": 5000}`)

Une de vos prévisions était-elle fausse ? Laquelle, et pourquoi ?

Les cinq prévisions étaient justes. En cherchant d'autres requêtes (étape 4), deux prévisions se sont révélées fausses :
- `"runtime_hours": true` : prévu 422, obtenu **200**. Pydantic, en mode « souple », convertit `true` en `1.0`.
- `"temperature_c": "60"` : prévu 422, obtenu **200**. Le texte `"60"` est converti en `60.0`.

Nous avons corrigé `schemas.py` avec `strict=True` : seuls de vrais nombres JSON sont acceptés, et `5000` ou `15000.5` passent toujours. Nous avons gardé le test : un 6ᵉ cas « booléen au lieu d'un nombre » dans `test_casser.py`.

Autre découverte, non corrigée : `NaN` et `Infinity` donnent **500** au lieu de 422. Le schéma les refuse bien (`le=150`), mais FastAPI plante en écrivant la réponse 422, parce que le JSON ne sait pas représenter `NaN` dans le champ `input` du message d'erreur. Le modèle n'est jamais appelé. Ces valeurs ne sont d'ailleurs pas du JSON valide, et un client normal ne les envoie pas.

Dernière ligne de `python -m pytest` avec `tests/test_casser.py` (dans `TP/TP1`) :

```
============================= 19 passed in 2.54s ==============================
```

(13 tests du TP1 + 5 cas + le cas « booléen » trouvé à l'étape 4.)

À quoi sert `@pytest.mark.parametrize` ? Combien de tests pytest compte-t-il pour votre fonction, et pourquoi ?

`parametrize` lance la même fonction de test une fois par ligne de la liste `CAS_REFUSES`, avec des arguments différents (description, URL, corps, code attendu). On écrit le test une seule fois, et ajouter un cas ne demande qu'une ligne. pytest compte **6 tests** pour notre fonction : un par cas. Chaque cas est nommé dans le rapport (`python -m pytest -v`), et un cas qui échoue n'empêche pas les autres de s'exécuter.

## 2. ruff

Sortie de `ruff check .` dans `TP/TP1` :

```
I001 [*] Import block is un-sorted or un-formatted
 --> maintai\api\demo_api.py:1:1
UP017 [*] Use `datetime.UTC` alias
  --> maintai\train.py:58:36
Found 2 errors.
[*] 2 fixable with `--fix`.
```

Puis `ruff check . --fix` (« Found 4 errors (4 fixed, 0 remaining) »), `ruff format .` (11 fichiers mis en forme), `python -m pytest` (toujours 19 passed), et enfin :

```
All checks passed!
```

Quelle différence entre `ruff check .` et `python -m pytest` ? Que vérifie chacun ?

`ruff` **lit** le code sans l'exécuter et signale ce qui est mal écrit : imports inutiles ou mal rangés, variables jamais utilisées, tournures dépassées ; `ruff format` met le code en forme. `pytest` **exécute** le code et vérifie ce qu'il fait : « si j'envoie 500 °C, l'API répond-elle 422 ? ». ruff ne voit pas qu'une API renvoie un mauvais code, et pytest ne voit pas un import inutile : les deux se complètent.

## 3. Mise en place du TP2 (dans `TP/TP2`)

Dernière ligne de `python -m pytest` juste après la mise en place :

```
======================== 2 failed, 16 passed in 3.46s =========================
```

Quels sont les deux tests qui échouent, et que reçoivent-ils au lieu de 401 ?

`test_missing_key_is_rejected` (sans clé) et `test_wrong_key_is_rejected` (avec la fausse clé `wrong`). Ils reçoivent **200**, une prédiction normale : l'API ne vérifie encore aucune clé.

## 4. La clé API (sprint 1)

Votre fonction `require_api_key()` (`maintai/api/security.py`) :

```python
def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Refuse la requête si la clé est absente ou fausse."""
    expected = get_settings().api_key
    if expected is None:
        # Erreur de configuration du serveur, pas du client : 500, et un message qui dit quoi faire
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="La clé API du serveur n'est pas configurée : lancez uvicorn avec --env-file .env",
        )
    # compare_digest prend le même temps que la clé soit juste ou non (pas de fuite par la durée).
    # On compare des octets : sur des textes avec accents ("clé"), compare_digest plante (500 au lieu de 401)
    if x_api_key is None or not secrets.compare_digest(
        x_api_key.encode(), expected.encode()
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clé API absente ou invalide",
        )
```

Faute trouvée en relisant : notre première version comparait directement les deux textes, `secrets.compare_digest(x_api_key, expected)`. Les tests passaient, mais une clé avec un accent (`X-API-Key: clé`) faisait **planter** l'API : **500** au lieu de 401, car `compare_digest` refuse de comparer des textes non ASCII (`TypeError`). En comparant des octets (`.encode()`), on obtient bien 401. Nous avons gardé le test : `test_cle_avec_accent_donne_401` dans `test_casser.py`.

Votre ligne `router = ...` dans `maintai/api/main.py` :

```python
router = APIRouter(prefix="/v1", dependencies=[Depends(require_api_key)])
```

Après avoir écrit `security.py` seul (sans toucher au router), combien de tests échouent ? Pourquoi ?

Toujours **2** (`2 failed, 16 passed`). La fonction existe, mais rien ne l'appelle : tant qu'elle n'est pas déclarée comme dépendance du router, FastAPI ne l'exécute jamais, et les requêtes sans clé reçoivent encore 200.

Dernière ligne de `python -m pytest` à la fin du sprint 1 :

```
============================= 18 passed in 2.68s ==============================
```

Lancez `uvicorn maintai.api.main:app --reload --env-file .env`, puis envoyez ces requêtes (avec `/docs` ou `curl.exe`) :

| Requête | Code obtenu | Réponse (le corps JSON) |
|---|---|---|
| `GET /health`, sans clé | 200 | `{"status":"ok","model_loaded":true}` |
| `POST /v1/predict`, relevé normal, sans clé | 401 | `{"detail":"Clé API absente ou invalide"}` |
| `POST /v1/predict`, relevé normal, fausse clé | 401 | `{"detail":"Clé API absente ou invalide"}` |
| `POST /v1/predict`, relevé normal, bonne clé | 200 | `{"failure_probability":0.9553,"alert":true,"threshold":0.3,"model_version":"2026-11-03T17:10:36Z"}` |
| `POST /v1/predict`, 500 °C, sans clé | 401 | `{"detail":"Clé API absente ou invalide"}` |
| `POST /v1/predict`, 500 °C, bonne clé | 422 | `{"detail":[{"type":"less_than_equal","loc":["body","temperature_c"],"msg":"Input should be less than or equal to 150","input":500,"ctx":{"le":150.0}}]}` |

(Relevé normal : `{"temperature_c": 72.5, "vibration_mm_s": 6.1, "load_pct": 85, "runtime_hours": 15000}`.)

500 °C sans clé et 500 °C avec la clé ne donnent pas le même code. Pourquoi ?

Une requête passe une suite de contrôles, et le premier qui échoue donne la réponse : la route (404), puis **la clé (401)**, puis **les données (422)**, puis le modèle (503). Sans clé, la requête est arrêtée au contrôle de la clé : l'API ne regarde même pas les données, d'où 401. Avec la bonne clé, elle passe ce contrôle et c'est la validation du schéma qui refuse 500 °C, d'où 422.

Relancez uvicorn **sans** `--env-file .env` et envoyez un relevé avec votre clé. Quel code obtenez-vous, et pourquoi ce n'est pas 401 ?

**500**, avec `{"detail":"La clé API du serveur n'est pas configurée : lancez uvicorn avec --env-file .env"}`. Ce n'est pas 401, parce que le client n'est pas en faute : sa clé est peut-être bonne, mais le serveur n'a aucune clé à laquelle la comparer (`get_settings().api_key` vaut `None`). C'est une erreur de configuration du serveur, donc un code 5xx. Et le serveur refuse tout plutôt que de tourner sans protection.

## 5. La page web (sprint 2)

Votre code `fetch` (le contenu du `addEventListener` dans `web/index.html`) :

```javascript
  // Champ vide -> null : l'API répond 422, au lieu de prédire avec 0 sans prévenir (Number("") vaut 0)
  const reading = Object.fromEntries(FEATURES.map(f => {
    const v = document.getElementById(f).value;
    return [f, v === "" ? null : Number(v)];
  }));
  const adresse = document.getElementById("url").value.replace(/\/+$/, "") + "/v1/predict";
  const cle = document.getElementById("key").value;
  try {
    const resp = await fetch(adresse, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-API-Key": cle },
      body: JSON.stringify(reading),  // l'objet devient du texte JSON
    });
    const data = await resp.json().catch(() => ({ detail: resp.statusText }));
    if (!resp.ok) {
      // 401 (clé), 422 (relevé refusé), 503 (modèle absent) : le code et l'explication de l'API
      const detail = Array.isArray(data.detail)
        ? data.detail.map(d => `${d.loc.at(-1)} : ${d.msg}`).join(" ; ")
        : data.detail;
      show("err", `Erreur ${resp.status} : ${detail}`);
      return;
    }
    const pct = (data.failure_probability * 100).toFixed(1);
    const seuil = Math.round(data.threshold * 100);
    if (data.alert) show("alert", `ALERTE : probabilité de panne ${pct} % (seuil ${seuil} %)`);
    else show("ok", `Pas d'alerte : probabilité de panne ${pct} % (seuil ${seuil} %)`);
  } catch (e) {
    // Pas de réponse lisible : l'API est arrêtée, ou CORS bloque cette origine
    show("err", `API injoignable (arrêtée, ou origine refusée par CORS) : ${e.message}`);
  }
```

Ce qu'affiche la page (servie sur le port 5500) :

| Essai | Ce qu'affiche la page |
|---|---|
| relevé normal, bonne clé | « ALERTE : probabilité de panne 94.8 % (seuil 30 %) », sur fond rouge (relevé par défaut de la page : 72 °C, 6 mm/s, 85 %, 15 000 h) |
| 500 °C, bonne clé | « Erreur 422 : temperature_c : Input should be less than or equal to 150 » |
| relevé normal, fausse clé | « Erreur 401 : Clé API absente ou invalide » |
| température laissée vide, bonne clé | « Erreur 422 : temperature_c : Input should be a valid number » |

Faute corrigée : la première version faisait `Number(valeur)` sur chaque champ. Or `Number("")` vaut `0` : un champ laissé vide envoyait 0 °C, et la page affichait une prédiction sans prévenir. Un champ vide est maintenant envoyé comme `null`, et l'API le refuse (422).

**Expérience CORS.** Servez la page sur le port 5501. Que dit la page, et que dit la console (F12) ?

La page affiche « API injoignable (arrêtée, ou origine refusée par CORS) : Failed to fetch » : `fetch` échoue sans réponse lisible. La console signale que la requête vers `http://localhost:8000/v1/predict` depuis l'origine `http://localhost:5501` est bloquée par la politique CORS. L'onglet Network (Réseau) montre la requête `OPTIONS` (le preflight, « puis-je ? ») refusée avec **400**. Le journal d'uvicorn ne contient que ces `OPTIONS /v1/predict 400 Bad Request` (corps : « Disallowed CORS origin ») : le navigateur n'a jamais envoyé le `POST`. Depuis le port 5500, au contraire, le preflight reçoit 200 et `access-control-allow-origin: http://localhost:5500`.

Pourquoi `curl.exe` obtient-il une réponse alors que la page du port 5501 est bloquée ?

CORS est une règle **du navigateur**, pas de l'API. C'est le navigateur qui demande la permission (`OPTIONS`) et qui bloque si l'API ne répond pas `Access-Control-Allow-Origin`. `curl.exe` n'est pas un navigateur : il n'envoie pas de preflight et ignore ces en-têtes. Avec `-H "Origin: http://localhost:5501"` et la bonne clé, `curl` a obtenu `200 OK` et la prédiction, sans `access-control-allow-origin` dans la réponse. CORS protège l'utilisateur contre une page qui utiliserait son navigateur ; ce qui protège l'API, c'est la clé.

**Un client Java.** `clients/java/MaintAIClient.java` envoie la même requête avec `java.net.http.HttpClient` : `POST /v1/predict`, en-têtes `Content-Type` et `X-API-Key`, le relevé en JSON. La clé est lue dans la variable d'environnement `MAINTAI_API_KEY`, jamais écrite dans le code :

```
PS> $env:MAINTAI_API_KEY = "<la clé de .env>" ; java clients\java\MaintAIClient.java
HTTP 200
{"failure_probability":0.9553,"alert":true,"threshold":0.3,"model_version":"2026-11-03T17:10:36Z"}
PS> $env:MAINTAI_API_KEY = "faux" ; java clients\java\MaintAIClient.java
HTTP 401
{"detail":"Clé API absente ou invalide"}
```

Même réponse que `curl.exe` et la page web : l'API ne sait pas qui l'appelle, seul le contrat compte. Piège rencontré : au premier essai, la bonne clé donnait **422 « Field required »** (corps vide). Par défaut, le `HttpClient` de Java tente de passer en HTTP/2 (en-tête `Upgrade: h2c`) ; uvicorn ne gère pas cette montée et le corps se perd. Avec `.version(HttpClient.Version.HTTP_1_1)`, on obtient 200. Comme pour CORS, Java n'envoie pas de preflight : seule la clé compte.

## 6. Les tests de l'activité 1 dans le TP2

Copiez `test_casser.py` dans `TP/TP2/tests`. Sans `headers=HEADERS`, combien de tests échouent, et avec quel code ? Lequel des cinq cas passe quand même, et pourquoi ?

Sans `headers=HEADERS`, **4 des 5 cas échouent** : les quatre qui attendent 422 reçoivent **401** (`assert 401 == 422`). Notre 6ᵉ cas (booléen) échoue aussi avec 401, d'où `5 failed, 1 passed`. La clé est vérifiée **avant** les données : sans clé, l'API ne regarde même pas le corps. Le cas qui passe quand même est **« mauvaise route »** (404) : `/v1/predicte` n'existe pas, le contrôle de la route vient en premier, et la requête n'atteint jamais le router ni sa dépendance `require_api_key`.

Dernière ligne de `python -m pytest` avec `headers=HEADERS` :

```
============================= 25 passed in 2.78s ==============================
```

(18 tests du TP2 + nos 6 cas + `test_cle_avec_accent_donne_401`. Avec les seuls 5 cas de l'énoncé, on obtient les 23 attendus : nous avons d'abord eu `1 failed, 23 passed`, car le `schemas.py` du starter TP2 n'a pas `strict=True`. Nous y avons reporté la correction de l'activité 1.)

## 7. Questions de compréhension

1. Quelle différence entre 401 et 422 ? Et entre 401 et 403 ?
   **401** : l'API ne sait pas qui appelle (clé absente ou fausse) ; elle s'arrête avant de regarder les données. **422** : l'appelant est authentifié, mais ses données sont refusées par le schéma (valeur hors bornes, champ manquant…). **401** veut dire « je ne sais pas qui vous êtes » (authentification) ; **403** veut dire « je sais qui vous êtes, mais vous n'avez pas le droit de faire ça » (autorisation, hors TP2).
2. Pourquoi la clé n'est-elle ni dans le code ni dans Git ? Que contiennent `.env` et `.env.example`, et lequel est commité ?
   Le code part sur GitHub, et une clé commitée une seule fois reste dans l'historique de Git pour toujours, même si on supprime le fichier : il faudrait la changer. `.env` contient les vraies valeurs (`MAINTAI_API_KEY=` la vraie clé, `MAINTAI_CORS_ORIGINS=` les origines autorisées). Il reste sur chaque machine, exclu par le `.gitignore`, et est lu au démarrage par `--env-file .env`. `.env.example` contient les mêmes variables avec une fausse valeur (`changez-moi`) : il dit **quoi** configurer. C'est lui qui est commité, jamais `.env`.
3. Pourquoi la clé voyage-t-elle dans un en-tête et pas dans l'URL ?
   Une URL est enregistrée partout : journaux du serveur (uvicorn affiche chaque chemin), historique du navigateur, proxys, en-tête `Referer`. Une clé dans l'URL se retrouverait en clair dans tous ces fichiers. Les en-têtes ne sont pas écrits dans les journaux d'accès.
4. Que fait `secrets.compare_digest` de plus qu'un simple `==` ?
   Elle compare en **temps constant**. `==` s'arrête au premier caractère différent : une clé dont les 10 premiers caractères sont justes est rejetée un peu plus tard qu'une clé fausse dès le premier. En mesurant la durée des réponses, un attaquant pourrait deviner la clé caractère par caractère (attaque temporelle). `compare_digest` met le même temps quelle que soit la clé.
5. Qu'est-ce qu'une « origine » ? `http://localhost:5500` et `http://localhost:8000` sont-elles la même origine ?
   Une origine, c'est le trio **schéma + domaine + port**. `http://localhost:5500` et `http://localhost:8000` ont le même schéma et le même domaine, mais pas le même port : ce sont **deux origines différentes**. C'est pourquoi la page (5500) doit avoir la permission CORS pour appeler l'API (8000). De même, `localhost` et `127.0.0.1` sont deux origines différentes, d'où les deux entrées dans `MAINTAI_CORS_ORIGINS`.

## 8. Le rendu Git

- Lien de la pull request : *(à compléter après l'ouverture de la PR de la branche `tp2`)*
- Le tag `tp2` existe sur GitHub : *(à compléter après la fusion, `git tag tp2` puis `git push --tags`)*
- `git status` avant le commit : le fichier `.env` apparaissait-il ? *(à vérifier au moment du commit : il ne doit pas apparaître, car le `.gitignore` de `TP/TP2` contient la règle `.env`)*
- Qui a relu la pull request, et quel commentaire a-t-il laissé ?
  *(à compléter : relecteur parmi Hiba Chefchaouni Moussaoui, Khalid Sammar, Kimath Elmer, et son commentaire)*

## 9. Ce qui reste flou

- **Distribuer la clé.** La page web demande à l'utilisateur de taper la clé. Si la page était en ligne pour de vrais utilisateurs, comment leur donner une clé sans la publier, puisque tout ce qui est dans le navigateur est visible ?
- **Une seule clé pour tout le monde.** Tous les clients partagent la même clé : impossible de savoir qui appelle, ou de retirer l'accès à un seul client sans changer la clé de tous.
- **HTTPS.** En local, la clé voyage en clair sur `http://`. Sur un vrai réseau, sans HTTPS, n'importe qui sur le chemin pourrait la lire dans l'en-tête.
- **`NaN` / `Infinity` → 500.** Le schéma les refuse, mais FastAPI n'arrive pas à écrire la réponse 422. Faut-il un gestionnaire d'erreurs dédié, ou refuser ces valeurs avant même la validation ?
