import os
from datetime import datetime, timedelta, timezone
import jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from .database import get_db
from .models import User

# PBKDF2-SHA256 is deliberately used here to avoid native bcrypt compatibility
# issues on low-cost Windows deployments while retaining salted password hashing.
pwd = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
bearer = HTTPBearer()
SECRET = os.getenv("JWT_SECRET", "development-secret-change-me")
def hash_password(v): return pwd.hash(v)
def verify_password(v, h): return pwd.verify(v, h)
def token_for(user):
    return jwt.encode({"sub": str(user.id), "role": user.role, "exp": datetime.now(timezone.utc)+timedelta(hours=12)}, SECRET, algorithm="HS256")
def current_user(creds: HTTPAuthorizationCredentials = Depends(bearer), db: Session = Depends(get_db)):
    try: payload = jwt.decode(creds.credentials, SECRET, algorithms=["HS256"])
    except jwt.PyJWTError: raise HTTPException(status_code=401, detail="Invalid or expired session")
    user = db.get(User, int(payload["sub"]))
    if not user or not user.active: raise HTTPException(status_code=401, detail="Account unavailable")
    return user
def allow(*roles):
    def check(user=Depends(current_user)):
        if user.role not in roles: raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This role cannot access this resource")
        return user
    return check
