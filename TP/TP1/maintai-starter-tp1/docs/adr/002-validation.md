# ADR 002 : validation des relevés et comportement sans modèle

Date : 27/10/2026 · Auteurs : Soufiane Jaouhari, Hiba Chefchaouni Moussaoui, Khalid Sammar, Kimath Elmer (Grp 2)

## Contexte
L'API MaintAI reçoit des relevés de capteurs envoyés par d'autres programmes (tableau de bord, application mobile, système de l'atelier). Une valeur impossible (capteur défaillant, erreur de saisie) ne doit jamais atteindre le modèle, mais une machine réelle en mauvais état doit toujours être acceptée, puisque c'est justement elle qu'il faut signaler. Il faut aussi décider du comportement de l'API quand le fichier du modèle (`models/model.joblib`) est absent.

## Décision 1 : les bornes de chaque variable

Les bornes sont **physiques** : ce qu'un moteur réel peut afficher. Elles ne sont **pas** le minimum et le maximum de `sensors.csv` (température environ 25 à 95 °C, charge 20 à 100 %, 0 à 20 000 h), qui refuseraient des machines réelles un peu plus chaudes ou plus anciennes que celles des données.

| Variable | Type | Min | Max | Justification |
|---|---|---|---|---|
| `temperature_c` | float | -40 | 150 | -40 °C : atelier non chauffé ou site extérieur en hiver, limite basse des capteurs industriels. 150 °C : au-delà, l'isolation des bobinages (classe F, 155 °C) est détruite ; une telle valeur vient d'un capteur en panne, pas d'un moteur qui tourne. |
| `vibration_mm_s` | float | 0 | 100 | Une vitesse de vibration efficace (RMS) est une amplitude : elle ne peut pas être négative. La norme ISO 10816 classe une machine comme « dangereuse » dès environ 7 à 11 mm/s, et les capteurs industriels mesurent couramment jusqu'à 50 ou 100 mm/s. Avec 100, une machine en très mauvais état est acceptée (et déclenche une alerte) au lieu d'être refusée. |
| `load_pct` | float | 0 | 150 | 0 % : machine à vide. Au-dessus de 100 %, une surcharge temporaire est physiquement possible (facteur de service, pics de charge), et refuser 110 % reviendrait à refuser les relevés les plus dangereux. Au-delà de 150 %, la protection thermique coupe le moteur en quelques secondes : ce n'est pas une valeur de fonctionnement. |
| `runtime_hours` | float | 0 | 300 000 | Un compteur cumulé ne peut pas être négatif. Une année en 24 h/24 compte 8 760 h ; 300 000 h font environ 34 ans sans arrêt, au-delà de la durée de vie d'un moteur industriel (20 à 30 ans). Le type est `float`, car un compteur peut afficher 15 000,5 h. |

## Décision 2 : modèle absent, répondre 503 ou refuser de démarrer ?

### Options étudiées
1. **Démarrer quand même, répondre 503 sur `/v1/predict`** (et `"model_loaded": false` sur `/health`).
   - Avantages : `/health` et `/docs` restent accessibles, ce qui permet de diagnostiquer le problème. Le client reçoit un code précis (« service indisponible, réessayez plus tard ») et un message qui dit quoi faire. Le comportement se teste (`test_503_when_model_missing`).
   - Ce qu'on perd : l'API semble « en marche » alors qu'elle ne sait pas prédire. Un déploiement peut paraître réussi alors qu'il est inutilisable, et l'erreur n'apparaît qu'à la première requête ou en lisant `/health`.
2. **Refuser de démarrer** (lever l'erreur dans `lifespan`).
   - Avantages : l'erreur est visible immédiatement, au déploiement, et il n'existe jamais d'API à moitié fonctionnelle.
   - Ce qu'on perd : plus de `/health` ni de `/docs` pour comprendre ce qui se passe. Les clients reçoivent « connexion refusée », moins explicite qu'un 503 avec un message. Dans un conteneur, le processus redémarre en boucle.

### Décision
Option 1 : l'API démarre et répond **503** tant que le modèle manque. La raison principale : l'absence de modèle n'est pas un bug du code (cas du 500) mais une ressource indisponible. Le 503 et son message (« lancez `python -m maintai.train`, puis redémarrez l'API ») disent au client et à l'opérateur ce qui se passe et quoi faire, et `/health` le signale aussi.

## Conséquences
- Les clients n'envoient jamais de valeur impossible au modèle : une erreur 422 indique le champ fautif et la borne dépassée, et ces bornes apparaissent dans `/docs`.
- Le modèle a été entraîné sur une plage plus étroite (charge 20 à 100 %, 0 à 20 000 h) que les bornes acceptées. Hors de cette plage, il extrapole, et ses probabilités sont moins fiables : à surveiller, et à couvrir avec des données réelles.
- Un déploiement ne doit pas se contenter de vérifier que `/health` répond 200 : il doit aussi vérifier `"model_loaded": true`.
- Si les capteurs changent (autre unité, autre type de machine), les bornes de `schemas.py` et cet ADR sont à revoir ensemble.
