from database import get_connection as shared_get_connection
from db_connection import get_connection as legacy_get_connection


def test_legacy_connection_module_reuses_shared_helper():
    assert legacy_get_connection is shared_get_connection
