import pytest

def pytest_configure(config):
    config.addinivalue_line(
        "markers", "integration: mark as integration test"
    )

@pytest.fixture(autouse=True)
def setup_logging():
    import logging
    logging.basicConfig(level=logging.DEBUG)