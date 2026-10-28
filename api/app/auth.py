from typing import Annotated, Any, Protocol

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool


class User(BaseModel):
    id: str
    username: str
    email: str | None
    name: str | None
    roles: list[str]


class SigningKeys(Protocol):
    def get_signing_key_from_jwt(self, token: str) -> jwt.PyJWK: ...


class TokenVerifier:
    """Accepts Keycloak access tokens: signature from the realm's keys, issuer, audience, expiry."""

    def __init__(
        self,
        issuer: str,
        audience: str,
        jwks_url: str | None = None,
        keys: SigningKeys | None = None,
    ) -> None:
        self.issuer = issuer
        self.audience = audience
        self._keys = keys or jwt.PyJWKClient(
            jwks_url or f"{issuer}/protocol/openid-connect/certs", cache_keys=True, lifespan=600
        )

    async def verify(self, token: str) -> User:
        # The key lookup is a blocking HTTP call the first time; keys are cached afterwards.
        key = await run_in_threadpool(self._keys.get_signing_key_from_jwt, token)
        claims: dict[str, Any] = jwt.decode(
            token,
            key.key,
            algorithms=["RS256"],
            audience=self.audience,
            issuer=self.issuer,
            options={"require": ["exp", "iss", "sub", "aud"]},
        )
        return User(
            id=claims["sub"],
            username=claims.get("preferred_username", claims["sub"]),
            email=claims.get("email"),
            name=claims.get("name"),
            roles=claims.get("realm_access", {}).get("roles", []),
        )


bearer = HTTPBearer(auto_error=False)


async def current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> User:
    challenge = {"WWW-Authenticate": "Bearer"}
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sign in required.", headers=challenge)
    verifier: TokenVerifier = request.app.state.auth
    try:
        return await verifier.verify(credentials.credentials)
    except jwt.PyJWKClientConnectionError as error:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "The sign-in service is unreachable."
        ) from error
    except jwt.PyJWTError as error:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, f"Invalid token: {error}", headers=challenge
        ) from error


CurrentUser = Annotated[User, Depends(current_user)]
