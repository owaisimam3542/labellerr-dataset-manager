
"""CLI presentation layer for Labellerr Dataset Manager."""
import argparse
import json
import logging
import os
import sys

from dotenv import load_dotenv

from ..config import Settings, ConfigurationError
from ..client import LabellerrGateway, SDKIntegrationError
from ..services.connection_service import ConnectionService, ServiceError
from ..services.dataset_service import DatasetService


LOG = logging.getLogger("labellerr_dataset_manager")

SUPPORTED_PROVIDERS = ("s3", "gcs")
SUPPORTED_DATA_TYPES = ("image", "video", "audio", "document", "text")
SUPPORTED_CONNECTION_TYPES = ("import", "export")


def _json_default(obj):
    """Convert SDK objects to JSON-compatible values."""
    if hasattr(obj, "model_dump"):
        return obj.model_dump(mode="json")
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    return str(obj)


def _get_id(result):
    """Extract an identifier from an SDK response."""
    if isinstance(result, dict):
        for key in ("connection_id", "dataset_id", "id", "_id", "uuid"):
            if result.get(key) is not None:
                return result[key]
        return None

    for attr in ("connection_id", "dataset_id", "id", "_id", "uuid"):
        value = getattr(result, attr, None)
        if value is not None:
            return value

    return None


def _row(obj, key):
    """Read a field from a dictionary or SDK object."""
    if isinstance(obj, dict):
        return obj.get(key, "")
    return getattr(obj, key, "")


def _connection_args(parser, include_name):
    parser.add_argument(
        "--provider",
        choices=SUPPORTED_PROVIDERS,
        required=True,
        help="Cloud storage provider: s3 or gcs.",
    )
    parser.add_argument(
        "--path",
        required=True,
        help="Storage path, such as s3://bucket/folder or gs://bucket/folder.",
    )
    parser.add_argument(
        "--data-type",
        choices=SUPPORTED_DATA_TYPES,
        default="image",
        help="Type of data stored in the connection.",
    )
    parser.add_argument(
        "--connection-type",
        choices=SUPPORTED_CONNECTION_TYPES,
        default="import",
        help="Connection purpose: import or export.",
    )

    if include_name:
        parser.add_argument(
            "--name",
            required=True,
            help="Display name for the connection.",
        )
        parser.add_argument(
            "--description",
            default="",
            help="Optional connection description.",
        )


