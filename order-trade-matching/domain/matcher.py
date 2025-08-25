from collections import defaultdict, deque
from .models import Match, Order, Trade


def match_orders_trades(
    orders: list[Order], trades: list[Trade]
) -> list[Match]:  # noqa: E501
    """
    For a list of unique Quorus orders and a list of unique custodian trades
    for a single account, matches the orders to the trades.

    Matching Rules:
    - Same symbol and direction
    - Same date (submitted_date and filled_date on same day)
    - Quantity balanced (sum of orders == sum of trades for each group)
    - FIFO within balanced groups

    Args:
        orders (list[Order]): list of unique Quorus orders
        transactions (list[Trade]): list of unique custodian trades

    Returns:
        list[Match]: list of `Match`es containing the matched
        orders and trades and the allocated quantity
    """
    
    matches = []
    
    # STEP 1: Group by symbol, direction, and date
    # AAPL Example: Creates key ("AAPL", "buy", 2023-01-10)
    order_groups = defaultdict(list)
    trade_groups = defaultdict(list)
    
    for order in orders:
        key = (order.symbol, order.direction, order.submitted_date.date())
        order_groups[key].append(order)
    
    for trade in trades:
        key = (trade.symbol, trade.direction, trade.filled_date.date())
        trade_groups[key].append(trade)
    
    # STEP 2: Only process groups that have both orders and trades with balanced quantities
    for key in order_groups:
        if key not in trade_groups:
            continue
            
        # AAPL: group_orders = [Order(50 shares)], group_trades = [Trade(50 shares)]
        group_orders = order_groups[key]
        group_trades = trade_groups[key]
        
        # STEP 3: Check quantity balance
        # AAPL: total_order_qty = 50, total_trade_qty = 50
        # AAPL: 50 == 50, so we continue processing this group
        total_order_qty = sum(order.quantity for order in group_orders)
        total_trade_qty = sum(trade.quantity for trade in group_trades)
        
        if total_order_qty != total_trade_qty:
            continue  # Skip unbalanced groups
        
        # STEP 4: Sort by date for FIFO matching within the group
        # AAPL: Only 1 order and 1 trade, so sorting doesn't change anything
        # sorted_orders = [Order(AAPL, 50, buy, 2023-01-10)]
        # sorted_trades = [Trade(AAPL, 50, buy, 2023-01-10)]
        sorted_orders = sorted(group_orders, key=lambda x: x.submitted_date)
        sorted_trades = sorted(group_trades, key=lambda x: x.filled_date)

        # STEP 5: Create queues with remaining quantities
        # AAPL: orders_q = deque([[Order_obj, 50]])
        # AAPL: trades_q = deque([[Trade_obj, 50]])
        orders_q = deque([[order, order.quantity] for order in sorted_orders])
        trades_q = deque([[trade, trade.quantity] for trade in sorted_trades])
        
        # STEP 6: Match within this balanced group using FIFO
        while orders_q and trades_q:
            # AAPL Iteration 1: Both queues have items, so continue
            
            # AAPL: order = Order_obj, order_rem = 50
            # AAPL: trade = Trade_obj, trade_rem = 50
            order, order_rem = orders_q[0]
            trade, trade_rem = trades_q[0]
            
            # AAPL: 50 > 0 and 50 > 0, so create match
            if order_rem > 0 and trade_rem > 0:
                
                # AAPL: allocated = min(50, 50) = 50
                allocated = min(order_rem, trade_rem)
                
                # AAPL: Creates Match(Order_obj, Trade_obj, 50)
                matches.append(Match(order=order, trade=trade, allocated_quantity=allocated))
                
                # AAPL: orders_q[0][1] = 50 - 50 = 0
                # AAPL: trades_q[0][1] = 50 - 50 = 0
                # AAPL: Both now have 0 remaining
                orders_q[0][1] -= allocated
                trades_q[0][1] -= allocated
            
            # STEP 7: Remove exhausted items
            # AAPL: Remove exhausted order, orders_q = deque([])
            if orders_q[0][1] == 0:
                orders_q.popleft()
                
            # AAPL: Remove exhausted trade, trades_q = deque([])
            if trades_q and trades_q[0][1] == 0:
                trades_q.popleft()
        
        # AAPL: Loop ends because both queues are now empty
        # Result: 1 match created with 50 shares allocated
        
        # BTC Example (more complex - partial fills):
        # Input: Orders=[1 BTC, 0.5 BTC], Trades=[1.5 BTC]
        # Iteration 1: Match Order1(1 BTC) with Trade1(1.5 BTC) → allocate 1 BTC
        #              Remaining: orders_q=[[Order1,0],[Order2,0.5]], trades_q=[[Trade1,0.5]]
        #              Remove Order1 (exhausted)
        # Iteration 2: Match Order2(0.5 BTC) with Trade1(0.5 BTC) → allocate 0.5 BTC  
        #              Remaining: orders_q=[[Order2,0]], trades_q=[[Trade1,0]]
        #              Remove both (exhausted)
        # Result: 2 matches from 1 trade (partial fills)
    
    return matches
