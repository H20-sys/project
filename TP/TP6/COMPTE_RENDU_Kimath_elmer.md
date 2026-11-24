# Compte rendu · TP6 : conteneuriser MaintAI (Docker, Docker Compose)

**Groupe :** …  ·  **Membres :*KIMATH Elmer* …  ·  **Date :** 24/11/2026

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP6.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Mise en place (dans `TP/TP6`)

Sortie de `docker run hello-world` (première ligne) et de `docker version` (lignes Client et Server) :

```
(
Hello from Docker!
This message shows that your installation appears to be working correctly.

To generate this message, Docker took the following steps:
 1. The Docker client contacted the Docker daemon.
 2. The Docker daemon pulled the "hello-world" image from the Docker Hub.
    (amd64)
 3. The Docker daemon created a new container from that image which runs the
    executable that produces the output you are currently reading.
 4. The Docker daemon streamed that output to the Docker client, which sent it
    to your terminal.

To try something more ambitious, you can run an Ubuntu container with:
 $ docker run -it ubuntu bash

Share images, automate workflows, and more with a free Docker ID:
 https://hub.docker.com/

For more examples and ideas, visit:
 https://docs.docker.com/get-started/)

 Docker version 29.1.3, build f52814d
```

Dernière ligne de `python -m pytest` après la mise en place :

```
(-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=================== 38 passed, 4 warnings in 31.31s ====================
(.venv) PS C:\Users\lenovo\Desktop\EMSI\DevAppIntelligent\TP6> )
```

## 2. Image et conteneur (pendant le premier build)

1. Quelle différence entre une image et un conteneur ?
   L'image est le paquet figé et nommé, construit à partir du Dockerfile. Le conteneur est une copie de cette image qui tourne, isolée. Avec une image, on peut lancer autant de conteneurs qu'on veut.
2. Pourquoi `COPY requirements-docker.txt` est-il placé avant `COPY maintai` ?
   Docker réutilise les couches jusqu'à la première qui change. Les bibliothèques sont lentes à installer et changent rarement. Le code change souvent. En les mettant avant le code, le `pip install` reste en cache.
3. Pourquoi `requirements-docker.txt` contient-il `scikit-learn==1.8.0` et pas `scikit-learn>=1.5` ?
   Le modèle a été sauvegardé avec la version 1.8.0. Il doit être relu avec la même version. Avec `>=`, une version plus récente pourrait être installée et casser le modèle.
4. Pourquoi ni `mlflow`, ni `dvc`, ni `pytest` dans l'image ?
   Ils servent à entraîner, suivre et tester, pas à faire tourner l'API. Sans eux, l'image est plus légère et se construit plus vite.

## 3. Sprint 1 : le Dockerfile

Votre `Dockerfile` :

```dockerfile
(collez ici le contenu de votre Dockerfile)
```

| Build | Durée | Taille de l'image (`docker images`) |
|---|---|---|
| premier build | (votre durée) | (votre taille) |
| après une modification de `maintai/predict.py` | (votre durée) | (votre taille) |

Que signifie `CACHED` dans le journal du second build ?

Cela veut dire que Docker a réutilisé une couche déjà construite, sans la refaire. Les couches avant le code n'ont pas changé, donc le `pip install` est `CACHED`. Seul le code est recopié, donc le build est bien plus rapide.

## 4. Sprint 1 : lancer un conteneur

Votre commande `docker run` :

```
docker run -d --name maintai-api -p 8000:8000 --env-file .env -v "${PWD}\models:/app/models:ro" maintai:0.4.0
```

| Essai | Réponse |
|---|---|
| `GET /health` | `{"status":"ok","model_loaded":true}` |
| `POST /v1/predict` sans clé | 401 |
| `POST /v1/predict` avec la clé | une `failure_probability` (collez votre valeur) |

**Piège 1.** Sans l'option `-v ...models...`, que répondent `/health` et `/v1/predict` ? Pourquoi ?

`/health` répond `"model_loaded":false` et `/v1/predict` répond 503 « Modèle non chargé ». Le modèle n'est pas dans l'image. Il arrive par le volume. Sans volume, l'API démarre mais n'a rien à charger.

**Piège 2.** Avec `--host 127.0.0.1`, que disent `docker logs test` et `http://localhost:8002/health` ? Pourquoi ?

