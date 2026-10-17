# Labellerr Dataset Manager

A Python CLI for testing cloud-storage paths, registering connections, listing and deleting connections, and creating datasets. SDK calls are isolated behind `LabellerrGateway`; unit tests use a fake gateway and do not require credentials.

## Requirements

- Python 3.10+
- Labellerr API key, API secret, and client ID
- Access to the cloud bucket and permissions required by Labellerr

## Setup (Windows PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` with your credentials. Never commit `.env`; `.gitignore` excludes it. Alternatively, set the three variables in your shell environment. The app never intentionally logs their values.

## Commands

```powershell
python main.py --help
python main.py test-connection --provider s3 --path s3://bucket/images --data-type image --connection-type import
python main.py create-connection --provider s3 --path s3://bucket/images --name "Image Import" --data-type image --connection-type import
python main.py list-connections
python main.py create-dataset --name "Vehicle Dataset" --connection-id conn-123 --description "Vehicle images"
python main.py delete-connection --id conn-123
python main.py --json list-connections
python main.py delete-connection --id conn-123 --yes
```

For GCS, use `--provider gcs --path gs://bucket/prefix`. GCS should be considered available only when the installed SDK's connection-test and connection-management APIs support it.

Deletion prompts for the exact word `yes`. In non-interactive use, pass `--yes` explicitly. Validation happens before remote calls where possible. Commands return exit code `0` for success, `2` for configuration/validation/integration errors, and `1` for unexpected failures.

## Tests

```powershell
python -m pytest -v
```

Tests mock the gateway boundary; they verify validation, service behavior, safe deletion defaults, and error handling without cloud or Labellerr credentials. They do not verify remote API compatibility or cloud IAM permissions.

## SDK compatibility note

The Labellerr SDK documents `LabellerrClient` in `labellerr.core` and dataset creation through its core modules. Storage connection APIs can differ across SDK releases. `src/client.py` isolates those operations and fails clearly if the installed SDK does not expose a recognized operation; it does not fake successful SDK responses. Before submission, verify the storage method names and signatures against the exact SDK version installed in your environment and update the adapter if needed.

## Example output

```text
SUCCESS: Storage connection test passed.
Connection created. ID: conn-123
```

The output above is illustrative only; IDs and successful API results come from Labellerr when run with valid configuration.

## Design decisions

- `config.py` validates all required environment values in one place.
- `LabellerrGateway` owns SDK initialization and external operations.
- Service classes validate input and translate expected failures into user-facing errors.
- `commands.py` handles parsing, display, confirmation, and exit codes.
- Logs contain operation-level errors, not credential values or raw SDK response payloads.

See [IMPROVEMENTS.md](IMPROVEMENTS.md) for architecture and production-readiness proposals.
