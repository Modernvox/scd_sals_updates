from cryptography.fernet import Fernet
import os

def get_machine_key():
    key_path = os.path.join(os.path.dirname(__file__), 'fernet.key')
    if not os.path.exists(key_path):
        key = Fernet.generate_key()  # Generate valid 32-byte key
        with open(key_path, 'wb') as f:
            f.write(key)
    with open(key_path, 'rb') as f:
        key = f.read()
        try:
            Fernet(key)  # Validate key
        except ValueError:
            key = Fernet.generate_key()  # Regenerate if invalid
            with open(key_path, 'wb') as f:
                f.write(key)
        return Fernet(key)

if __name__ == "__main__":
    fernet = get_machine_key()
    keys = {
        'STRIPE_PUBLIC_KEY': 'pk_live_51RJl1aJ7WrcpTNl6HDujxtz6FKIENvdxe4YoRDOqjaeVrqhrT2O6l0izKPrZklC2PharatHSFvwRgGLZsAl3vGDl00KQmWKIY5',
        'STRIPE_SECRET_KEY': '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',
        'STRIPE_WEBHOOK_SECRET': 'whsec_qsaErZXCQiYBsmkxfSOAoKFzN71NxN58',
        'API_TOKEN': '68cd22fe-d525-47c8-9d46-409bfe1f817f',
        'SECRET_KEY': '57f2c8d4-3eaf-48a1-9c6b-2f1d9b7c0e13',
        'DEV_OVERRIDE_SECRET': 'letmein',
        'NGROK_AUTH_TOKEN': '2whl3YAMUCIDAzklvOB675SqKwX_54bn6nhKxPjtD8s9C2mgA'
    }
    for key, value in keys.items():
        encrypted = fernet.encrypt(value.encode()).decode()
        print(f"'{key}': '{encrypted}',")