# Compte rendu · TP5 : suivre les entraînements (MLflow) et versionner les données (DVC)

**Groupe :** …  ·  **Membres :** …  ·  **Date :** 17/11/2026

> ⚠️ À supprimer avant le rendu : les valeurs chiffrées (recall, md5, commits, identifiants de run) sont des **exemples**. Remplace-les par tes vraies sorties de terminal et de `mlflow ui`.

---

## 1. Mise en place (dans `TP/TP5`)

Dernière ligne de `python -m pytest` après `pip install -r requirements.txt` et `pip install -e .` :

```
5 failed, 27 passed
```

Quels tests échouent, et pourquoi ?

Cinq tests échouent : ce sont les tests de `tests/test_tracking.py`. La fonction `log_run` n'est pas encore écrite : elle ne fait rien, ne crée aucun run et ne renvoie aucun identifiant.

Avant `pip install -e .`, où pointait le package `maintai` installé dans l'environnement ? Et après ?

Avant, il pointait vers le TP4. Après, il pointe vers `TP/TP5` : le code importé est bien celui du TP5.

## 2. Sprint 1 : MLflow

Votre fonction `log_run` (`maintai/tracking.py`) :

```python
def log_run(model, metrics, params, data_path, X_example) -> str:
    mlflow.set_experiment(EXPERIMENT)
    with mlflow.start_run() as run:
        mlflow.log_params(params)
        mlflow.log_param("data_md5", file_md5(data_path))
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
32 passed
```

Vos runs, relevés dans `mlflow ui` (mode « Model training ») :

| Commande | recall | precision | accuracy |
|---|---|---|---|
| `python -m maintai.train` | 0.71 | 0.83 | 0.86 |
| `python -m maintai.train --C 0.01` | 0.55 | 0.88 | 0.79 |
| `python -m maintai.train --threshold 0.2` | 0.92 | 0.71 | 0.84 |
| `python -m maintai.train --model forest` | 0.87 | 0.94 | 0.93 |
| `python -m maintai.train --threshold 0.3` (mon essai) | 0.81 | 0.80 | 0.85 |

Quel run choisiriez-vous pour MaintAI, et pourquoi ?

Je choisis `--threshold 0.2`. C'est le run qui a le meilleur recall (0.92). Une panne manquée coûte plus cher qu'une fausse alerte : on accepte donc davantage de fausses alertes (precision plus basse, 0.71) pour manquer le moins de pannes possible.

Quelle version de scikit-learn est indiquée dans le `requirements.txt` du modèle ? Quel problème du TP4 cela règle-t-il ?

`scikit-learn==1.8.0`. Au TP4, le modèle n'était pas livré avec ses versions : sur un autre poste, le résultat pouvait différer, voire le modèle ne pas se charger. Maintenant MLflow garde les versions exactes, on peut recréer le même environnement.

Où MLflow enregistre-t-il les runs sur votre disque ? Ces fichiers vont-ils dans Git ? Pourquoi ?

Dans `mlflow.db` et dans le dossier `mlruns/`. Non, ils ne vont pas dans Git : ce sont des fichiers binaires, lourds et régénérables. Le `.gitignore` les exclut.

## 3. Sprint 2 : DVC

Contenu de `data/sensors.csv.dvc` après `dvc add data/sensors.csv` :

```
outs:
- md5: 8f14e45fceea167a5a36dedd4bea2543
  size: 412987
  hash: md5
  path: sensors.csv
```

Comparez la valeur `md5` de ce fichier au paramètre `data_md5` de votre dernier run MLflow. Que constatez-vous ?

Les deux valeurs sont identiques : le run est relié à la version exacte des données utilisée pour l'entraînement.

Pourquoi `data/sensors.csv` ne va pas dans Git, alors que `data/sensors.csv.dvc` y va ?

Git gère mal les gros fichiers : il conserve chaque version pour toujours et le dépôt devient trop lourd. DVC stocke le fichier à part ; Git ne garde qu'un petit « reçu » de quelques lignes (le `.dvc`) qui pointe vers la bonne version.

Après `python -m maintai.dataset --n 8000 --seed 7`, que dit `dvc status` ?

```
data/sensors.csv.dvc
        changed outs:
                modified:           sensors.csv
```

| Version | Commit Git (`git log --oneline`) | md5 (8 premiers caractères) | Nombre de lignes |
|---|---|---|---|
| v1 | `a1b2c3d Données v1` | `8f14e45f` | 5000 |
| v2 | `e4f5g6h Données v2` | `c9f0f895` | 8000 |

Retour à la v1 puis à la v2 :

Après retour à la v1 : 5000 lignes. Après retour à la v2 : 8000 lignes.

Suppression de `data/sensors.csv` et de `.dvc/cache`, puis `dvc pull` :

DVC télécharge le fichier depuis le stockage, le remet dans le cache, puis le replace dans `data/sensors.csv`. Tout est restauré.

## 4. Relier modèle et données

| Run | data_md5 (8 caractères) | n_train | recall | precision |
|---|---|---|---|---|
| v1 | `8f14e45f` | 4000 | 0.71 | 0.83 |
| v2 | `c9f0f895` | 6400 | 0.78 | 0.86 |

Peut-on dire que le modèle v2 est « meilleur » ? Pourquoi faut-il être prudent ?

Pas forcément. Les deux modèles sont évalués sur des données différentes : la v2 contient plus de lignes et sa distribution peut avoir changé. Une hausse du recall peut venir des données (jeu de test plus facile) et non du modèle. Pour comparer équitablement, il faut le même jeu de test.

## 5. Décision : l'ADR 004

Voir `docs/adr/004-choix-du-modele.md`.

- Modèle : régression logistique, `C=1.0`
- Seuil : `threshold=0.2`
- Run retenu : `<identifiant du run>`
- Données : v2, `data_md5 = <8 caractères>`

## 6. Questions de compréhension

1. Quelle différence entre Git, DVC et MLflow ? Que versionne chacun ?
   - **Git** versionne le code, ainsi que le reçu `.dvc` des données.
   - **DVC** versionne les fichiers de données : le fichier est dans le stockage, le reçu dans Git.
   - **MLflow** versionne chaque entraînement : paramètres, métriques, modèle et versions des bibliothèques.

2. Pourquoi le stockage DVC est-il ajouté avec `--local` dans ce TP ? Que faudrait-il pour que tout le groupe partage les mêmes données ?

   `--local` écrit le chemin dans `.dvc/config.local`, fichier ignoré par Git. C'est normal : le chemin du dossier est propre à chaque poste. Pour partager, il faut un stockage commun (S3, Google Drive, serveur…), ajouté sans `--local` pour que la configuration soit versionnée.

3. Livrer un modèle, c'est trois choses (TP4). Lesquelles, et où sont-elles maintenant ?
   - Le **code** : dans Git (et dans le wheel du TP4).
   - Les **données** : dans DVC (reçu dans Git, fichier dans le stockage).
   - Le **modèle** : dans MLflow (un run, un identifiant, un `requirements.txt`).

## 7. Le rendu Git

- Lien de la pull request : …
- Le tag `tp5` existe sur GitHub : oui
- `git status` avant le commit : `mlflow.db`, `mlruns/`, `data/sensors.csv` ou `.dvc/cache` apparaissaient-ils ? non

## 8. Ce qui reste flou

…
