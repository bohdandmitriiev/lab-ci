from unittest.mock import Mock

import pytest

from shop.cart import Cart


class StubRates:
    """Власна заглушка RateProvider без мережевих запитів."""

    def __init__(self, rate: float) -> None:
        self.rate = rate

    def get_rate(self, currency: str) -> float:
        return self.rate


def test_new_cart_is_empty(cart: Cart) -> None:
    assert cart.items_count() == 0
    assert cart.total() == 0


def test_add_single_item(cart: Cart) -> None:
    cart.add("book", price=200.0)
    assert cart.items_count() == 1


def test_items_count(cart_with_items: Cart) -> None:
    assert cart_with_items.items_count() == 6


def test_add_same_item_increases_qty(cart: Cart) -> None:
    cart.add("book", price=200.0, qty=2)
    cart.add("book", price=200.0, qty=3)
    assert cart.items_count() == 5
    assert cart.total() == 1000.0


def test_add_same_name_different_price_keeps_first_price(cart: Cart) -> None:
    # Зафіксоване рішення: ціна першого додавання зберігається, змінюється лише кількість.
    cart.add("book", price=200.0)
    cart.add("book", price=300.0)
    assert cart.items_count() == 2
    assert cart.total() == 400.0


def test_remove_item(cart_with_items: Cart) -> None:
    cart_with_items.remove("pen")
    assert cart_with_items.items_count() == 2


def test_total_without_discount(cart_with_items: Cart) -> None:
    assert cart_with_items.total() == 460.0


def test_total_with_discount() -> None:
    # Arrange
    cart = Cart()
    cart.add("book", price=200.0, qty=2)
    # Act
    total = cart.total(discount_percent=10)
    # Assert
    assert total == 360.0


@pytest.mark.parametrize(
    ("discount", "expected"),
    [(0, 400.0), (10, 360.0), (50, 200.0), (100, 0.0)],
)
def test_discounts(discount: int, expected: float) -> None:
    cart = Cart()
    cart.add("book", price=200.0, qty=2)
    assert cart.total(discount_percent=discount) == expected


def test_total_rounding(cart: Cart) -> None:
    cart.add("x", price=0.1, qty=3)
    assert cart.total() == pytest.approx(0.3)


def test_add_negative_price_raises(cart: Cart) -> None:
    with pytest.raises(ValueError, match="price"):
        cart.add("book", price=-1.0)


@pytest.mark.parametrize("qty", [0, -1])
def test_add_non_positive_qty_raises(cart: Cart, qty: int) -> None:
    with pytest.raises(ValueError, match="qty"):
        cart.add("book", price=1.0, qty=qty)


@pytest.mark.parametrize("discount", [-1, 100.5, 101])
def test_invalid_discount_raises(cart_with_items: Cart, discount: float) -> None:
    with pytest.raises(ValueError, match="discount_percent"):
        cart_with_items.total(discount_percent=discount)


def test_remove_missing_item_raises(cart: Cart) -> None:
    with pytest.raises(KeyError):
        cart.remove("ghost")


@pytest.mark.parametrize("rate", [0.0, -5.0])
def test_total_in_invalid_rate_raises(cart: Cart, rate: float) -> None:
    with pytest.raises(ValueError, match="rate"):
        cart.total_in("USD", StubRates(rate))


def test_total_in_usd() -> None:
    rates = Mock()
    rates.get_rate.return_value = 40.0  # 1 USD = 40 UAH
    cart = Cart()
    cart.add("book", price=400.0)
    assert cart.total_in("USD", rates) == 10.0
    rates.get_rate.assert_called_once_with("USD")


def test_total_in_with_stub(cart_with_items: Cart) -> None:
    assert cart_with_items.total_in("EUR", StubRates(46.0)) == 10.0


# --- TDD: most_expensive() ---
def test_most_expensive_empty_cart(cart: Cart) -> None:
    assert cart.most_expensive() is None


def test_most_expensive_returns_highest_unit_price(cart_with_items: Cart) -> None:
    item = cart_with_items.most_expensive()
    assert item is not None
    assert item.name == "book"


def test_most_expensive_uses_unit_price_not_total(cart: Cart) -> None:
    cart.add("pen", price=15.0, qty=100)
    cart.add("book", price=200.0, qty=1)
    item = cart.most_expensive()
    assert item is not None
    assert item.name == "book"


def test_format_total(cart_with_items: Cart) -> None:
    assert cart_with_items.format_total() == "460.00"


def test_discount_formula_regression(cart: Cart) -> None:
    cart.add("book", price=100.0)
    assert cart.total(discount_percent=25) == 75.0
