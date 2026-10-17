
"""Environment-backed configuration. Never log credential values."""
from dataclasses import dataclass
import os


class ConfigurationError(ValueError):
    """Raised when required configuration is absent."""


@dataclass(frozen=True)
class Settings:
    api_key: str
    api_secret: str
    client_id: str
    aws_access_key: str = ""
    aws_secret_key: str = ""
    gcs_service_account_json: str = ""

    @classmethod
    def from_env(cls, environ=None):
        env = os.environ if environ is None else environ

        required = {
            "LABELLERR_API_KEY": env.get("LABELLERR_API_KEY", "").strip(),
            "LABELLERR_API_SECRET": env.get("LABELLERR_API_SECRET", "").strip(),
            "LABELLERR_CLIENT_ID": env.get("LABELLERR_CLIENT_ID", "").strip(),
        }

        missing = [key for key, value in required.items() if not value]
        if missing:
            raise ConfigurationError(
                "Missing required environment variable(s): "
                + ", ".join(missing)
                + ". Set them in your environment or .env file."
            )

        return cls(
            api_key=required["LABELLERR_API_KEY"],
            api_secret=required["LABELLERR_API_SECRET"],
            client_id=required["LABELLERR_CLIENT_ID"],
            aws_access_key=env.get("AWS_ACCESS_KEY_ID", "").strip(),
            aws_secret_key=env.get("AWS_SECRET_ACCESS_KEY", "").strip(),
            gcs_service_account_json=env.get(
                "GCS_SERVICE_ACCOUNT_JSON", ""
            ).strip(),
        )
