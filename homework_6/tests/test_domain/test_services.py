import pytest
from pytest_mock import MockerFixture
from domain.models import Product
from domain.repositories import OrderRepository, ProductRepository
from domain.services import WarehouseService, gen_id


@pytest.mark.parametrize(
    "name, quantity, price",
    [
        ("Test Product", 1024, 1024.0),
        ("Another Product", 512, 512.0),
    ],
)
def test_service_should_create_product_and_store_it(
    mocker: MockerFixture, name, quantity, price
):
    mock_product_repo = mocker.MagicMock(spec=ProductRepository)
    mock_order_repo = mocker.MagicMock(spec=OrderRepository)
    service = WarehouseService(mock_product_repo, mock_order_repo)

    product = service.create_product(name=name, quantity=quantity, price=price)

    expected = {"name": name, "quantity": quantity, "price": price}
    actual = {
        "name": product.name,
        "quantity": product.quantity,
        "price": product.price,
    }

    assert actual == expected
    mock_product_repo.add.assert_called_once_with(product)


def test_service_should_create_order_and_store_it(mocker: MockerFixture):
    mock_product_repo = mocker.MagicMock(spec=ProductRepository)
    mock_order_repo = mocker.MagicMock(spec=OrderRepository)
    service = WarehouseService(mock_product_repo, mock_order_repo)

    product1 = Product(id=1, name="Product 1", quantity=512, price=512.0)
    product2 = Product(id=2, name="Product 2", quantity=1024, price=1024.0)
    products = [product1, product2]

    order = service.create_order(products=products)

    assert order.products == products
    mock_order_repo.add.assert_called_once_with(order)


def test_gen_id_produces_sequential_values():
    gen = gen_id()
    assert next(gen) == 1
    assert next(gen) == 2
    assert next(gen) == 3
