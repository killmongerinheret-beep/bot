import hashlib, secrets

NEW_PASSWORD = 'HydraAdmin2026!'
salt = secrets.token_hex(16)
hashed = hashlib.sha256((NEW_PASSWORD + salt).encode()).hexdigest()
pw_hash = f"{salt}${hashed}"
print(f"UPDATE users SET password_hash='{pw_hash}' WHERE id=6;")
