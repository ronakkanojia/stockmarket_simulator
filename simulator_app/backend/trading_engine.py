import sqlite3
from database import DB_NAME, get_cash, update_cash
def execute_order(ticker, strike, option_type, expiry, action, quantity, current_price):
    """
    Executes an option trade and updates both the cash wallet and positions.
    action: 'BUY' (adds to position, spends cash) or 'SELL' (reduces position, yields cash)
    quantity: The number of contracts to trade (1 contract usually = 100 shares multiplier)
    """
    if quantity <= 0:
        return {"success": False, "message": "Quantity must be greater than zero."}
        
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    option_type = option_type.upper()
    action = action.upper()
    
    # 1 option contract typically represents 100 shares
    multiplier = 100
    total_premium = current_price * quantity * multiplier
    
    current_cash = get_cash()
    
    # Fetch existing position if it exists
    cursor.execute('''
        SELECT id, quantity, avg_price FROM positions 
        WHERE ticker=? AND strike=? AND option_type=? AND expiry=?
    ''', (ticker, strike, option_type, expiry))
    position = cursor.fetchone()
    
    existing_qty = position[1] if position else 0
    existing_avg = position[2] if position else 0.0

    if action == "BUY":
        # Check if user has enough cash to pay the premium
        if current_cash < total_premium:
            conn.close()
            return {"success": False, "message": "Insufficient virtual funds to complete this purchase."}
        
        new_cash = current_cash - total_premium
        
        if position:
            # If adding to a long position or covering a short position
            new_qty = existing_qty + quantity
            # Recalculate average price only if expanding a long position
            if existing_qty >= 0:
                new_avg = ((existing_qty * existing_avg) + (quantity * current_price)) / new_qty
            else:
                new_avg = existing_avg # Covering a short position doesn't alter short cost basis
                
            if new_qty == 0:
                cursor.execute("DELETE FROM positions WHERE id=?", (position[0],))
            else:
                cursor.execute("UPDATE positions SET quantity=?, avg_price=? WHERE id=?", (new_qty, new_avg, position[0]))
        else:
            # Open brand new long position
            cursor.execute('''
                INSERT INTO positions (ticker, strike, option_type, expiry, quantity, avg_price)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (ticker, strike, option_type, expiry, quantity, current_price))

    elif action == "SELL":
        # Options selling (Shorting) adds premium to cash, but creates an outstanding debt liability
        new_cash = current_cash + total_premium
        new_qty = existing_qty - quantity
        
        if position:
            # Closing out a long position or expanding a short position
            if existing_qty > 0 and new_qty < 0:
                # Basic protection to avoid flipping from long straight to short in one click for simplicity
                conn.close()
                return {"success": False, "message": "Cannot flip from long to short in a single transaction. Close existing position first."}
            
            if new_qty == 0:
                cursor.execute("DELETE FROM positions WHERE id=?", (position[0],))
            else:
                cursor.execute("UPDATE positions SET quantity=? WHERE id=?", (new_qty, position[0]))
        else:
            # Opening a brand new naked short position (Writing an option)
            cursor.execute('''
                INSERT INTO positions (ticker, strike, option_type, expiry, quantity, avg_price)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (ticker, strike, option_type, expiry, -quantity, current_price))

    # Record the transaction history log
    cursor.execute('''
        INSERT INTO trade_history (ticker, strike, option_type, expiry, action, quantity, price)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (ticker, strike, option_type, expiry, action, quantity, current_price))
    
    # Save cash updates
    update_cash(new_cash)
    conn.commit()
    conn.close()
    
    return {
        "success": True, 
        "message": f"Successfully executed {action} order for {quantity} contracts.",
        "remaining_cash": round(new_cash, 2)
    }

def get_portfolio():
    """Retrieves all open options configurations in the simulator portfolio."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT ticker, strike, option_type, expiry, quantity, avg_price FROM positions")
    rows = cursor.fetchall()
    conn.close()
    
    portfolio = []
    for row in rows:
        portfolio.append({
            "ticker": row[0],
            "strike": row[1],
            "option_type": row[2],
            "expiry": row[3],
            "quantity": row[4],
            "avg_price": row[5]
        })
    return portfolio