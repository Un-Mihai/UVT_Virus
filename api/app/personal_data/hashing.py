import hashlib
import hmac

from pydantic import SecretStr


class IdentifierHasher:
    """Keyed hashes let documents be compared on a CNP without storing or sending the CNP.

    A plain SHA-256 of a 13-digit CNP is reversible by brute force; the HMAC key prevents that.
    """

    def __init__(self, key: SecretStr) -> None:
        self._key = key.get_secret_value().encode()

    def hash(self, kind: str, value: str) -> str:
        return hmac.new(self._key, f"{kind}:{value}".encode(), hashlib.sha256).hexdigest()

    def placeholder(self, kind: str, value: str) -> str:
        """Stand-in shown to the model: the same value always gets the same token."""
        return f"[{kind.upper()}#{self.hash(kind, value)[:6]}]"

    @staticmethod
    def mask(value: str) -> str:
        """What people see: "1900101123456" -> "1*********456"."""
        if len(value) <= 4:
            return "*" * len(value)
        return value[0] + "*" * (len(value) - 4) + value[-3:]
