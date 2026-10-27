"""Chargement et découpage des données.

À vous d'écrire load_data() et split(). Les tests de tests/test_data.py disent ce qui est attendu.
"""
import pandas as pd
from sklearn.model_selection import train_test_split  # noqa: F401  (utile pour split)

from monprojet import config


def load_data(path=None) -> pd.DataFrame:
    """Lit le fichier CSV et renvoie un DataFrame.

    Attendu :
    - lire config.DATA_PATH (ou `path` s'il est donné) ;
    - si la colonne config.TARGET n'existe pas, lever une ValueError avec un message clair ;
    - retirer les lignes où la cible est manquante.

    Pistes : pd.read_csv, df.columns, df.dropna(subset=[...]).
    """
    if path is None:
        path = config.DATA_PATH
    df = pd.read_csv(path)
    if config.TARGET not in df.columns:
        raise ValueError(f"Colonne cible '{config.TARGET}' absente de {path}. Colonnes trouvées : {list(df.columns)}")
    return df.dropna(subset=[config.TARGET])

def feature_columns(df: pd.DataFrame) -> list:
    """Les colonnes d'entrée : celles de config.FEATURES, ou toutes sauf la cible et la date. (Fournie.)"""
    if config.FEATURES is not None:
        return list(config.FEATURES)
    excluded = {config.TARGET, config.TIME_COLUMN}
    return [c for c in df.columns if c not in excluded]


def split(df: pd.DataFrame):
    """Renvoie X_train, X_test, y_train, y_test.

    Attendu :
    - X = les colonnes de feature_columns(df) ; y = la colonne cible ;
    - si config.SPLIT == "random" : un découpage aléatoire de taille config.TEST_SIZE,
      avec la graine config.SEED, et stratifié sur y pour une classification ;
    - si config.SPLIT == "chronologique" : trier selon config.TIME_COLUMN et garder
      les lignes les plus récentes pour le test (le modèle apprend le passé, il est testé sur le futur).

    Pistes : train_test_split(..., test_size=..., random_state=..., stratify=...) ;
    pd.to_datetime(...).argsort() ; X.iloc[...].
    """
    X = df[feature_columns(df)]
    y = df[config.TARGET]

    if config.SPLIT == "random":
        stratify = y if config.TASK == "classification" else None
        return train_test_split(
            X, y, test_size=config.TEST_SIZE, random_state=config.SEED, stratify=stratify
        )

    if config.SPLIT == "chronologique":
        if config.TIME_COLUMN is None:
            raise ValueError("SPLIT = 'chronologique' demande une colonne de date : renseignez config.TIME_COLUMN")
        order = pd.to_datetime(df[config.TIME_COLUMN]).argsort().to_numpy()
        X, y = X.iloc[order], y.iloc[order]
        n_test = round(len(df) * config.TEST_SIZE)
        return X.iloc[:-n_test], X.iloc[-n_test:], y.iloc[:-n_test], y.iloc[-n_test:]

    raise ValueError(f"config.SPLIT inconnu : {config.SPLIT!r} (attendu 'random' ou 'chronologique')")
