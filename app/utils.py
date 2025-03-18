from requests import get
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from typing import Annotated

security = HTTPBearer()

ISSUER = "https://<url_here>"
JWKS_URL = f"{ISSUER}/.well-known/openid-configuration/jwks"
jwks = get(JWKS_URL).json()


def validate_token(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
):
    try:
        unverified_header = jwt.get_unverified_header(credentials.credentials)
        kid = unverified_header["kid"]
        key = next((k for k in jwks["keys"] if k["kid"] == kid), None)

        if not key:
            raise HTTPException(status_code=401, detail="Invalid token")

        payload = jwt.decode(
            token=credentials.credentials,
            key=key,
            algorithms=["RS256"],
            audience="OptiMargin.Index.Data.Api",
            issuer=ISSUER,
            options={"verify_nbf": False},
        )
        return payload
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Invalid token: " + str(e.args[0]))
