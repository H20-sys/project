"""Authentification par clé API, transmise dans l'en-tête X-API-Key."""

import secrets

from fastapi import Header, HTTPException, status

from maintai.config import get_settings


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Refuse la requête si la clé est absente ou fausse."""
    expected = get_settings().api_key
    if expected is None:
        # Erreur de configuration du serveur, pas du client : 500, et un message qui dit quoi faire
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="La clé API du serveur n'est pas configurée : lancez uvicorn avec --env-file .env",
        )
    # compare_digest prend le même temps que la clé soit juste ou non (pas de fuite par la durée).
    # On compare des octets : sur des textes avec accents ("clé"), compare_digest plante (500 au lieu de 401)
    if x_api_key is None or not secrets.compare_digest(
        x_api_key.encode(), expected.encode()
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clé API absente ou invalide",
        )
