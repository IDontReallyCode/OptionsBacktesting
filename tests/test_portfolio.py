import pytest
from datetime import date
from src.portfolio.position import OptionPosition, Position
from src.portfolio.portfolio import Portfolio

def test_option_position_logic():
    # 1. Test Valuation with Multiplier
    # Bought 1 Call at $2.00
    opt = OptionPosition(
        symbol="SPY_CALL", 
        quantity=1, 
        avg_price=2.0, 
        strike=400, 
        option_type="C",
        multiplier=100
    )
    
    # Price moves to $3.00
    opt.update_market_value(3.0)
    
    # Value should be 3.00 * 1 * 100 = 300
    assert opt.market_value == 300.0
    # PnL should be (3.0 - 2.0) * 1 * 100 = 100
    assert opt.unrealized_pnl == 100.0

    # 2. Test ITM Logic
    assert opt.is_itm(401.0) is True  # Call Strike 400, Price 401 (ITM)
    assert opt.is_itm(399.0) is False # Call Strike 400, Price 399 (OTM)

    # 3. Test Put Logic
    put = OptionPosition(
        symbol="SPY_PUT", quantity=1, avg_price=2.0, 
        strike=400, option_type="P"
    )
    assert put.is_itm(390.0) is True # Put Strike 400, Price 390 (ITM)

def test_portfolio_aggregation():
    port = Portfolio(initial_capital=10000.0)
    
    # Buy Stock: 10 shares @ 100 = $1000 cost
    port.add_position("SPY", 10, 100.0)
    assert port.current_cash == 9000.0
    
    # Buy Option: 1 Call @ 2.0 = $200 cost (2 * 100 multiplier)
    meta = {"strike": 400, "option_type": "C"}
    port.add_position("SPY_OPT", 1, 2.0, meta=meta)
    assert port.current_cash == 8800.0  # 9000 - 200
    
    # Initial Equity should still be 10,000 (Cash + Assets)
    # Stock Value: 10 * 100 = 1000
    # Option Value: 1 * 2.0 * 100 = 200
    # Cash: 8800
    # Total: 10000
    port.positions["SPY"].update_market_value(100.0)
    port.positions["SPY_OPT"].update_market_value(2.0)
    
    # We mock the mark_to_market logic manually here to test aggregation
    equity = port.current_cash
    for pos in port.positions.values():
        equity += pos.market_value
        
    assert equity == 10000.0