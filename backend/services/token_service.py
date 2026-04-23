import secrets
import hashlib


# -------------------
# 1. Token utils
# -------------------
def generate_token(candidate_id: str) -> str:
    random_part = secrets.token_hex(16)
    token       = hashlib.sha256(f"{candidate_id}{random_part}".encode()).hexdigest()[:40]
    return token
