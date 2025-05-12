from typing import List
from .models import Product, Order
from .repositories import ProductRepository, OrderRepository


def gen_id():
    _id = 1
    while True:
        yield _id
        _id += 1


class WarehouseService:
    def __init__(self, product_repo: ProductRepository, order_repo: OrderRepository):
        self.product_repo=product_repo
        self.order_repo=order_repo

    def create_product(self, name: str, quantity: int, price: float) -> Product:
        product=Product(id=gen_id(), name=name, quantity=quantity,price=price)
        self.product_repo.add(product)
        return product

    def create_order(self, products: List[Product]) -> Order:
        order=Order(id=gen_id(), products=products)
        self.order_repo.add(order)
        return order
