from werkzeug.security import generate_password_hash

# Lista de contraseñas que quieras registrar
usuarios = ["juan123", "maria123", "carlos123", "rosa123"]

for pw in usuarios:
    hash_pw = generate_password_hash(pw)
    print(f"{pw} -> {hash_pw}")
