# Compte rendu · TP5 : suivre les entraînements (MLflow) et versionner les données (DVC)

**Groupe :** Grp 2  ·  **Membres :** Soufiane Jaouhari, Hiba Chefchaouni Moussaoui, Khalid Sammar, Kimath Elmer, Abdellah Mamdouh  ·  **Date :** 17/11/2026

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP5.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Mise en place (dans `TP/TP5`)

Dernière ligne de `python -m pytest` après `pip install -r requirements.txt` et `pip install -e .` :

```
FAILED tests/test_tracking.py::test_training_creates_a_run - AssertionError: ...
FAILED tests/test_tracking.py::test_run_records_metrics - AssertionError: auc...
FAILED tests/test_tracking.py::test_run_records_data_version - AssertionError...
FAILED tests/test_tracking.py::test_run_stores_the_model - AssertionError: au...
FAILED tests/test_tracking.py::test_options_change_the_run - AssertionError: ...
5 failed, 27 passed, 2 warnings in 49.40s
```

Quels tests échouent, et pourquoi ?

Les 5 tests de `tests/test_tracking.py`. Dans le starter, `log_run` ne fait rien et renvoie `""` : aucun run n'est
enregistré dans MLflow, donc `mlflow.search_runs(...)` ne trouve rien et les tests s'arrêtent sur
« aucun run MLflow : log_run n'a rien enregistré ». Les 27 autres tests (API, client, CLI, données, package,
sécurité, UI) passent : le code du TP4 n'a pas changé.

Avant `pip install -e .`, où pointait le package `maintai` installé dans l'environnement ? Et après ?

Avant : dans l'environnement du TP4, `maintai` était installé en mode éditable depuis `TP\TP4` : un `import maintai`
lancé hors du dossier TP5 (ou la commande `maintai-predict`) aurait exécuté le code du TP4, et
`test_installed_version_matches_the_code` échoue si la version installée diffère de celle du code.
Après : `pip show maintai` donne `Version: 0.3.0` et `Editable project location: C:\9RAYA\EMSI\S3\APP\TP5` :
le package pointe vers le code du TP5.

## 2. Sprint 1 : MLflow

Votre fonction `log_run` (`maintai/tracking.py`) :

```python
def log_run(params: dict, metrics: dict, model, X_example, data_path: Path) -> str:
    """Enregistre un entraînement : paramètres, version des données, métriques et modèle. Renvoie l'id du run."""
    mlflow.set_experiment(EXPERIMENT)  # tous les runs de MaintAI sous le même nom
    with mlflow.start_run() as run:  # tout ce qui est enregistré dans le with appartient au run
        mlflow.log_params(params)
        mlflow.log_param("data_md5", file_md5(data_path))  # la version des données, comme dans le .dvc
        mlflow.log_metrics(metrics)
        mlflow.sklearn.log_model(
            model,
            name="model",
            input_example=X_example,
            skops_trusted_types=TRUSTED_TYPES,
        )
    return run.info.run_id
```

Dernière ligne de `python -m pytest` à la fin du sprint 1 :

```
32 passed, 4 warnings in 43.74s
```

Vos runs (au moins quatre), relevés dans `mlflow ui` (mode « Model training ») :

Tous sur les données v1 (`data_md5` = `73e0b7cb…`, n_train = 4000, test : 1000 relevés dont 136 pannes).

| Commande | recall | precision | accuracy |
|---|---|---|---|
| `python -m maintai.train` (run `5969ae7c`) | 0.750 | 0.622 | 0.904 |
| `python -m maintai.train --C 0.01` (run `35e206e2`) | 0.691 | 0.653 | 0.908 |
| `python -m maintai.train --threshold 0.2` (run `612c5b17`) | **0.838** | 0.543 | 0.882 |
| `python -m maintai.train --model forest` (run `38564707`) | 0.728 | 0.562 | 0.886 |
| `python -m maintai.train --model forest --threshold 0.2` (run `95666406`) | 0.831 | 0.479 | 0.854 |

Baseline (« jamais de panne ») : recall 0.0, accuracy 0.864.

