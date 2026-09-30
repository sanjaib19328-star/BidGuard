import socket
import pytest

from app.core.config import settings


def is_postgres_reachable() -> bool:
    """Check if the configured PostgreSQL port is reachable."""
    host = settings.DATABASE_URL.split("@")[-1].split(":")[0] if "@" in settings.DATABASE_URL else "localhost"
    port_str = settings.DATABASE_URL.split(":")[-1].split("/")[0] if ":" in settings.DATABASE_URL else "5433"
    try:
        port = int(port_str)
    except ValueError:
        port = 5433

    try:
        with socket.create_connection((host, port), timeout=0.5):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


DB_ONLINE = is_postgres_reachable()

DB_INTEGRATION_MODULES = {
    "test_auth",
    "test_tenders",
    "test_documents",
    "test_clauses_api",
    "test_requirements_api",
    "test_compliance_api",
}


@pytest.fixture(autouse=True)
def require_db_for_integration_tests(request):
    """Automatically skip live-DB integration tests if PostgreSQL server is offline."""
    module_name = request.module.__name__.split(".")[-1] if request.module else ""
    if module_name in DB_INTEGRATION_MODULES and not DB_ONLINE:
        pytest.skip(f"Live PostgreSQL server is offline ({settings.DATABASE_URL}). Skipping integration test.")
