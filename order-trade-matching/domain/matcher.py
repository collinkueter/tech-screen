from collections import defaultdict, deque
from .models import Match, Order, Trade


def match_orders_trades(
    orders: list[Order], trades: list[Trade]
) -> list[Match]:  # noqa: E501
    """
    For a list of unique Quorus orders and a list of unique custodian trades
    for a single account, matches the orders to the trades.

    Args:
        orders (list[Order]): list of unique Quorus orders
        transactions (list[Trade]): list of unique custodian trades

    Returns:
        list[Match]: list of `Match`es containing the matched
        orders and trades and the allocated quantity
    """
    
    matches = []
    
    # Create a single sorted structure with remaining quantities
    sorted_orders = sorted(orders, key=lambda x: (x.symbol, x.direction, x.submitted_date))
    sorted_trades = sorted(trades, key=lambda x: (x.symbol, x.direction, x.filled_date))
    
    # Build lookup with deques for efficient pop operations
    order_queues = defaultdict(deque)
    trade_queues = defaultdict(deque)
    
    for order in sorted_orders:
        order_queues[(order.symbol, order.direction)].append([order, order.quantity])
    
    for trade in sorted_trades:
        trade_queues[(trade.symbol, trade.direction)].append([trade, trade.quantity])
    
    # Process all matching pairs
    for key in order_queues:
        orders_q = order_queues[key]
        trades_q = trade_queues.get(key, deque())
        
        while orders_q and trades_q:
            order, order_rem = orders_q[0]
            trade, trade_rem = trades_q[0]
            
            if order_rem > 0 and trade_rem > 0:
                allocated = min(order_rem, trade_rem)
                matches.append(Match(order=order, trade=trade, allocated_quantity=allocated))
                
                orders_q[0][1] -= allocated
                trades_q[0][1] -= allocated
            
            # Remove exhausted items
            if orders_q[0][1] == 0:
                orders_q.popleft()
            if trades_q and trades_q[0][1] == 0:
                trades_q.popleft()
    
    return matches
