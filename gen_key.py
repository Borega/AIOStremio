from cryptography.fernet import Fernet

key = Fernet.generate_key()

print("Encryption key:", key.decode())
