import hashlib, secrets

def make_hash(password):
    salt = secrets.token_hex(16)
    hashed = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}${hashed}"

creds = [
    (10, 'bigbus',               'Big bus',              'bigbus@hydrabot.it',                'Bigbus2026!'),
    (9,  'Italypass',            'Italy pass',           'Italypass@hydrabot.it',             'Italypass2026!'),
    (12, 'Bot123',               'Mahabur',              'Bot123@hydrabot.it',                'Mahabur2026!'),
    (8,  'Tourguides',           'Tour_guides',          'Tourguides@hydrabot.it',            'Tourguides2026!'),
    (3,  'vatican_bot_agency_1', 'Vatican Bot Agency 1', 'vatican_bot_agency_1@agency.local', 'Vatican2026!'),
    (4,  'wondersofrome',        'Vatican Bot Agency 2', 'vatican_bot_agency_2@agency.local', 'Wonders2026!'),
    (11, 'wondersofrome123',     'Wondersofrome',        'wondersofrome123@hydrabot.it',      'Wonders2026!'),
]

# Write SQL file
with open('reset_passwords.sql', 'w') as f:
    for uid, uname, agency, email, pw in creds:
        h = make_hash(pw)
        f.write(f"UPDATE users SET password_hash='{h}' WHERE id={uid};\n")

print("reset_passwords.sql written.\n")

print(f"{'Agency':<25} {'Username':<22} {'Password':<18} {'Email':<38} Login URL")
print('-'*115)
for uid, uname, agency, email, pw in creds:
    print(f"{agency:<25} {uname:<22} {pw:<18} {email:<38} https://hydrabot.it")
print()
