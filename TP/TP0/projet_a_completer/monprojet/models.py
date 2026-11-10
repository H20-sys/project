"""Les modèles à comparer.

À vous d'écrire candidates(). Les tests de tests/test_models.py disent ce qui est attendu.
"""
from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.ensemble import (HistGradientBoostingClassifier, HistGradientBoostingRegressor,
                              RandomForestClassifier, RandomForestRegressor)
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor

from monprojet import config


def candidates() -> dict:
    """Renvoie un dictionnaire {nom: modèle scikit-learn non entraîné}.

    Attendu :
    - le PREMIER modèle est la baseline : le modèle le plus simple possible
      (DummyClassifier pour une classification, DummyRegressor pour une régression) ;
    - au moins trois vrais modèles ensuite, adaptés à config.TASK ;
    - random_state=config.SEED pour les modèles qui ont du hasard.

    Pistes : sklearn.dummy, sklearn.linear_model, sklearn.ensemble, sklearn.neighbors, sklearn.tree.
    """
    seed = config.SEED

    if config.TASK == "classification":
        # class_weight="balanced" : la classe rare (les pannes) pèse autant que l'autre,
        # sinon les modèles prédisent presque toujours « pas de panne » et le rappel s'effondre.
        return {
            "baseline": DummyClassifier(strategy="most_frequent"),
            "regression_logistique": LogisticRegression(class_weight="balanced", max_iter=1000),
            "arbre_de_decision": DecisionTreeClassifier(max_depth=5, class_weight="balanced",
                                                        random_state=seed),
            "foret_aleatoire": RandomForestClassifier(n_estimators=200, class_weight="balanced",
                                                      random_state=seed),
            "gradient_boosting": HistGradientBoostingClassifier(class_weight="balanced",
                                                                random_state=seed),
        }

    if config.TASK == "regression":
        return {
            "baseline": DummyRegressor(strategy="mean"),
            "ridge": Ridge(),
            "arbre_de_decision": DecisionTreeRegressor(max_depth=5, random_state=seed),
            "foret_aleatoire": RandomForestRegressor(n_estimators=200, random_state=seed),
            "gradient_boosting": HistGradientBoostingRegressor(random_state=seed),
        }

    raise ValueError(f"config.TASK inconnu : {config.TASK!r} (attendu 'classification' ou 'regression')")
