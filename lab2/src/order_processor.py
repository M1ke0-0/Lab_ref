from typing import Dict, Any, List

def _calculate_total(items: List[Dict[str, Any]]) -> float:
    """Calculate the total price of all items in the order."""
    total = 0.0
    for item in items:
        price = item.get('price', 0)
        qty = item.get('quantity', 0)
        if price < 0 or qty < 0:
            raise ValueError("Invalid price or quantity")
        total += price * qty
    return total

def _calculate_discount(total: float, customer_type: str) -> float:
    """Calculate the applicable discount based on customer type and order total."""
    discount = 0.0
    if customer_type == 'vip':
        discount = total * 0.10
    elif customer_type == 'premium':
        discount = total * 0.05
        
    if total > 1000:
        discount += total * 0.02
        
    return discount

def process_order(order: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process an order by calculating total price, applicable discounts,
    and updating the final price and status.
    """
    if order.get('status') != 'new':
        raise Exception("Order is not new")
    
    total = _calculate_total(order.get('items', []))
    discount = _calculate_discount(total, order.get('customer_type', 'regular'))
    
    order['total'] = total
    order['discount'] = discount
    order['final_price'] = total - discount
    order['status'] = 'processed'
    
    return order
