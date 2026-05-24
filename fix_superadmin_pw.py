import hashlib, secrets
pw = 'HydraAdmin2026!'
salt = secrets.token_hex(16)
h = hashlib.sha256((pw + salt).encode()).hexdigest()
print(f"UPDATE users SET password_hash='{salt}${h}' WHERE username='superadmin';")
