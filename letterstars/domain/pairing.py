"""Short, case-insensitive pairing codes for the local school prototype."""
import secrets

CODE_LENGTH = 8
CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def short_pairing_code(code):
    # Existing private credentials stay intact; expose their short prefix.
    return str(code).strip()[:CODE_LENGTH].upper()


def new_pairing_code():
    return "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))
