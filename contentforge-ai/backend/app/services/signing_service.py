import hashlib
import logging
import os
from typing import Optional, Tuple
from uuid import UUID

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.approval_signature import ApprovalSignature
from app.models.reviewer_key import ReviewerKey
from app.models.user import User

logger = logging.getLogger(__name__)


def _get_encryption_key() -> bytes:
    """Derive a 256-bit AES key from the application SECRET_KEY."""
    return hashlib.sha256(settings.SECRET_KEY.encode("utf-8")).digest()


def _encrypt_private_key(private_bytes: bytes) -> str:
    """Encrypt Ed25519 private key bytes using AES-256-GCM.

    Format returned: '{nonce_hex}:{ciphertext_hex}'
    """
    key = _get_encryption_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, private_bytes, None)
    return f"{nonce.hex()}:{ciphertext.hex()}"


def _decrypt_private_key(encrypted_str: str) -> bytes:
    """Decrypt an encrypted private key string."""
    key = _get_encryption_key()
    aesgcm = AESGCM(key)
    nonce_hex, ciphertext_hex = encrypted_str.split(":")
    nonce = bytes.fromhex(nonce_hex)
    ciphertext = bytes.fromhex(ciphertext_hex)
    return aesgcm.decrypt(nonce, ciphertext, None)


def generate_ed25519_keypair() -> Tuple[str, str]:
    """Generate a new Ed25519 keypair.

    Returns:
        (public_key_hex, encrypted_private_key_str)
    """
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    pub_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    priv_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )

    public_key_hex = pub_bytes.hex()
    encrypted_private_key = _encrypt_private_key(priv_bytes)

    return public_key_hex, encrypted_private_key


def get_or_create_reviewer_keys(db: Session, user_id: UUID) -> ReviewerKey:
    """Retrieve an existing ReviewerKey for the user or generate a new one."""
    rev_key = db.query(ReviewerKey).filter(ReviewerKey.user_id == user_id).first()
    if rev_key is not None:
        return rev_key

    pub_hex, enc_priv = generate_ed25519_keypair()
    rev_key = ReviewerKey(
        user_id=user_id,
        public_key=pub_hex,
        encrypted_private_key=enc_priv,
    )
    db.add(rev_key)
    db.commit()
    db.refresh(rev_key)
    logger.info(f"Generated new Ed25519 keypair for reviewer {user_id} [pub={pub_hex[:12]}...]")
    return rev_key


def sign_content_hash(
    db: Session,
    reviewer_id: UUID,
    output_id: UUID,
    content_hash: str,
) -> ApprovalSignature:
    """Sign a content hash using the reviewer's private key and store the signature."""
    rev_key = get_or_create_reviewer_keys(db, reviewer_id)
    priv_bytes = _decrypt_private_key(rev_key.encrypted_private_key)
    private_key = ed25519.Ed25519PrivateKey.from_private_bytes(priv_bytes)

    # Sign content hash bytes
    signature_bytes = private_key.sign(content_hash.encode("utf-8"))
    signature_hex = signature_bytes.hex()

    approval_sig = ApprovalSignature(
        output_id=output_id,
        reviewer_id=reviewer_id,
        content_hash_signed=content_hash,
        signature=signature_hex,
    )
    db.add(approval_sig)
    db.commit()
    db.refresh(approval_sig)

    logger.info(
        f"Reviewer {reviewer_id} signed output {output_id} "
        f"[hash={content_hash[:12]}..., sig={signature_hex[:12]}...]"
    )
    return approval_sig


def verify_signature(
    public_key_hex: str,
    content_hash: str,
    signature_hex: str,
) -> bool:
    """Independently verify an Ed25519 digital signature against a content hash.

    Any external party can run this verification without authentication or database access.
    """
    try:
        pub_bytes = bytes.fromhex(public_key_hex)
        sig_bytes = bytes.fromhex(signature_hex)
        public_key = ed25519.Ed25519PublicKey.from_public_bytes(pub_bytes)
        public_key.verify(sig_bytes, content_hash.encode("utf-8"))
        return True
    except (InvalidSignature, ValueError, Exception) as exc:
        logger.warning(f"Signature verification failed: {exc}")
        return False
