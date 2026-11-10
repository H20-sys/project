import pytest

VALID = {"temperature_c": 60.0, "vibration_mm_s": 2.0, "load_pct": 50.0, "runtime_hours": 5000}

CAS_REFUSES = [  # (description, url, corps, code attendu)
    ("champ manquant", "/v1/predict", {k: v for k, v in VALID.items() if k != "load_pct"}, 422),
    ("valeur absurde", "/v1/predict", {**VALID, "load_pct": 250}, 422),
    ("texte au lieu d'un nombre", "/v1/predict", {**VALID, "temperature_c": "chaud"}, 422),
    ("champ en trop", "/v1/predict", {**VALID, "admin": True}, 422),
    ("mauvaise route", "/v1/predicte", VALID, 404),
]


@pytest.mark.parametrize("description, url, corps, attendu", CAS_REFUSES, ids=[c[0] for c in CAS_REFUSES])
def test_requetes_refusees(client, description, url, corps, attendu):
    r = client.post(url, json=corps)
    assert r.status_code == attendu