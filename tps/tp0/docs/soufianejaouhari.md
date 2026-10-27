# Compte rendu individuel — Projet à compléter

Nom : Soufiane Jaouhari
Date : 27/10/2026
Projet : Prédiction des pannes de machines

## 1. Objectif du TP

Ce TP consiste à compléter un projet Python fourni avec sa structure
et ses tests, pour entraîner et comparer plusieurs modèles de machine learning.

L'objectif est de prédire la variable `failure` (1 = panne) à partir de
quatre mesures prises sur les machines : température, vibrations, charge
et heures de fonctionnement. Il faut ensuite retenir le modèle qui détecte
le mieux les pannes.

Le travail est terminé quand les huit tests passent et que le meilleur
modèle bat la baseline sur la métrique principale, le recall.

## 2. Ma contribution personnelle

Avec une aide guidée, j'ai complété les fonctions `load_data()` et `split()`
pour charger, nettoyer et découper les données.

J'ai ensuite écrit `candidates()`, qui définit la baseline et quatre modèles
de classification, puis `evaluate()` et `main()`, qui entraînent les modèles,
comparent leurs scores et sauvegardent le meilleur.

J'ai vérifié que les huit tests passent, lancé l'entraînement, analysé
les résultats, puis publié le projet sur le dépôt GitHub.

## 3. Fonctionnement du projet

Le programme suit plusieurs étapes :

1. `load_data()` lit le fichier CSV, vérifie que la colonne cible existe
   et supprime les lignes dont la cible est manquante.
2. `split()` sépare les données en un jeu d'entraînement et un jeu de test.
3. `build_preprocessing()` (fournie) prépare les colonnes : valeurs manquantes
   remplacées par la médiane, puis mise à l'échelle des nombres.
4. `candidates()` renvoie la baseline et les modèles à comparer.
5. `main()` entraîne chaque modèle, et `evaluate()` calcule ses scores
   sur le jeu de test.
6. `main()` classe les modèles selon le recall, sauvegarde le meilleur
   dans `models/model.joblib` et tous les scores dans `models/metrics.json`.

Commandes, depuis la racine du projet :

```powershell
.venv\Scripts\Activate.ps1
python -m pytest            # lance les 8 tests
python -m monprojet.train   # entraîne et compare les modèles
```

## 4. Données utilisées

Le fichier utilisé est `data/exemple_pannes.csv`.
Il contient 5 000 lignes et aucune valeur manquante :
aucune ligne n'est supprimée au nettoyage.

| Colonne | Rôle | Min | Moyenne | Max |
|---|---|---:|---:|---:|
| `temperature_c` | entrée | 35,8 | 64,8 | 92,6 |
| `vibration_mm_s` | entrée | 0,02 | 3,00 | 22,23 |
| `load_pct` | entrée | 20,0 | 60,4 | 100,0 |
| `runtime_hours` | entrée | 5 | 15 002 | 29 999 |
| `failure` | cible | 0 | — | 1 |

Les classes sont déséquilibrées : 4 122 lignes sans panne (82,4 %)
et 878 pannes (17,6 %).

Le découpage est aléatoire et stratifié, avec une graine fixée à 42 :

| Jeu | Lignes | Pannes | Taux de panne |
|---|---:|---:|---:|
| Entraînement (80 %) | 4 000 | 702 | 17,6 % |
| Test (20 %) | 1 000 | 176 | 17,6 % |

## 5. Modèles comparés

| Modèle | Classe scikit-learn | Réglages |
|---|---|---|
| Baseline | `DummyClassifier` | prédit toujours « pas de panne » |
| Régression logistique | `LogisticRegression` | `class_weight="balanced"` |
| Arbre de décision | `DecisionTreeClassifier` | `max_depth=5`, `class_weight="balanced"` |
| Forêt aléatoire | `RandomForestClassifier` | 200 arbres, `class_weight="balanced"` |
| Gradient boosting | `HistGradientBoostingClassifier` | `class_weight="balanced"` |

