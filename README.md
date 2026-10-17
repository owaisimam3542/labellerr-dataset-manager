# Labellerr Dataset Manager

A Python command-line application for managing cloud-storage connections and datasets through the Labellerr Python SDK.

## Features

- Load configuration from environment variables.
- Test cloud-storage connections.
- Create and list storage connections.
- Create datasets using existing connections.
- Delete connections with a safety confirmation.
- Support JSON output for automation.
- Validate inputs and handle SDK errors.
- Run automated tests without live cloud credentials.

## Project Structure

```text
labellerr-dataset-manager/
├── main.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── IMPROVEMENTS.md
├── src/
│   ├── config.py
│   ├── client.py
│   ├── cli/
│   └── services/
└── tests/
```

## Prerequisites

- Python 3.11 or another version supported by the pinned Labellerr SDK.
- Git.
- Valid Labellerr API credentials for live API operations.
- Appropriate cloud-storage permissions for the selected provider.

## Installation

Clone the repository:

```bash
git clone https://github.com/owaisimam3542/labellerr-dataset-manager.git
cd labellerr-dataset-manager
```

Create and activate a virtual environment.

**Windows PowerShell:**

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

## Configuration

Copy the environment template:

```powershell
Copy-Item .env.example .env
```

Edit `.env` and provide your authorized credentials:

```dotenv
LABELLERR_API_KEY=your_api_key
LABELLERR_API_SECRET=your_api_secret
LABELLERR_CLIENT_ID=your_client_id
```

Never commit `.env` or expose credentials in logs, screenshots, or issue reports. The `.env.example` file must contain placeholders only.

## Usage

Display available commands:

```bash
python main.py --help
```

Test an S3 connection:

```bash
python main.py test-connection --provider s3 --path s3://bucket/images --data-type image --connection-type import
```

Create a connection:

```bash
python main.py create-connection --provider s3 --path s3://bucket/images --name "Image Import" --data-type image --connection-type import
```

List connections:

```bash
python main.py list-connections
```

Create a dataset:

```bash
python main.py create-dataset --name "Vehicle Dataset" --connection-id YOUR_CONNECTION_ID --description "Vehicle images"
```

Delete a connection with confirmation:

```bash
python main.py delete-connection --id YOUR_CONNECTION_ID
```

For supported commands, use `--json` to request JSON output. Check `python main.py --help` for the exact available options.

**Important:** Replace example bucket paths and IDs with values appropriate for your account. Supported providers and options depend on the installed SDK and application implementation.

## Testing

Run the automated tests:

```bash
python -m pytest -v
```

Check installed dependencies:

```bash
python -m pip check
```

Tests mock external SDK/API interactions so they can run without live Labellerr or cloud credentials.

## Design Decisions

- **CLI separation:** Command parsing is separated from service logic.
- **Reusable services:** Connection and dataset operations are handled in dedicated service modules.
- **Configuration:** Credentials are read from environment variables instead of hardcoded source values.
- **Validation and error handling:** Invalid input and operation failures should produce useful error messages.
- **Testability:** External SDK operations are mocked in unit tests.

## Execution Evidence

Record the actual results from your final local run here. For example:

- `python -m pytest -v` — report the actual number of passing tests.
- `python -m pip check` — report the actual result.
- `python main.py --help` — verify that all required commands are listed.

Do not claim successful live API operations unless they have been verified using valid credentials.

## Known Limitations

- Live API behavior depends on valid Labellerr credentials and provider permissions.
- Cloud integration tests require authorized credentials and suitable storage resources.
- Pagination, retries, and other production enhancements should be documented according to their actual implementation status.

## Future Improvements

See [IMPROVEMENTS.md](IMPROVEMENTS.md) for proposed reliability, security, and architecture improvements.
