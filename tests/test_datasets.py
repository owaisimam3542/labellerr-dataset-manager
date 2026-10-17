import pytest
from src.services.dataset_service import DatasetService
from src.services.connection_service import ServiceError


class Gateway:
    def create_dataset(self, **kwargs):
        return {"dataset_id": "ds-123", **kwargs}



def test_dataset_creation_success():
    result = DatasetService(Gateway()).create(
        "Vehicles",
        "conn-123",
        "Vehicle images",
        "s3://test-bucket/vehicles",
    )

    assert result is not None



def test_invalid_dataset_input():
    with pytest.raises(ServiceError, match="name cannot be empty"):
        DatasetService(Gateway()).create(" ", "conn-123", "description")
    with pytest.raises(ServiceError, match="Invalid connection ID"):
        DatasetService(Gateway()).create("Vehicles", "bad id", "description")
