import io
import logging
from typing import Optional
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from app.core.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    def __init__(self):
        self.bucket_name = settings.MINIO_BUCKET_NAME
        self.endpoint_url = (
            f"https://{settings.MINIO_ENDPOINT}"
            if settings.MINIO_SECURE
            else f"http://{settings.MINIO_ENDPOINT}"
        )
        self._client = None
        # Optional in-memory fallback for local unit tests without MinIO running
        self._in_memory_store = {}

    @property
    def client(self):
        if self._client is None:
            self._client = boto3.client(
                "s3",
                endpoint_url=self.endpoint_url,
                aws_access_key_id=settings.MINIO_ACCESS_KEY,
                aws_secret_access_key=settings.MINIO_SECRET_KEY,
                config=Config(signature_version="s3v4", connect_timeout=1, retries={"max_attempts": 1}),
                region_name="us-east-1",
            )
        return self._client

    def ensure_bucket_exists(self) -> bool:
        """Create bucket if it does not already exist."""
        if settings.ENVIRONMENT == "testing":
            return True

        # Fast socket check to prevent botocore timeout delays
        try:
            import socket
            from urllib.parse import urlparse
            parsed = urlparse(self.endpoint_url)
            host = parsed.hostname or "localhost"
            port = parsed.port or 9000
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            res = sock.connect_ex((host, port))
            sock.close()
            if res != 0:
                logger.debug(f"MinIO port {port} not listening. Local disk/memory storage active.")
                return False
        except Exception:
            return False

        try:
            self.client.head_bucket(Bucket=self.bucket_name)
            return True
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code in ("404", "NoSuchBucket"):
                try:
                    self.client.create_bucket(Bucket=self.bucket_name)
                    logger.info(f"Created MinIO bucket: {self.bucket_name}")
                    return True
                except Exception as ce:
                    logger.error(f"Failed to create MinIO bucket: {ce}")
                    return False
            logger.warning(f"MinIO head_bucket error ({error_code}): {e}")
            return False
        except Exception as e:
            logger.warning(f"Could not connect to MinIO ({e}). Fallback mode active.")
            return False

    def _get_local_file_path(self, object_name: str) -> str:
        import os
        storage_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "storage_data")
        os.makedirs(storage_dir, exist_ok=True)
        safe_name = object_name.replace("/", "_").replace("\\", "_")
        return os.path.join(storage_dir, safe_name)

    def upload_file(self, file_bytes: bytes, object_name: str, content_type: str = "application/octet-stream") -> str:
        """Upload binary data to MinIO bucket and return the object storage path."""
        # Always populate memory and local disk fallback for resilience
        self._in_memory_store[object_name] = (file_bytes, content_type)
        try:
            local_path = self._get_local_file_path(object_name)
            with open(local_path, "wb") as f:
                f.write(file_bytes)
        except Exception as local_err:
            logger.warning(f"Could not write local storage fallback: {local_err}")

        if settings.ENVIRONMENT == "testing":
            return object_name

        try:
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=object_name,
                Body=file_bytes,
                ContentType=content_type,
            )
            return object_name
        except Exception as e:
            logger.warning(f"MinIO upload failed ({e}), using local disk/memory fallback store")
            return object_name

    def download_file(self, object_name: str) -> bytes:
        """Download binary data from MinIO bucket or local fallback."""
        if settings.ENVIRONMENT == "testing" or object_name in self._in_memory_store:
            if object_name in self._in_memory_store:
                return self._in_memory_store[object_name][0]

        try:
            response = self.client.get_object(Bucket=self.bucket_name, Key=object_name)
            return response["Body"].read()
        except Exception as e:
            if object_name in self._in_memory_store:
                return self._in_memory_store[object_name][0]
            try:
                local_path = self._get_local_file_path(object_name)
                import os
                if os.path.exists(local_path):
                    with open(local_path, "rb") as f:
                        return f.read()
            except Exception:
                pass
            logger.error(f"Failed to download object {object_name} from MinIO and local fallback: {e}")
            raise

    def delete_file(self, object_name: str) -> bool:
        """Delete an object from MinIO and local fallback."""
        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=object_name)
        except Exception as e:
            logger.error(f"Failed to delete object {object_name} from MinIO: {e}")
        self._in_memory_store.pop(object_name, None)
        try:
            local_path = self._get_local_file_path(object_name)
            import os
            if os.path.exists(local_path):
                os.remove(local_path)
        except Exception:
            pass
        return True


storage_service = StorageService()
