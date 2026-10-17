
"""SDK initialization and adapter for Labellerr operations."""
from pathlib import Path

from .config import Settings


class SDKIntegrationError(RuntimeError):
    """The installed SDK does not expose or complete a required operation."""


class LabellerrGateway:
    def __init__(self, client, modules=None, settings=None):
        self.client = client
        self._modules = modules
        self.settings = settings

    @classmethod
    def from_settings(cls, settings: Settings):
        try:
            from labellerr.core import LabellerrClient
        except ImportError as exc:
            raise SDKIntegrationError(
                "Labellerr SDK is missing. Install requirements.txt first."
            ) from exc

        try:
            client = LabellerrClient(
                api_key=settings.api_key,
                api_secret=settings.api_secret,
                client_id=settings.client_id,
            )
        except Exception as exc:
            raise SDKIntegrationError(
                "Labellerr client initialization failed. Check your configuration."
            ) from exc

        return cls(client, settings=settings)

    @staticmethod
    def _enums(provider, data_type, connection_type):
        from labellerr.core.schemas.connectors import ConnectorType, ConnectionType
        from labellerr.core.schemas.base import DatasetDataType

        providers = {
            "s3": ConnectorType._S3,
            "gcs": ConnectorType._GCS,
        }

        if provider not in providers:
            raise SDKIntegrationError("Provider must be s3 or gcs.")

        try:
            return (
                providers[provider],
                DatasetDataType(data_type),
                ConnectionType(connection_type),
            )
        except (ValueError, TypeError) as exc:
            raise SDKIntegrationError(
                "Invalid data type or connection type."
            ) from exc

    def _settings(self):
        if self.settings is None:
            raise SDKIntegrationError(
                "Cloud credentials are not configured. Use the .env file."
            )
        return self.settings

    def _connection_params(
        self, provider, path, data_type, connection_type,
        name=None, description=""
    ):
        from labellerr.core.schemas.connectors import (
            AWSConnectionParams,
            AWSConnectionTestParams,
            GCSConnectionParams,
            GCSConnectionTestParams,
        )

        settings = self._settings()
        _, sdk_data_type, sdk_connection_type = self._enums(
            provider, data_type, connection_type
        )

        if provider == "s3":
            access_key = settings.aws_access_key
            secret_key = settings.aws_secret_key

            if not access_key or not secret_key:
                raise SDKIntegrationError(
                    "S3 credentials are missing. Set AWS_ACCESS_KEY_ID "
                    "and AWS_SECRET_ACCESS_KEY in .env."
                )

            fields = {
                "aws_access_key": access_key,
                "aws_secrets_key": secret_key,
                "path": path,
                "connection_type": sdk_connection_type,
                "data_type": sdk_data_type,
            }

            if name is None:
                return AWSConnectionTestParams(**fields)

            return AWSConnectionParams(
                **fields, name=name, description=description
            )

        service_account = settings.gcs_service_account_json

        if not service_account:
            raise SDKIntegrationError(
                "GCS credentials are missing. Set GCS_SERVICE_ACCOUNT_JSON "
                "to your service-account JSON file path in .env."
            )

        if not Path(service_account).is_file():
            raise SDKIntegrationError(
                "The configured GCS service-account JSON file does not exist."
            )

        fields = {
            "svc_account_json": service_account,
            "path": path,
            "connection_type": sdk_connection_type,
            "data_type": sdk_data_type,
        }

        if name is None:
            return GCSConnectionTestParams(**fields)

        return GCSConnectionParams(
            **fields, name=name, description=description
        )

    def test_connection(self, provider, path, data_type, connection_type):
        from labellerr.core.connectors.s3_connection import S3Connection
        from labellerr.core.connectors.gcs_connection import GCSConnection

        params = self._connection_params(
            provider, path, data_type, connection_type
        )

        try:
            if provider == "s3":
                return S3Connection.test_connection(self.client, params)
            if provider == "gcs":
                return GCSConnection.test_connection(self.client, params)
            raise SDKIntegrationError("Provider must be s3 or gcs.")
        except SDKIntegrationError:
            raise
        except Exception as exc:
            raise SDKIntegrationError(
                "Storage connection test failed. Check the path, credentials, "
                "permissions, and Labellerr configuration."
            ) from exc

    def create_connection(
        self, provider, path, name, data_type, connection_type,
        description=""
    ):
        from labellerr.core.connectors import create_connection

        connector_type, _, _ = self._enums(
            provider, data_type, connection_type
        )
        params = self._connection_params(
            provider, path, data_type, connection_type,
            name=name, description=description
        )

        try:
            # The SDK also tests the connection before creating it.
            return create_connection(self.client, connector_type, params)
        except SDKIntegrationError:
            raise
        except Exception as exc:
            raise SDKIntegrationError(
                "Labellerr could not create the storage connection."
            ) from exc

    def list_connections(self):
        from labellerr.core.connectors import list_connections
        from labellerr.core.schemas.connectors import ConnectorType

        results = []
        try:
            for connector in (ConnectorType._S3, ConnectorType._GCS):
                results.extend(list_connections(self.client, connector))
            return results
        except Exception as exc:
            raise SDKIntegrationError(
                "Labellerr could not list the storage connections."
            ) from exc

    def delete_connection(self, connection_id):
        from labellerr.core.connectors import delete_connection

        try:
            return delete_connection(self.client, connection_id)
        except Exception as exc:
            raise SDKIntegrationError(
                "Labellerr could not delete the specified connection."
            ) from exc

    def create_dataset(
        self, name, connection_id, description, path, data_type="image"
    ):
        from labellerr.core.datasets import create_dataset_from_connection
        from labellerr.core.schemas.base import DatasetDataType
        from labellerr.core.schemas.datasets import DatasetConfig

        try:
            config = DatasetConfig(
                dataset_name=name,
                data_type=DatasetDataType(data_type),
                dataset_description=description,
            )
            return create_dataset_from_connection(
                self.client, config, connection_id, path
            )
        except SDKIntegrationError:
            raise
        except Exception as exc:
            raise SDKIntegrationError(
                "Labellerr could not create the dataset. Check the connection ID, "
                "storage path, dataset type, and API permissions."
            ) from exc
