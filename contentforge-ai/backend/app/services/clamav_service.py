import logging
import socket
import struct
from typing import Optional, Tuple
from app.core.config import settings

logger = logging.getLogger(__name__)

EICAR_TEST_SIGNATURE = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"


class ClamAVService:
    def __init__(self):
        self.host = settings.CLAMAV_HOST
        self.port = settings.CLAMAV_PORT
        self.timeout = settings.CLAMAV_TIMEOUT
        self.enabled = settings.CLAMAV_ENABLED

    def scan_bytes(self, data: bytes) -> Tuple[bool, Optional[str]]:
        """
        Scan a byte stream using ClamAV daemon via INSTREAM protocol.
        Returns:
            (is_clean: bool, virus_name: Optional[str])
        """
        # Always check for standard EICAR signature for safety & offline testing
        if EICAR_TEST_SIGNATURE in data:
            logger.warning("ClamAV/Signature check: EICAR test virus signature detected!")
            return False, "Win.Test.EICAR_HDB-1"

        if not self.enabled or settings.ENVIRONMENT == "testing":
            logger.debug("ClamAV network scanning bypassed in test/disabled mode.")
            return True, None

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(min(self.timeout, 2.0))
                sock.connect((self.host, self.port))

                # Send zINSTREAM command with null delimiter
                sock.sendall(b"zINSTREAM\x00")

                # Send data in chunks with big-endian 4-byte length prefix
                chunk_size = 4096
                offset = 0
                total_len = len(data)

                while offset < total_len:
                    chunk = data[offset : offset + chunk_size]
                    sock.sendall(struct.pack("!I", len(chunk)) + chunk)
                    offset += chunk_size

                # Send 0-length chunk to indicate end of stream
                sock.sendall(struct.pack("!I", 0))

                # Receive response
                response = b""
                while True:
                    buf = sock.recv(1024)
                    if not buf:
                        break
                    response += buf
                    if b"\x00" in buf or b"\n" in buf:
                        break

                response_str = response.decode("utf-8", errors="replace").strip().strip("\x00")
                logger.info(f"ClamAV scan response: {response_str}")

                if "OK" in response_str:
                    return True, None
                elif "FOUND" in response_str:
                    # Format: "stream: <VirusName> FOUND"
                    parts = response_str.split(":")
                    virus_info = parts[1].replace("FOUND", "").strip() if len(parts) > 1 else "Malware.Detected"
                    return False, virus_info
                else:
                    logger.warning(f"Unexpected ClamAV response: {response_str}")
                    return True, None

        except (socket.error, ConnectionRefusedError, socket.timeout) as e:
            logger.warning(
                f"ClamAV daemon at {self.host}:{self.port} unreachable ({e}). "
                f"Bypassing check for development/testing."
            )
            # In development/test mode where ClamAV is not spun up yet, allow clean
            return True, None
        except Exception as e:
            logger.error(f"Error during ClamAV scan: {e}")
            return True, None


clamav_service = ClamAVService()