Quel run choisiriez-vous pour MaintAI, et pourquoi ? (Rappel : une panne manquée coûte plus cher qu'une fausse alerte.)

Le run `--threshold 0.2` (régression logistique, C = 1.0, seuil 0.2) : il a le meilleur recall (0.838). Sur les 136 pannes
du test, il en manque 22 au lieu de 34 au seuil 0.3. En échange, la precision baisse (0.622 → 0.543) : 96 fausses
alertes au lieu de 62, ce qui est acceptable puisqu'une inspection inutile coûte moins qu'une panne.
L'accuracy, la plus haute pour `--C 0.01` (0.908), n'est pas le bon critère : la baseline atteint déjà 0.864 sans
détecter une seule panne.

La forêt aléatoire n'est pas meilleure : au seuil 0.3, son recall (0.728) est inférieur à celui de la régression
logistique (0.750) ; au seuil 0.2, elle détecte une panne de moins (113 contre 114) et déclenche 27 fausses alertes
de plus (123 contre 96). Elle est aussi plus lourde (200 arbres) et moins explicable. Le seuil compte plus que le modèle.

Dans `mlflow ui`, ouvrez le modèle d'un run. Quelle version de scikit-learn est indiquée dans son `requirements.txt` ? Quel problème du TP4 cela règle-t-il ?

`scikit-learn==1.8.0`. Le fichier complet :

```
mlflow==3.18.0
numpy==2.4.4
pandas==3.0.2
psutil==7.2.2
pyarrow==26.0.1
pytest==9.1.1
scikit-learn==1.8.0
scipy==1.18.1
skops==0.16.0
```

Au TP4, un modèle `.joblib` ne se recharge de façon fiable qu'avec la même version de scikit-learn que celle de
l'entraînement. Il fallait figer les versions à la main dans `requirements.txt` et le wheel ne contenait pas le modèle
(seul `sklearn_version` était noté dans `model_info.json`). Maintenant, chaque modèle enregistré dans MLflow porte ses
versions exactes (`requirements.txt`, `conda.yaml`, `python_env.yaml`) : on sait recréer l'environnement qui le relit.

Où MLflow enregistre-t-il les runs sur votre disque ? Ces fichiers vont-ils dans Git ? Pourquoi ?

Dans le dossier où l'on lance l'entraînement (`TP\TP5`) :
- `mlflow.db` : base SQLite avec les expériences, les runs, leurs paramètres, métriques et tags ;
- `mlruns/1/models/m-<id>/artifacts/` : le modèle de chaque run (`model.skops`, `MLmodel`, `requirements.txt`,
  `conda.yaml`, `python_env.yaml`, `input_example.json`, `serving_input_example.json`).

Non, ils ne vont pas dans Git : le `.gitignore` exclut `mlflow.db` et `mlruns/`. Ce sont des fichiers générés,
binaires et qui grossissent à chaque run. Ils sont propres à chaque PC (deux membres créeraient deux bases en conflit)
et se régénèrent à partir du code et des données. Pour partager les runs dans une équipe, on utilise un serveur
MLflow commun, pas Git.

## 3. Sprint 2 : DVC

Contenu de `data/sensors.csv.dvc` après `dvc add data/sensors.csv` :

```
outs:
- md5: 73e0b7cb3c6f795c70c3ddf970b99c15
  size: 126815
  hash: md5
  path: sensors.csv
```

Comparez la valeur `md5` de ce fichier au paramètre `data_md5` de votre dernier run MLflow. Que constatez-vous ?

C'est la même valeur : `73e0b7cb3c6f795c70c3ddf970b99c15`. `file_md5()` de `tracking.py` calcule le même md5 que DVC,
donc chaque run MLflow pointe vers une version précise des données. Partant d'un run, on retrouve le commit Git dont
le reçu `.dvc` porte ce md5, puis le fichier avec `dvc checkout` ou `dvc pull`.

Pourquoi `data/sensors.csv` ne va pas dans Git, alors que `data/sensors.csv.dvc` y va ?

Git gère mal les gros fichiers (un CSV peut peser 100 Mo) et garde chaque version pour toujours : le dépôt gonflerait
à chaque nouvelle version des données. Le fichier reste donc hors de Git (`data/*.csv` dans le `.gitignore`). DVC le
copie dans son cache, puis dans le stockage, sous un nom qui est son md5. Git ne garde que le reçu `.dvc` (98 octets
de texte : md5, taille, chemin). Il est petit et lisible, se compare dans une pull request et suffit à retrouver
exactement le fichier.

Après `python -m maintai.dataset --n 8000 --seed 7`, que dit `dvc status` ?

```
data\sensors.csv.dvc:
	changed outs:
		modified:           data\sensors.csv
```

| Version | Commit Git (`git log --oneline`) | md5 (8 premiers caractères) | Nombre de lignes |
|---|---|---|---|
| v1 | `f90df13` Données v1 | `73e0b7cb` | 5000 |
| v2 | `cfa9616` Données v2 | `93fdeef2` | 8000 |

Revenez à la v1 (`git checkout <commit> -- data/sensors.csv.dvc`, puis `dvc checkout`). Combien de lignes contient `data/sensors.csv` ? Puis revenez à la v2.

```
> git checkout f90df13 -- data/sensors.csv.dvc & dvc checkout
M       data\sensors.csv
> python -c "import pandas as pd; print(len(pd.read_csv('data/sensors.csv')))"
5000
> git checkout HEAD -- data/sensors.csv.dvc & dvc checkout
M       data\sensors.csv
> python -c "import pandas as pd; print(len(pd.read_csv('data/sensors.csv')))"
8000
```

5000 lignes sur la v1, 8000 après le retour à la v2. Git choisit le reçu, DVC ramène le fichier correspondant depuis
son cache. Pendant le passage par la v1, `git status` montrait `M data/sensors.csv.dvc` (l'ancien reçu) : il n'a pas été
commité, `git checkout HEAD -- data/sensors.csv.dvc` l'a remis.

Supprimez `data/sensors.csv` et le dossier `.dvc/cache`, puis lancez `dvc pull`. Que se passe-t-il ?

```
> dvc pull
A       data\sensors.csv
1 file fetched and 1 file added
```

DVC lit le md5 dans le reçu (`93fdeef2…`), télécharge le fichier depuis le stockage
(`%USERPROFILE%\dvc-stockage`) dans le cache (`fetch`), puis le place dans `data/` (`checkout`). Le fichier revient avec
8000 lignes et le même md5 (`93fdeef2cac1893c4f720c16457eea75`), et `dvc status` répond « Data and pipelines are up to
date ». C'est ce que fait un coéquipier après `git clone` : le code vient de Git, les données du stockage.

Vérifié dans un clone neuf du dépôt du groupe : après `dvc pull`, le cache ne contient que la v2. Revenir à la v1 avec
`git checkout f90df13 -- data/sensors.csv.dvc` puis `dvc checkout` échoue (« missing-files ») et `data/sensors.csv`
disparaît : `dvc checkout` ne cherche que dans le cache local. Avec `dvc pull`, la v1 est téléchargée depuis le
stockage (« 1 file fetched »), on retrouve 5000 lignes, et ensuite `dvc checkout` suffit pour passer de v1 à v2.

## 4. Relier modèle et données

Entraînez un modèle sur la v2. Dans `mlflow ui`, comparez ce run à celui de la v1 avec les mêmes réglages :

Mêmes réglages : régression logistique, C = 1.0, seuil 0.3.

| Run | data_md5 (8 caractères) | n_train | recall | precision |
|---|---|---|---|---|
| v1 (`5969ae7c`) | `73e0b7cb` | 4000 | 0.750 | 0.622 |
| v2 (`05cb4a21`) | `93fdeef2` | 6400 | 0.741 | 0.650 |

Peut-on dire que le modèle v2 est « meilleur » ? Pourquoi faut-il être prudent en comparant deux runs entraînés sur des données différentes ?

Non. Le recall v2 est même un peu plus bas (0.741 contre 0.750) et la precision un peu plus haute (0.650 contre
0.622), mais on ne peut rien en conclure :
- les deux runs ne sont pas évalués sur le même jeu de test (1000 relevés et 136 pannes pour la v1, 1600 relevés et
  205 pannes pour la v2, avec un taux de panne de 13.6 % contre 12.8 %). Une métrique mesure le modèle *et* son jeu de
  test ;
- les écarts sont minuscules : sur la v1, une seule panne vaut 0.7 point de recall. Un autre découpage pourrait
  inverser le classement ;
- plus de données ne rend pas automatiquement un modèle meilleur.

Pour comparer deux modèles, il faut les évaluer sur les mêmes données de test (même `data_md5`), idéalement sur
plusieurs découpages (validation croisée). C'est justement ce que le `data_md5` de chaque run permet de vérifier.

## 5. Décision : l'ADR 004

Dans `docs/adr/004-choix-du-modele.md` : le modèle et le seuil retenus, à partir de votre tableau MLflow. Indiquez l'identifiant du run et le `data_md5` de la version des données utilisée.

Voir [`docs/adr/004-choix-du-modele.md`](docs/adr/004-choix-du-modele.md). En résumé :
- **régression logistique, C = 1.0, seuil d'alerte 0.2** ;
- run `612c5b17cf2b4808900bdb562d7503e0`, `data_md5` = `73e0b7cb3c6f795c70c3ddf970b99c15` (données v1) ;
- contrepartie acceptée : plus de fausses alertes (precision 0.543) ;
- vérifié sur la v2 : run `6232a7870fb94049b8a5ed54f19d9ed1`, `data_md5` = `93fdeef2…`, recall 0.824 (contre 0.741 au
  seuil 0.3).

## 6. Questions de compréhension

1. Quelle différence entre Git, DVC et MLflow ? Que versionne chacun ?
   **Git** versionne le code (`maintai/`, `tests/`, `pyproject.toml`, `requirements.txt`, les ADR) et les reçus `.dvc`
   des données. **DVC** versionne les fichiers de données eux-mêmes : il les garde hors de Git, dans un cache local puis
   un stockage partagé, nommés par leur md5. **MLflow** garde chaque entraînement (un run) : ses paramètres
   (model, C, threshold, n_train), la version des données (`data_md5`), ses métriques et le modèle avec les versions
   exactes des bibliothèques. Git dit *quel code*, DVC *quelles données*, MLflow *quel résultat*.
2. Pourquoi le stockage DVC est-il ajouté avec `--local` dans ce TP ? Que faudrait-il pour que tout le groupe partage les mêmes données ?
   Le stockage est un dossier de mon PC (`C:\Users\…\dvc-stockage`). Ce chemin n'a pas de sens pour les autres membres
   et contient un nom d'utilisateur. `--local` l'écrit dans `.dvc/config.local`, que Git ignore, au lieu de
   `.dvc/config`, qui est commité. Pour partager les données, il faut un stockage accessible par tous (S3, Google Drive,
   Azure Blob, serveur SSH, dossier réseau), déclaré **sans** `--local` (par exemple
   `dvc remote add -d stockage s3://maintai-data`) pour qu'il soit commité dans `.dvc/config`, les identifiants restant
   dans `config.local`. Ensuite chacun fait `dvc push` après un `dvc add` et `dvc pull` après un `git pull`.
3. Livrer un modèle, c'est trois choses (TP4). Lesquelles, et où sont-elles maintenant ?
   - **Le code** : dans Git (et le wheel du TP4).
   - **Le modèle** : dans MLflow, retrouvé par l'identifiant de son run (artefact `model.skops`).
   - **Les versions exactes des bibliothèques** : dans MLflow, le `requirements.txt` enregistré avec le modèle.

   Le TP5 ajoute une quatrième chose : **les données**, avec DVC (le reçu dans Git, le fichier dans le stockage), reliées
   au run par `data_md5`.

## 7. Le rendu Git

- Lien de la pull request : https://github.com/H20-sys/project/pull/4
- Le tag `tp5` existe sur GitHub : oui, sur `main`, sur le commit qui remet `TP/TP5` après la PR #4 (le tag `tp4` marque `main` avant le TP5)
- « Files changed » de la PR : 40 fichiers, tous dans `TP/TP5` ; aucun `mlflow.db`, `mlruns/`, `data/sensors.csv`,
  `.dvc/cache`, `.dvc/config.local`, `models/`, `dist/` ni `*.egg-info`.
- `git status` avant le commit : `mlflow.db`, `mlruns/`, `data/sensors.csv` ou `.dvc/cache` apparaissaient-ils ? **non** :
  `mlflow.db`, `mlruns/`, `models/` et `data/*.csv` sont exclus par le `.gitignore` du TP5 ; `.dvc/cache`, `.dvc/tmp` et
  `.dvc/config.local` par le `.dvc/.gitignore` créé par `dvc init`.

## 8. Ce qui reste flou

- Comment partager concrètement les runs MLflow dans le groupe : chacun a sa propre `mlflow.db`, il faudrait un serveur
  MLflow commun (`mlflow server` avec une base et un stockage d'artefacts partagés).
- Comment choisir le seuil de façon plus rigoureuse qu'à l'œil sur un tableau : chiffrer le coût d'une panne manquée et
  d'une fausse alerte, puis chercher le seuil qui minimise le coût total, sur plusieurs découpages.
