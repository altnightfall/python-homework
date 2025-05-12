from infrastructure.orm import OrderORM, ProductORM


class TestORM:
    def test_creation(self):
        ProductORM()
        OrderORM()
