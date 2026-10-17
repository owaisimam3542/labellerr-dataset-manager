import pytest
from src.services.connection_service import ConnectionService, ServiceError, validate_id


class Gateway:
    def __init__(self, test_result=True, create_error=None):
        self.test_result = test_result
        self.create_error = create_error
        self.created = False
    def test_connection(self, **kwargs):
        if isinstance(self.test_result, Exception):
            raise self.test_result
        return self.test_result
    def create_connection(self, **kwargs):
        if self.create_error:
            raise self.create_error
        self.created = True
        return {"connection_id": "conn-123"}
    def list_connections(self):
        return [{"id": "conn-123", "name": "images", "provider": "s3", "status": "active"}]
    def delete_connection(self, connection_id):
        return True


def test_unexpected_sdk_exception_is_friendly():
    gateway = Gateway(
        test_result=RuntimeError("SECRET_TOKEN private SDK response")
    )

    with pytest.raises(ServiceError) as exc_info:
        ConnectionService(gateway).test(
            "s3",
            "s3://bucket/images",
            "image",
            "import",
        )

    assert "SECRET_TOKEN" not in str(exc_info.value)
    assert "private SDK response" not in str(exc_info.value)

def test_connection_validation_success():
    service = ConnectionService(Gateway())
    assert service.test("s3", "s3://bucket/images", "image", "import") is True


def test_connection_validation_failure():
    with pytest.raises(ServiceError, match="could not validate"):
        ConnectionService(Gateway(test_result=False)).test("s3", "s3://bucket/images", "image", "import")


def test_create_connection_does_not_create_if_test_fails():
    gateway = Gateway(test_result=False)
    with pytest.raises(ServiceError):
        ConnectionService(gateway).create("s3", "s3://bucket/images", "Images", "image", "import")
    assert gateway.created is False


def test_connection_creation_failure_is_friendly():
    with pytest.raises(ServiceError, match="creation failed"):
        ConnectionService(Gateway(create_error=RuntimeError("private SDK response"))).create("s3", "s3://bucket/images", "Images", "image", "import")


def test_invalid_path_and_id():
    with pytest.raises(ServiceError):
        ConnectionService(Gateway()).test("s3", "bucket/images", "image", "import")
    with pytest.raises(ServiceError, match="Invalid connection ID"):
        validate_id("bad id with spaces")


def test_delete_safety_noninteractive(monkeypatch, capsys):
    from src.cli.commands import run
    monkeypatch.setenv("LABELLERR_API_KEY", "key")
    monkeypatch.setenv("LABELLERR_API_SECRET", "secret")
    monkeypatch.setenv("LABELLERR_CLIENT_ID", "client")
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)
    code = run(["delete-connection", "--id", "conn-1"], gateway_factory=lambda settings: Gateway())
    assert code == 2
    assert "requires confirmation" in capsys.readouterr().err
