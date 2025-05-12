from pytest_mock import MockerFixture
from sqlalchemy.orm import Session

from domain.models import Order, Product
from infrastructure.orm import OrderORM, ProductORM
from infrastructure.repositories import (
    SqlAlchemyOrderRepository,
    SqlAlchemyProductRepository,
)


class TestSqlAlchemyProductRepository:

    def test_add_product_to_session(self, mocker: MockerFixture):
        mock_session = mocker.Mock(spec=Session)
        repo = SqlAlchemyProductRepository(mock_session)
        product = Product(id=1, name="Test Product", quantity=10, price=100)

        repo.add(product)

        mock_session.add.assert_called_once()
        added_orm = mock_session.add.call_args[0][0]
        assert added_orm.__dict__["name"] == "Test Product"

    def test_get_product_by_id(self, mocker: MockerFixture):
        mock_session = mocker.Mock(spec=Session)
        repo = SqlAlchemyProductRepository(mock_session)
        product_orm = ProductORM(id=1, name="Test Product", quantity=10, price=100)
        mock_session.query.return_value.filter_by.return_value.one.return_value = (
            product_orm
        )

        product = repo.get(1)

        mock_session.query.assert_called_once_with(ProductORM)
        assert (
            product.__dict__
            == Product(id=1, name="Test Product", quantity=10, price=100).__dict__
        )

    def test_list_all_products(self, mocker: MockerFixture):
        mock_session = mocker.Mock(spec=Session)
        repo = SqlAlchemyProductRepository(mock_session)
        products_orm = [
            ProductORM(id=1, name="Product 1", quantity=10, price=100),
            ProductORM(id=2, name="Product 2", quantity=20, price=200),
        ]
        mock_session.query.return_value.all.return_value = products_orm

        products = repo.list()

        mock_session.query.assert_called_once_with(ProductORM)
        assert [p.id for p in products] == [1, 2]


class TestSqlAlchemyOrderRepository:

    def test_add_order_with_products_to_session(self, mocker: MockerFixture):
        mock_session = mocker.Mock(spec=Session)
        repo = SqlAlchemyOrderRepository(mock_session)

        product1 = Product(id=1, name="Product 1", quantity=10, price=100)
        product2 = Product(id=2, name="Product 2", quantity=20, price=200)
        order = Order(id=42, products=[product1, product2])

        product_orm1 = ProductORM(id=1, name="Product 1", quantity=10, price=100)
        product_orm2 = ProductORM(id=2, name="Product 2", quantity=20, price=200)
        mock_session.query.return_value.filter_by.return_value.one.side_effect = [
            product_orm1,
            product_orm2,
        ]

        repo.add(order)

        mock_session.add.assert_called_once()
        added_order_orm = mock_session.add.call_args[0][0]
        assert [p.id for p in added_order_orm.products] == [1, 2]

    def test_get_order_by_id_with_products(self, mocker: MockerFixture):
        mock_session = mocker.Mock(spec=Session)
        repo = SqlAlchemyOrderRepository(mock_session)
        product_orm1 = ProductORM(id=1, name="Product 1", quantity=10, price=100)
        product_orm2 = ProductORM(id=2, name="Product 2", quantity=20, price=200)
        order_orm = OrderORM(id=1, products=[product_orm1, product_orm2])
        mock_session.query.return_value.filter_by.return_value.one.return_value = (
            order_orm
        )

        order = repo.get(1)

        mock_session.query.assert_called_once_with(OrderORM)
        assert [p.id for p in order.products] == [1, 2]

    def test_list_all_orders_with_their_products(self, mocker: MockerFixture):
        mock_session = mocker.Mock(spec=Session)
        repo = SqlAlchemyOrderRepository(mock_session)
        product_orm1 = ProductORM(id=1, name="Product 1", quantity=10, price=100)
        product_orm2 = ProductORM(id=2, name="Product 2", quantity=20, price=200)
        order_orm1 = OrderORM(id=1, products=[product_orm1, product_orm2])
        order_orm2 = OrderORM(id=2, products=[product_orm1])
        mock_session.query.return_value.all.return_value = [order_orm1, order_orm2]

        orders = repo.list()

        mock_session.query.assert_called_once_with(OrderORM)
        assert [(o.id, len(o.products)) for o in orders] == [(1, 2), (2, 1)]
