from fastapi import Depends, HTTPException, Header
from jose import jwt, jwk
import requests

# Clerk Config
CLERK_JWT_ISSUER = "https://trusting-ant-47.clerk.accounts.dev"
CLERK_JWT_AUDIENCE = "https://upcyclica.vercel.app/"  # Use your actual frontend URL in prod
CLERK_JWT_KEY_URL = f"{CLERK_JWT_ISSUER}/.well-known/jwks.json"

# Load JWKS from Clerk
JWKS = requests.get(CLERK_JWT_KEY_URL).json()

# Helper: Extract matching public key from JWKS
def get_public_key(token):
    headers = jwt.get_unverified_header(token)
    for key in JWKS["keys"]:
        if key["kid"] == headers["kid"]:
            return jwk.construct(key)
    raise HTTPException(status_code=401, detail="Public key not found")

# Auth Dependency
def get_current_user(authorization: str = Header(...)):
    try:
        token = authorization.replace("Bearer ", "")
        public_key = get_public_key(token)

        # Decode and verify the JWT
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience=CLERK_JWT_AUDIENCE,
            issuer=CLERK_JWT_ISSUER,
        )
        return payload["sub"]  # Clerk User ID
    except Exception as e:
        print("JWT decode error:", e)
        raise HTTPException(status_code=401, detail="Invalid or expired token")
