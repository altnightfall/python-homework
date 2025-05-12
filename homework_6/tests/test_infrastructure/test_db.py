from infrastructure.database import DATABASE_URL


class TestDatabase:
    def test_db(self):
        assert DATABASE_URL.startswith("sqlite://")
