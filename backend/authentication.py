"""
authentication.py

This file will contain:
- Password hashing
- Password verification
- JWT token creation
- JWT token verification
- User registration
- User login
- Current-user authentication
"""

import os

from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from jose import JWTError, jwt
from passlib.context import CryptContext

from database import SessionLocal
from models import User


# ==========================================================
# Load Environment Variables
# ==========================================================

load_dotenv()


# ==========================================================
# Authentication Configuration
# ==========================================================

SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    raise ValueError("SECRET_KEY is not found in the .env file.")


ALGORITHM = os.getenv("ALGORITHM", "HS256")

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
)


# ==========================================================
# Password Hashing Configuration
# ==========================================================

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

# ==========================================================
# Password Hashing
# ==========================================================

def hash_password(password: str) -> str:
    """
    Convert a plain password into a secure hash.
    """

    return pwd_context.hash(password)


# ==========================================================
# Password Verification
# ==========================================================

def verify_password(
    plain_password: str,
    hashed_password: str
) -> bool:
    """
    Check whether a plain password matches
    the stored hashed password.
    """

    return pwd_context.verify(
        plain_password,
        hashed_password
    )

# Temporarily Add

#if __name__ == "__main__":

   # password = "Test@123"

    #hashed = hash_password(password)

    #print("Original password:", password)
    # print("Hashed password:", hashed)

    #print(
     #   "Correct password:",
      #  verify_password("Test@123", hashed)
    #)

    #print(
     #   "Wrong password:",
      #  verify_password("WrongPassword", hashed)
    #)



    # ==========================================================
# Create JWT Access Token
# ==========================================================

def create_access_token(
    data: dict,
    expires_minutes: int | None = None
) -> str:
    """
    Create a JWT access token.

    data:
        Information that will be stored inside the token.

    expires_minutes:
        Number of minutes before the token expires.
    """

    # Make a copy so we don't modify the original dictionary
    to_encode = data.copy()

    # Use configured expiration time if one wasn't provided
    if expires_minutes is None:
        expires_minutes = ACCESS_TOKEN_EXPIRE_MINUTES

    # Calculate token expiration time
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes
    )

    # Add expiration time to the token data
    to_encode["exp"] = expire

    # Create and return JWT token
    encoded_jwt = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return encoded_jwt

# ==========================================================
# Decode and Verify JWT Token
# ==========================================================

def decode_access_token(token: str) -> dict:
    """
    Decode and verify a JWT access token.

    Returns the token data if the token is valid.
    Raises ValueError if the token is invalid.
    """

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        return payload

    except JWTError:
        raise ValueError("Invalid or expired token.")
# =================================
# Temporarily check 
# =================================
# if __name__ == "__main__":

#     Password test
#     password = "Test@123"

#     hashed = hash_password(password)

#     print("Original password:", password)
#     print("Hashed password:", hashed)

#     print(
#         "Correct password:",
#         verify_password("Test@123", hashed)
#     )

#     print(
#         "Wrong password:",
#         verify_password("WrongPassword", hashed)
#     )

#     JWT test
#     token = create_access_token(
#         {"sub": "1"}
#     )

#     print("JWT Token:")
#     print(token)

#     Decode JWT token
#     payload = decode_access_token(token)

#     print("Decoded JWT data:")
#     print(payload)