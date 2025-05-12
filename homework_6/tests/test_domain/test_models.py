from dataclasses import asdict

import pytest
from domain.models import Order, Product


@pytest.mark.parametrize(
    "product, expected_dict",
    [
        (Product(id=1, name="Test Product", quantity=42, price=42.0),
         {"id": 1, "name": "Test Product", "quantity": 42, "price": 42.0})
    ]
)
def test_product_creation(product, expected_dict):
    assert asdict(product) == expected_dict


@pytest.mark.parametrize(
    "order, expected_products",
    [
        (Order(id=1), []),
        (Order(id=1, products=[
            Product(id=1, name="Product 1", quantity=512, price=512.0),
            Product(id=2, name="Product 2", quantity=1024, price=1024.0)
        ]), [
            Product(id=1, name="Product 1", quantity=512, price=512.0),
            Product(id=2, name="Product 2", quantity=1024, price=1024.0)
        ])
    ]
)
def test_order_creation(order, expected_products):
    assert order.products == expected_products


def test_order_add_single_product():
    order = Order(id=1)
    product = Product(id=1, name="Test Product", quantity=42, price=420.0)
    order.add_product(product)
    assert order.products == [product]


def test_order_add_multiple_products():
    order = Order(id=1)
    p1 = Product(id=1, name="Product 1", quantity=512, price=512.0)
    p2 = Product(id=2, name="Product 2", quantity=1024, price=1024.0)
    order.add_product(p1)
    order.add_product(p2)
    assert order.products == [p1, p2]


def test_order_add_same_product_twice():
    order = Order(id=1)
    product = Product(id=1, name="Test Product", quantity=42, price=420.0)
    order.add_product(product)
    order.add_product(product)
    assert order.products == [product, product]
