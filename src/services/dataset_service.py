
"""Business rules for dataset creation."""
from ..client import SDKIntegrationError
from .connection_service import ServiceError, validate_id, SUPPORTED_TYPES


class DatasetService:
    def __init__(self, gateway):
        self.gateway = gateway

    def create(
        self,
        name,
        connection_id,
        description,
        path=None,
        data_type="image",
    ):
        if not isinstance(name, str) or not name.strip():
            raise ServiceError("Dataset name cannot be empty.")

        if not isinstance(description, str) or not description.strip():
            raise ServiceError("Dataset description cannot be empty.")
        connection_id = validate_id(connection_id)
        if not isinstance(path, str) or not path.strip():
            raise ServiceError(
                "Storage path is required. Provide an s3:// or gs:// path."
            )

        path = path.strip()

        if not (
            path.startswith("s3://") or path.startswith("gs://")
        ):
            raise ServiceError(
                "Storage path must start with s3:// or gs://."
            )

        if data_type not in SUPPORTED_TYPES:
            raise ServiceError(
                "Data type must be image, video, audio, document, or text."
            )

        connection_id = validate_id(connection_id)

        try:
            return self.gateway.create_dataset(
                name=name.strip(),
                connection_id=connection_id,
                description=description.strip(),
                path=path,
                data_type=data_type,
            )
        except (SDKIntegrationError, ServiceError):
            raise
        except Exception as exc:
            raise ServiceError(
                "Dataset creation failed. Check the connection ID, "
                "storage path, and API permissions."
            ) from exc
