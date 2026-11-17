# ADR 004 : choix du modèle et du seuil d'alerte de MaintAI

Date : 17/11/2026 · Auteurs : Soufiane Jaouhari, Hiba Chefchaouni Moussaoui, Khalid Sammar, Kimath Elmer (Grp 2)

## Contexte
MaintAI doit prévenir la maintenance avant qu'une machine tombe en panne. Une panne manquée (arrêt de production,
réparation lourde) coûte bien plus cher qu'une fausse alerte (une inspection pour rien) : **le recall est la métrique
prioritaire**, la precision ne vient qu'ensuite. Jusqu'au TP4, chaque entraînement écrasait le précédent ; depuis le TP5,
chaque réglage est un run MLflow relié à sa version des données (`data_md5`), ce qui permet de comparer et de justifier.

## Options étudiées
Runs MLflow de l'expérience `maintai`, tous sur les **mêmes données v1** (5000 relevés, `data_md5` = `73e0b7cb…`,
jeu de test : 1000 relevés dont 136 pannes). Baseline « jamais de panne » : recall 0.0, accuracy 0.864.

| Option | Run MLflow | recall | precision | accuracy | pannes manquées | fausses alertes |
|---|---|---|---|---|---|---|
| A. logreg, C=1.0, seuil 0.3 (TP4) | `5969ae7c` | 0.750 | 0.622 | 0.904 | 34 | 62 |
| B. logreg, C=0.01, seuil 0.3 | `35e206e2` | 0.691 | 0.653 | 0.908 | 42 | 50 |
| **C. logreg, C=1.0, seuil 0.2** | **`612c5b17`** | **0.838** | **0.543** | 0.882 | **22** | 96 |
| D. forêt aléatoire, seuil 0.3 | `38564707` | 0.728 | 0.562 | 0.886 | 37 | 77 |
| E. forêt aléatoire, seuil 0.2 | `95666406` | 0.831 | 0.479 | 0.854 | 23 | 123 |

1. **A (statu quo du TP4)** : bon équilibre, la meilleure accuracy à C=1 ; mais une panne sur quatre est manquée.
2. **B (plus de régularisation)** : la meilleure precision et accuracy, mais le plus mauvais recall : écarté.
3. **C (seuil abaissé à 0.2)** : le meilleur recall ; 12 pannes manquées en moins que A, au prix de 34 fausses alertes de plus.
4. **D et E (forêt aléatoire)** : à seuil égal, la forêt ne fait pas mieux que la régression logistique
   (D < A et E ≤ C en recall) et produit nettement plus de fausses alertes (E : 123 contre 96 pour C). Elle est aussi
   plus lourde (200 arbres) et moins lisible. Plus complexe ne veut pas dire meilleure : écartée.

## Décision
**Régression logistique, C = 1.0, seuil d'alerte 0.2** (option C).

- Run retenu : `612c5b17cf2b4808900bdb562d7503e0`
- Données : `data_md5` = `73e0b7cb3c6f795c70c3ddf970b99c15` (v1, 5000 relevés, commit `f90df13` « Données v1 »)
- Pour retrouver ces données : `git checkout f90df13 -- data/sensors.csv.dvc` puis `dvc checkout` (ou `dvc pull` sur un autre PC)
- Versions exactes : le `requirements.txt` du modèle dans MLflow (scikit-learn==1.8.0, numpy==2.4.4, pandas==3.0.2)

Raison principale : c'est le meilleur recall mesuré (0.838) ; le seul concurrent proche (forêt, seuil 0.2) détecte une
panne de moins et déclenche 27 fausses alertes de plus.

Vérification sur les données v2 (8000 relevés, `data_md5` = `93fdeef2cac1893c4f720c16457eea75`) : même réglage,
run `6232a7870fb94049b8a5ed54f19d9ed1`, recall 0.824, precision 0.567, contre recall 0.741 au seuil 0.3
(run `05cb4a21`). Le choix du seuil 0.2 tient sur la nouvelle version des données.

En production : `MAINTAI_THRESHOLD=0.2`.

## Conséquences
- **Ce que nous acceptons en échange** : plus de fausses alertes. La precision passe de 0.622 à 0.543 : près d'une
  alerte sur deux (96 sur 210) déclenche une inspection pour rien, et l'accuracy baisse (0.904 → 0.882).
  Il faut que l'équipe de maintenance l'accepte, sinon elle finira par ignorer les alertes.
- **Facilité** : modèle simple, rapide, explicable (un coefficient par capteur) ; le choix est traçable de bout en bout
  (run MLflow → `data_md5` → reçu `.dvc` dans Git → fichier dans le stockage DVC).
- **À surveiller** : la dérive des données. Si la distribution des capteurs change, réentraîner sur la nouvelle version
  (enregistrée avec DVC) et comparer les runs **sur un même jeu de test** avant de changer de modèle.
- **À revoir** : le seuil a été choisi sur un seul découpage test (136 pannes : une panne vaut 0.7 point de recall).
  Une validation croisée, ou un coût chiffré par panne manquée et par fausse alerte, affinerait le choix du seuil.
