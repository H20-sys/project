"""Activité 1 (S5) : casser son API. Chaque cas est une requête qui doit être refusée."""

import pytest

# La clé des tests (conftest.py) : inutile en TP1, nécessaire en TP2
HEADERS = {"X-API-Key": "test-key"}
VALID = {
    "temperature_c": 60.0,
    "vibration_mm_s": 2.0,
    "load_pct": 50.0,
    "runtime_hours": 5000,
}
SANS_CHARGE = {k: v for k, v in VALID.items() if k != "load_pct"}

CAS_REFUSES = [
    # (description, url, corps, code attendu)
    ("champ manquant", "/v1/predict", SANS_CHARGE, 422),
    ("valeur absurde", "/v1/predict", {**VALID, "load_pct": 250}, 422),
    (
        "texte au lieu d'un nombre",
        "/v1/predict",
        {**VALID, "temperature_c": "chaud"},
        422,
    ),
    ("champ en trop", "/v1/predict", {**VALID, "humidite_pct": 40}, 422),
    ("mauvaise route", "/v1/predicte", VALID, 404),
    # Trouvé à l'étape 4 : accepté (200) avant strict=True dans schemas.py
    (
        "booléen au lieu d'un nombre",
        "/v1/predict",
        {**VALID, "runtime_hours": True},
        422,
    ),
]


@pytest.mark.parametrize("description, url, corps, attendu", CAS_REFUSES)
def test_requete_refusee(client, description, url, corps, attendu):
    assert client.post(url, json=corps, headers=HEADERS).status_code == attendu


def test_cle_avec_accent_donne_401(client):
    # Trouvé en TP2 : compare_digest plantait sur une clé avec accent (500 au lieu de 401)
    r = client.post("/v1/predict", json=VALID, headers={"X-API-Key": "clé".encode()})
    assert r.status_code == 401