Les modèles qui ont une part de hasard utilisent `random_state=42`.

L'option `class_weight="balanced"` donne autant de poids aux pannes,
qui sont rares, qu'aux autres lignes. Sans elle, la régression logistique
ne détecte que 57,4 % des pannes au lieu de 84,7 %.

## 6. Résultats

Les huit tests automatisés du projet passent.

L'entraînement a produit les résultats suivants sur le jeu de test :

| Modèle | Recall | Accuracy | Precision | F1 |
|---|---:|---:|---:|---:|
| Baseline | 0,000 | 0,824 | 0,000 | 0,000 |
| **Régression logistique** | **0,847** | 0,839 | 0,527 | 0,649 |
| Gradient boosting | 0,767 | 0,863 | 0,584 | 0,663 |
| Arbre de décision | 0,722 | 0,825 | 0,502 | 0,592 |
| Forêt aléatoire | 0,540 | 0,882 | 0,720 | 0,617 |

Sur les 176 pannes du jeu de test :

| Modèle | Pannes détectées | Pannes manquées | Fausses alertes |
|---|---:|---:|---:|
| Baseline | 0 | 176 | 0 |
| Régression logistique | 149 | 27 | 134 |
| Gradient boosting | 135 | 41 | 96 |
| Arbre de décision | 127 | 49 | 126 |
| Forêt aléatoire | 95 | 81 | 37 |

Le modèle retenu est la régression logistique, car elle obtient
le meilleur recall : 84,7 %.

Elle dépasse la baseline de 84,7 points de pourcentage en recall.
La baseline ne détecte aucune panne, même si son accuracy
atteint 82,4 %.

## 7. Analyse des résultats

Le recall mesure la proportion de pannes réelles détectées.
Il est prioritaire dans ce projet, car une panne qui passe inaperçue
coûte plus cher qu'une inspection inutile.

La régression logistique détecte 149 pannes sur 176. Sa precision
de 52,7 % montre cependant qu'environ une alerte sur deux est fausse
(134 fausses alertes).

Le gradient boosting offre un compromis : il détecte un peu moins
de pannes (135), mais avec moins de fausses alertes (96),
et il a le meilleur score F1 (0,663).

La forêt aléatoire fait le choix inverse. Elle a la meilleure precision
(72,0 %) et la meilleure accuracy (88,2 %), mais elle manque 81 pannes,
soit presque la moitié.

Le choix du modèle dépend donc du coût d'une panne manquée
par rapport au coût d'une fausse alerte.

## 8. Difficultés personnelles rencontrées

_[À compléter : ce qui vous a posé problème pendant le TP et comment
vous l'avez résolu.]_

## 9. Ce que je retiens

Il faut toujours comparer un modèle à une baseline : sans elle,
82,4 % d'accuracy pourrait sembler un bon résultat, alors que
ce modèle ne détecte aucune panne.

La métrique doit être choisie selon le coût des erreurs.
Quand une classe est rare, l'accuracy ne suffit pas.

Pondérer les classes change fortement le comportement des modèles :
le recall de la régression logistique passe de 57,4 % à 84,7 %.

## 10. Limites et améliorations

L'évaluation repose sur un seul découpage, avec seulement 176 pannes
dans le jeu de test. Une validation croisée permettrait de vérifier
que l'écart entre les modèles est stable.

Les 134 fausses alertes pourraient être réduites en ajustant le seuil
de décision du modèle (`predict_proba`) au lieu du seuil de 0,5 par défaut.

Les réglages des modèles n'ont pas été optimisés.
Une recherche d'hyperparamètres (`GridSearchCV`) pourrait améliorer les scores.

Le modèle retenu manque encore 15,3 % des pannes.
Une évaluation sur des données réelles serait nécessaire
avant une utilisation en production.
