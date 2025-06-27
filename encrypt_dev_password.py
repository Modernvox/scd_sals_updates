# encrypt_dev_password.py

from config import _FERNET as f

# Replace with your chosen dev password:
plain = b"LetMeIn"

# Encrypt and print the blob
encrypted = f.encrypt(plain).decode("utf-8")
print(encrypted)