def build_parser():
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="labellerr-dataset-manager",
        description=(
            "Manage Labellerr cloud-storage connections and datasets."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # Test a storage connection without creating it.
    test = sub.add_parser(
        "test-connection",
        help="Validate access to an S3 or GCS storage path.",
    )
    _connection_args(test, include_name=False)

    # Create a cloud-storage connection.
    create = sub.add_parser(
        "create-connection",
        help="Test and register a cloud-storage connection.",
    )
    _connection_args(create, include_name=True)

    # List configured connections.
    sub.add_parser(
        "list-connections",
        help="List configured S3 and GCS connections.",
    )

    # Create a dataset from an existing connection.
    dataset = sub.add_parser(
        "create-dataset",
        help="Create a dataset from an existing connection and storage path.",
    )
    dataset.add_argument(
        "--name",
        required=True,
        help="Dataset name.",
    )
    dataset.add_argument(
        "--connection-id",
        required=True,
        help="Existing Labellerr connection ID.",
    )
    dataset.add_argument(
        "--path",
        required=True,
        help="Storage path accessible through the connection.",
    )
    dataset.add_argument(
        "--description",
        required=True,
        help="Dataset description.",
    )
    dataset.add_argument(
        "--data-type",
        choices=SUPPORTED_DATA_TYPES,
        default="image",
        help="Dataset data type.",
    )

    # Delete a connection, with confirmation by default.
    delete = sub.add_parser(
        "delete-connection",
        help="Delete an existing cloud-storage connection.",
    )
    delete.add_argument(
        "--id",
        required=True,
        dest="connection_id",
        help="Connection ID to delete.",
    )
    delete.add_argument(
        "--yes",
        action="store_true",
        help="Skip interactive confirmation.",
    )

    return parser


def _print(value, as_json=False):
    """Print plain text or JSON output."""
    if as_json:
        print(json.dumps(value, default=_json_default, indent=2))
    else:
        print(value)


def _connection_summary(item):
    """Build a readable connection summary."""
    connection_id = (
        _row(item, "connection_id")
        or _row(item, "id")
        or _row(item, "uuid")
        or _row(item, "_id")
    )

    name = _row(item, "name") or _row(item, "connection_name")
    provider = (
        _row(item, "provider")
        or _row(item, "connector_type")
        or _row(item, "connector")
    )
    connection_type = _row(item, "connection_type") or _row(item, "type")
    status = _row(item, "status")

    return [
        connection_id or "",
        name or "",
        provider or "",
        connection_type or "",
        status or "",
    ]


def run(argv=None, gateway_factory=None):
    """Execute a CLI command and return an exit code."""
    load_dotenv()

    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO").upper(),
        format="%(levelname)s %(name)s: %(message)s",
    )

    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        # Confirm deletion before initializing the SDK.
        if args.command == "delete-connection" and not args.yes:
            if not sys.stdin.isatty():
                raise ServiceError(
                    "Deletion requires confirmation in non-interactive mode. "
                    "Review the ID and rerun with --yes to confirm."
                )

            answer = input(
                f"Delete connection '{args.connection_id}'? "
                "Type 'yes' to confirm: "
            ).strip().lower()

            if answer != "yes":
                print("Deletion cancelled.")
                return 0

        settings = Settings.from_env()

        gateway = (
            gateway_factory(settings)
            if gateway_factory
            else LabellerrGateway.from_settings(settings)
        )

        connections = ConnectionService(gateway)

        if args.command == "test-connection":
            connections.test(
                provider=args.provider,
                path=args.path,
                data_type=args.data_type,
                connection_type=args.connection_type,
            )

            output = {
                "success": True,
                "message": "Storage connection test passed.",
            }

            _print(
                output if args.json else "SUCCESS: Storage connection test passed.",
                args.json,
            )

        elif args.command == "create-connection":
            result = connections.create(
                provider=args.provider,
                path=args.path,
                name=args.name,
                data_type=args.data_type,
                connection_type=args.connection_type,
                description=args.description,
            )

            connection_id = _get_id(result)

            output = {
                "success": True,
                "connection_id": connection_id,
                "result": result,
            }

            _print(
                output
                if args.json
                else (
                    "Connection created. ID: "
                    f"{connection_id or 'See SDK result'}"
                ),
                args.json,
            )

        elif args.command == "list-connections":
            items = connections.list()

            if args.json:
                _print(items, as_json=True)

            elif not items:
                print("No connections found.")

            else:
                columns = (
                    "ID",
                    "NAME",
                    "PROVIDER",
                    "TYPE",
                    "STATUS",
                )

                rows = [_connection_summary(item) for item in items]

                widths = [
                    max(
                        len(columns[index]),
                        *(len(str(row[index])) for row in rows),
                    )
                    for index in range(len(columns))
                ]

                print(
                    " | ".join(
                        columns[index].ljust(widths[index])
                        for index in range(len(columns))
                    )
                )
                print("-+-".join("-" * width for width in widths))

                for row in rows:
                    print(
                        " | ".join(
                            str(row[index]).ljust(widths[index])
                            for index in range(len(columns))
                        )
                    )

        elif args.command == "create-dataset":
            result = DatasetService(gateway).create(
                name=args.name,
                connection_id=args.connection_id,
                description=args.description,
                path=args.path,
                data_type=args.data_type,
            )

            dataset_id = _get_id(result)

            output = {
                "success": True,
                "dataset_id": dataset_id,
                "result": result,
            }

            _print(
                output
                if args.json
                else (
                    "Dataset created. ID: "
                    f"{dataset_id or 'See SDK result'}"
                ),
                args.json,
            )

        elif args.command == "delete-connection":
            connections.delete(args.connection_id)

            output = {
                "success": True,
                "deleted_id": args.connection_id,
            }

            _print(
                output
                if args.json
                else f"Connection deleted: {args.connection_id}",
                args.json,
            )

        return 0

    except (ConfigurationError, ServiceError, SDKIntegrationError) as exc:
        LOG.error("Command failed: %s", str(exc))
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    except Exception as exc:
        # Avoid printing raw SDK responses or credential-bearing tracebacks.
        LOG.error("Unexpected failure (%s).", type(exc).__name__)
        print(
            "ERROR: An unexpected error occurred. Check configuration and "
            "SDK compatibility, then retry.",
            file=sys.stderr,
        )
        return 1