Les logs disent « Uvicorn running on http://127.0.0.1:8000 », mais `http://localhost:8002/health` ne répond pas. Dans un conteneur, `127.0.0.1` veut dire « ce conteneur seulement ». Docker relie le PC au conteneur par une autre interface, donc la demande n'arrive pas. Avec `0.0.0.0`, l'API écoute partout.

## 5. Sprint 2 : Docker Compose

Votre `compose.yaml` :

```yaml
(# MaintAI en deux conteneurs : l'API et l'interface Streamlit.
# Lancer : docker compose up --build      Arrêter : docker compose down

services:
  api:
    build: .
    image: maintai:0.4.0
    env_file: .env                     # MAINTAI_API_KEY, comme au TP2
    ports:
      - "8000:8000"                    # PC:conteneur
    # TODO TP6 sprint 2 : monter le dossier models du PC dans /app/models, en lecture seule
    #   volumes:
    #     - ./...:/app/...:ro
    volumes:
      - ./models:/app/models:ro

  # TODO TP6 sprint 2 : le service ui
  #   - la même image (maintai:0.4.0), avec une autre commande :
  #       ["python", "-m", "streamlit", "run", "ui/app.py",
  #        "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
  #   - la variable MAINTAI_API_URL : l'adresse de l'API vue depuis ce conteneur (le nom du service, port 8000)
  #   - le port 8501 publié sur le PC
  #   - le dossier data du PC monté dans /app/data, en lecture seule
  #   - depends_on : api
  ui:
    image: maintai:0.4.0
    command: ["python", "-m", "streamlit", "run", "ui/app.py",
              "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
    environment:
      MAINTAI_API_URL: http://api:8000
    ports:
      - "8501:8501"
    volumes:
      - ./data:/app/data:ro
    depends_on:
      - api)
```

Sortie de `docker compose ps` :

```
(NAME      IMAGE     COMMAND   SERVICE   CREATED   STATUS    PORTS)
```

Quelle URL affiche la barre latérale de l'interface ? D'où vient-elle ?

Elle affiche `http://api:8000`. Elle vient de la variable `MAINTAI_API_URL`, définie dans `compose.yaml` pour le service `ui`. Le fichier `ui/app.py` la lit avec `os.getenv`.

Résultat des deux commandes `docker compose exec ui ...` (avec `api` puis avec `localhost`). Pourquoi la seconde échoue-t-elle ?

```
(service "ui" is not running
service "localhost" is not running)
```

La seconde échoue avec `Connection refused`. Dans le conteneur `ui`, `localhost` veut dire « ce conteneur seulement », et il n'y a pas d'API dedans. Dans le navigateur, `localhost:8000` marche parce que le navigateur est sur le PC, où Docker publie le port 8000. Entre conteneurs, on utilise le nom du service : `api`.

Dernière ligne de `python -m pytest` à la fin du sprint 2 :

```
(=================== 38 passed, 4 warnings in 33.11s ====================)
```

## 6. Décision : l'ADR 005

Dans `docs/adr/005-image-docker.md`. Résumez ici votre décision en deux phrases :

Le modèle n'est pas dans l'image : il arrive au lancement par un volume, pour changer de modèle sans refaire l'image. Le `.dockerignore` laisse dehors les données, le modèle, le secret `.env`, MLflow et DVC, car ils sont lourds, locaux ou secrets.

## 7. Questions de compréhension

1. Qu'est-ce qui entre dans l'image, et qu'est-ce qui arrive au lancement ? Donnez le moyen pour chaque élément.
   Dans l'image : Linux, Python 3.11, les bibliothèques et le code (`maintai/`, `ui/`), par `docker build`. Au lancement : le modèle (`-v`, volume), les données (`-v`, volume) et la clé API (`--env-file .env`).
2. Pourquoi la clé API n'est-elle jamais dans l'image ?
   Une image peut être partagée. Si la clé est dedans, tous ceux qui ont l'image peuvent la lire. On la donne donc au lancement.
3. Livrer un modèle (TP4, TP5) : qu'est-ce que Docker ajoute à la liste ?
   Docker ajoute l'environnement : le système, Python et les bonnes versions des bibliothèques. L'API tourne alors de la même façon sur tout PC ou serveur où Docker est installé, sans `.venv`.

## 8. Le rendu Git

- Lien de la pull request : …
- Le tag `tp6` existe sur GitHub : oui / non
- `git status` avant le commit : `.env`, `models/` ou `data/*.csv` apparaissaient-ils ? non

## 9. Ce qui reste flou

…