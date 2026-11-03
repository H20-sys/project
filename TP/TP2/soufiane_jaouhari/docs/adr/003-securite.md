# ADR 003 : transmission de la clé API et origines autorisées (CORS)

Date : 03/11/2026 · Auteurs : Soufiane Jaouhari, Hiba Chefchaouni Moussaoui, Khalid Sammar, Kimath Elmer (Grp 2)

## Contexte
L'API MaintAI ne doit répondre qu'aux programmes autorisés : chacun envoie une clé, qui ne doit apparaître ni dans le code ni dans Git. Une page web servie sur `http://localhost:5500` doit pouvoir appeler l'API depuis le navigateur, mais pas une page servie ailleurs. Il faut décider où voyage la clé, et quelles origines le navigateur a le droit d'utiliser.

## Décision 1 : où transmettre la clé ?

### Options étudiées
1. **Dans l'URL** (`/v1/predict?key=...`).
   - Avantage : simple, on peut tester avec un lien.
   - Ce qu'on perd : le secret. Une URL est enregistrée partout : journaux du serveur (uvicorn affiche chaque chemin), historique du navigateur, proxys, en-tête `Referer`. La clé finirait en clair dans des fichiers que d'autres lisent.
2. **Dans le corps JSON** (un champ `api_key` à côté des mesures).
   - Avantage : pas visible dans l'URL.
   - Ce qu'on perd : la séparation entre « qui appelle » et « les données ». Il faudrait ajouter un champ à `SensorReading`, ce qui change le contrat du modèle et contredit `extra="forbid"`. Une route `GET` n'a pas de corps. Et la clé ne serait lue qu'après l'analyse du JSON : un relevé invalide envoyé sans clé recevrait 422 au lieu de 401.
3. **Dans un en-tête** (`X-API-Key`).
   - Avantages : c'est la place prévue par HTTP pour l'authentification. Les en-têtes ne sont pas écrits dans les journaux d'accès, la clé est vérifiée avant les données (401 avant 422), et le mécanisme est le même pour toutes les routes `/v1`. `/docs` affiche le champ `x-api-key`.
   - Ce qu'on perd : un en-tête personnalisé déclenche une requête `OPTIONS` (preflight) côté navigateur, et doit figurer dans `allow_headers`. On ne peut plus tester avec un simple lien.

### Décision
La clé voyage dans l'en-tête **`X-API-Key`**. Elle est comparée avec `secrets.compare_digest` à la clé du serveur, lue dans `.env` au démarrage (`--env-file .env`). Le `.env` est exclu par le `.gitignore`, et seul `.env.example`, avec une fausse valeur, est commité.

## Décision 2 : quelles origines autoriser, et où les configurer ?

### Options étudiées
1. **`*` (toutes les origines).**
   - Avantage : aucune configuration, toute page peut appeler l'API.
   - Ce qu'on perd : le contrôle. N'importe quel site, y compris une page piégée où l'utilisateur taperait sa clé, pourrait appeler l'API depuis son navigateur. On ne sait plus quelles pages utilisent l'API.
2. **Une liste explicite** (`http://localhost:5500`, `http://127.0.0.1:5500`).
   - Avantage : seule notre page web peut appeler l'API depuis un navigateur. Une autre origine reçoit un refus au preflight (400 « Disallowed CORS origin »), et le navigateur n'envoie même pas le `POST`.
   - Ce qu'on perd : chaque nouveau client web (un autre port, le vrai domaine en production) doit être ajouté à la liste, puis uvicorn relancé, car la liste est lue au démarrage. Il faut penser à `localhost` **et** `127.0.0.1`, qui sont deux origines différentes.

### Où configurer la liste ?
Dans `.env` (`MAINTAI_CORS_ORIGINS`), et non dans le code : la liste change d'un environnement à l'autre (PC, serveur de la séance 8) sans modifier le code. `.env.example` donne la valeur par défaut.

### Décision
Une **liste explicite**, lue dans `.env`.

## Conséquences
- CORS est une règle **du navigateur** : elle protège l'utilisateur contre une page qui utiliserait son navigateur, mais pas l'API. `curl.exe`, Java ou Python ne demandent pas la permission. La clé reste donc indispensable.
- Sans `--env-file .env`, le serveur n'a pas de clé : toutes les routes `/v1` répondent 500 (« clé non configurée »). C'est voulu, pour ne jamais tourner sans protection par erreur.
- Une seule clé est partagée par tous les clients : impossible de savoir qui appelle, ou de retirer l'accès à un seul client. Il faudrait une clé par client, et le code 403 pour l'autorisation (hors TP2).
- Une clé commitée par erreur reste dans l'historique de Git : il faut alors la changer, pas seulement supprimer le fichier.
