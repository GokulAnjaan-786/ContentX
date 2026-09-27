import logging
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.trust_record import TrustRecord

logger = logging.getLogger(__name__)


def is_public_anchor_enabled() -> bool:
    """Check if public blockchain anchoring is enabled."""
    return bool(settings.ENABLE_PUBLIC_ANCHOR)


def anchor_latest_chain_head(db: Session, organisation_id: UUID) -> Optional[str]:
    """Anchor the organisation's latest chain head hash to Polygon Amoy testnet.

    Only the one-way cryptographic hash of the latest block in the chain is anchored,
    NEVER any confidential content.

    Returns the transaction hash if anchored, or None if disabled/skipped.
    """
    if not is_public_anchor_enabled():
        logger.debug("Public blockchain anchoring is disabled (ENABLE_PUBLIC_ANCHOR=false). Skipping.")
        return None

    # Retrieve latest record for this org
    latest_record = (
        db.query(TrustRecord)
        .filter(TrustRecord.organisation_id == organisation_id)
        .order_by(TrustRecord.chain_index.desc())
        .first()
    )

    if not latest_record:
        logger.info(f"No trust records found for organisation {organisation_id} to anchor.")
        return None

    if latest_record.public_anchor_tx_hash:
        logger.info(f"Latest record #{latest_record.chain_index} is already anchored: {latest_record.public_anchor_tx_hash}")
        return latest_record.public_anchor_tx_hash

    # Attempt Polygon Amoy testnet broadcast via Web3
    try:
        from web3 import Web3
        from web3.exceptions import Web3Exception

        rpc_url = settings.POLYGON_AMOY_RPC_URL
        w3 = Web3(Web3.HTTPProvider(rpc_url))

        if not w3.is_connected():
            logger.warning(f"Could not connect to Polygon Amoy RPC at {rpc_url}. Public anchor skipped.")
            return None

        private_key = settings.PUBLIC_ANCHOR_PRIVATE_KEY
        if not private_key:
            logger.warning("PUBLIC_ANCHOR_PRIVATE_KEY not set. Cannot sign public anchor transaction.")
            return None

        account = w3.eth.account.from_key(private_key)
        sender_address = account.address

        # EVM data payload containing the 64-char record_hash as hex bytes
        payload_data = w3.to_hex(text=f"CF_ANCHOR:{latest_record.record_hash}")

        nonce = w3.eth.get_transaction_count(sender_address, "pending")
        gas_price = w3.eth.gas_price

        tx = {
            "nonce": nonce,
            "to": sender_address,  # Self-notarization transaction
            "value": 0,
            "gas": 60000,
            "gasPrice": gas_price,
            "chainId": settings.POLYGON_AMOY_CHAIN_ID,
            "data": payload_data,
        }

        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash_bytes = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        tx_hash = w3.to_hex(tx_hash_bytes)

        # Update record with anchor transaction
        latest_record.public_anchor_tx_hash = tx_hash
        latest_record.public_anchor_chain_id = settings.POLYGON_AMOY_CHAIN_ID
        db.commit()

        logger.info(
            f"Successfully anchored chain head #{latest_record.chain_index} "
            f"to Polygon Amoy testnet: tx={tx_hash}"
        )
        return tx_hash

    except ImportError:
        logger.warning("web3 package not installed. Public blockchain anchor skipped.")
        return None
    except Exception as exc:
        logger.error(f"Failed to submit public anchor transaction to Polygon Amoy: {exc}")
        return None
