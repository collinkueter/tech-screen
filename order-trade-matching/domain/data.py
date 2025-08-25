from datetime import datetime
from decimal import Decimal

from .models import Match, Order, Trade

ORDERS_TO_MATCH = [
    Order(
        symbol="AAPL",
        quantity=Decimal("50"),
        direction="buy",
        submitted_date=datetime(2023, 1, 10),
    ),
    Order(
        symbol="BTC",
        quantity=Decimal("1"),
        direction="sell",
        submitted_date=datetime(2023, 2, 20),
    ),
    Order(
        symbol="BTC",
        quantity=Decimal("0.5"),
        direction="sell",
        submitted_date=datetime(2023, 2, 20),
    ),
    Order(
        symbol="USBOND",
        quantity=Decimal("100"),
        direction="buy",
        submitted_date=datetime(2023, 3, 15),
    ),
    Order(
        symbol="USBOND1",
        quantity=Decimal("60"),
        direction="buy",
        submitted_date=datetime(2023, 3, 15),
    ),
    Order(
        symbol="GE",
        quantity=Decimal("100"),
        direction="sell",
        submitted_date=datetime(2023, 3, 15),
    ),
    Order(
        symbol="GE",
        quantity=Decimal("50"),
        direction="sell",
        submitted_date=datetime(2023, 3, 15),
    ),
]

TRADES_TO_MATCH = [
    Trade(
        symbol="AAPL",
        cost_basis=Decimal("10023"),
        quantity=Decimal("50"),
        price=Decimal("200.46"),
        direction="buy",
        filled_date=datetime(2023, 1, 10),
    ),
    Trade(
        symbol="BTC",
        cost_basis=Decimal("45002.22"),
        quantity=Decimal("1.5"),
        price=Decimal("30001.48"),
        direction="sell",
        filled_date=datetime(2023, 2, 20),
    ),
    Trade(
        symbol="USBOND",
        cost_basis=Decimal("25925"),
        quantity=Decimal("50"),
        price=Decimal("518.5"),
        direction="buy",
        filled_date=datetime(2023, 3, 15),
    ),
    Trade(
        symbol="USBOND",
        cost_basis=Decimal("25935"),
        quantity=Decimal("50"),
        price=Decimal("518.7"),
        direction="buy",
        filled_date=datetime(2023, 3, 15),
    ),
    Trade(
        symbol="USBOND1",
        cost_basis=Decimal("25945"),
        quantity=Decimal("50"),
        price=Decimal("518.9"),
        direction="buy",
        filled_date=datetime(2023, 3, 15),
    ),
    Trade(
        symbol="GE",
        cost_basis=Decimal("2512.5"),
        quantity=Decimal("75"),
        price=Decimal("33.5"),
        direction="sell",
        filled_date=datetime(2023, 3, 15),
    ),
    Trade(
        symbol="GE",
        cost_basis=Decimal("1177.75"),
        quantity=Decimal("70"),
        price=Decimal("33.65"),
        direction="sell",
        filled_date=datetime(2023, 3, 15),
    ),
    Trade(
        symbol="GE",
        cost_basis=Decimal("1346.4"),
        quantity=Decimal("5"),
        price=Decimal("33.66"),
        direction="sell",
        filled_date=datetime(2023, 3, 15),
    ),
]

TARGET_MATCHES = [
    Match(
        order=ORDERS_TO_MATCH[0],
        trade=TRADES_TO_MATCH[0],
        allocated_quantity=Decimal("50"),
    ),
    Match(
        order=ORDERS_TO_MATCH[1],
        trade=TRADES_TO_MATCH[1],
        allocated_quantity=Decimal("1"),
    ),
    Match(
        order=ORDERS_TO_MATCH[2],
        trade=TRADES_TO_MATCH[1],
        allocated_quantity=Decimal("0.5"),
    ),
    Match(
        order=ORDERS_TO_MATCH[3],
        trade=TRADES_TO_MATCH[2],
        allocated_quantity=Decimal("50"),
    ),
    Match(
        order=ORDERS_TO_MATCH[3],
        trade=TRADES_TO_MATCH[3],
        allocated_quantity=Decimal("50"),
    ),
    Match(
        order=ORDERS_TO_MATCH[5],
        trade=TRADES_TO_MATCH[5],
        allocated_quantity=Decimal("75"),
    ),
    Match(
        order=ORDERS_TO_MATCH[5],
        trade=TRADES_TO_MATCH[6],
        allocated_quantity=Decimal("25"),
    ),
    Match(
        order=ORDERS_TO_MATCH[6],
        trade=TRADES_TO_MATCH[6],
        allocated_quantity=Decimal("45"),
    ),
    Match(
        order=ORDERS_TO_MATCH[6],
        trade=TRADES_TO_MATCH[7],
        allocated_quantity=Decimal("5"),
    ),
]