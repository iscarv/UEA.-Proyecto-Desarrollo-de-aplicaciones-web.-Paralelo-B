from werkzeug.security import generate_password_hash

# Lista de contraseñas que quieras registrar
usuarios = ["juan123", "maria123", "carlos123", "rosa123"]

# Recorre cada contraseña y genera su hash
for pw in usuarios:
    hash_pw = generate_password_hash(pw) # Genera el hash seguro
    print(f"{pw} -> {hash_pw}")  # Muestra la contraseña original y el hash
