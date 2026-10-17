
"""Business rules for cloud-storage connections."""
import re
from urllib.parse import urlparse

from ..client import SDKIntegrationError


class ServiceError(ValueError):
    pass


SUPPORTED_TYPES = {"image", "video", "audio", "document", "text"}


def validate_storage_path(provider, path):
    provider = provider.lower().strip()

    if provider not in {"s3", "gcs"}:
        raise ServiceError("Provider must be 's3' or 'gcs'.")

    if not isinstance(path, str) or not path.strip():
        raise ServiceError("Storage path cannot be empty.")

    path = path.strip()
    parsed = urlparse(path)
    expected = "s3" if provider == "s3" else "gs"

    if parsed.scheme != expected or not parsed.netloc:
        raise ServiceError(
            f"Path for {provider.upper()} must start with "
            f"{expected}:// and include a bucket name."
        )

    return path


def validate_id(value):
    if not isinstance(value, str) or not re.fullmatch(
        r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", value.strip()
    ):
        raise ServiceError(
            "Invalid connection ID. Use the ID returned by list-connections."
        )
    return value.strip()


class ConnectionService:
    def __init__(self, gateway):
        self.gateway = gateway

    def test(self, provider, path, data_type, connection_type):
        path = validate_storage_path(provider, path)

        if data_type not in SUPPORTED_TYPES:
            raise ServiceError(
                "Data type must be image, video, audio, document, or text."
            )

        if connection_type not in {"import", "export"}:
            raise ServiceError(
                "Connection type must be import or export."
            )

        try:
            result = self.gateway.test_connection(
                provider=provider,
                path=path,
                data_type=data_type,
                connection_type=connection_type,
            )
        except (SDKIntegrationError, ServiceError):
            raise
        except Exception as exc:
            raise ServiceError(
                "Connection test failed. Verify storage permissions, "
                "path, credentials, and Labellerr configuration."
            ) from exc

        if result is False or (
            isinstance(result, dict) and result.get("success") is False
        ):
            raise ServiceError(
                "Labellerr could not validate this storage connection."
            )

        return result

    def create(
        self, provider, path, name, data_type, connection_type,
        description=""
    ):
        if not isinstance(name, str) or not name.strip():
            raise ServiceError("Connection name cannot be empty.")

        path = validate_storage_path(provider, path)

        # Do not create a connection if the validation step fails.
        self.test(provider, path, data_type, connection_type)

        try:
            return self.gateway.create_connection(
                provider=provider,
                path=path,
                name=name.strip(),
                data_type=data_type,
                connection_type=connection_type,
                description=(description or "").strip(),
            )
        except (SDKIntegrationError, ServiceError):
            raise
        except Exception as exc:
            raise ServiceError(
                "Connection creation failed. Check your credentials and permissions."
            ) from exc

    def list(self):
        try:
            result = self.gateway.list_connections()
            if isinstance(result, dict):
                return result.get("items", result.get("connections", [result]))
            return list(result or [])
        except (SDKIntegrationError, ServiceError):
            raise
        except Exception as exc:
            raise ServiceError(
                "Unable to list connections. Check API access and retry."
            ) from exc

    def delete(self, connection_id):
        connection_id = validate_id(connection_id)
        try:
            return self.gateway.delete_connection(connection_id)
        except (SDKIntegrationError, ServiceError):
            raise
        except Exception as exc:
            raise ServiceError(
                "Connection deletion failed. Check the ID and your permissions."
            ) from exc
