import re
from typing import Any, Dict, List, Set
from ai_services.domains.base_domain import BaseDomain

HEX_ADDRESS_REGEX = re.compile(r"\b0x[a-fA-F0-9]{40}\b")
TX_HASH_REGEX = re.compile(r"\b0x[a-fA-F0-9]{64}\b")
BLOCK_NUMBER_REGEX = re.compile(r"\bblock\s+#?(\d+)\b", re.IGNORECASE)

BLOCKCHAIN_KEYWORDS = {
    "blockchain", "smart contract", "ethereum", "polygon", "solana", "bitcoin",
    "token", "nft", "wallet", "transaction hash", "txhash", "gas fee", "nonce",
    "validator", "consensus", "bridge", "defi", "exploit", "reentrancy", "slippage",
    "chain id", "amoy", "mainnet", "testnet", "erc-20", "erc-721", "erc-1155"
}


class BlockchainDomain(BaseDomain):
    @property
    def domain_key(self) -> str:
        return "blockchain"

    @property
    def domain_name(self) -> str:
        return "Blockchain & Smart Contract Intelligence Pack"

    def detect_affinity(self, text: str) -> float:
        text_lower = text.lower()
        keyword_matches = sum(1 for kw in BLOCKCHAIN_KEYWORDS if kw in text_lower)
        tx_matches = len(TX_HASH_REGEX.findall(text))
        addr_matches = len(HEX_ADDRESS_REGEX.findall(text))

        score = min(1.0, (keyword_matches * 0.15) + (tx_matches * 0.35) + (addr_matches * 0.25))
        return round(score, 2)

    def extract_domain_entities(self, text: str) -> Dict[str, List[str]]:
        addresses = list(set(HEX_ADDRESS_REGEX.findall(text)))
        tx_hashes = list(set(TX_HASH_REGEX.findall(text)))
        blocks = list(set(BLOCK_NUMBER_REGEX.findall(text)))

        return {
            "contract_addresses": addresses,
            "transaction_hashes": tx_hashes,
            "block_numbers": blocks,
        }

    def validate_domain_constraints(
        self,
        source_entities: Dict[str, List[str]],
        generated_content: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        issues: List[Dict[str, Any]] = []
        gen_str = str(generated_content)
        gen_entities = self.extract_domain_entities(gen_str)

        # 1. Validate Transaction Hashes (Exact hex preservation)
        source_txs = set(tx.lower() for tx in source_entities.get("transaction_hashes", []))
        for gen_tx in gen_entities.get("transaction_hashes", []):
            if gen_tx.lower() not in source_txs:
                issues.append({
                    "domain": self.domain_key,
                    "issue_type": "tx_hash_mismatch",
                    "severity": "critical",
                    "description": f"Generated transaction hash '{gen_tx}' does not match any source transaction hash.",
                })

        # 2. Validate Contract / Wallet Addresses
        source_addrs = set(addr.lower() for addr in source_entities.get("contract_addresses", []))
        for gen_addr in gen_entities.get("contract_addresses", []):
            if gen_addr.lower() not in source_addrs:
                issues.append({
                    "domain": self.domain_key,
                    "issue_type": "contract_address_mismatch",
                    "severity": "critical",
                    "description": f"Generated contract/wallet address '{gen_addr}' is not present in source document.",
                })

        return issues
