import pytest
from src.order_processor import process_order

def test_process_order_basic():
    order = {
        'id': 1, 
        'items': [{'name': 'item1', 'price': 100, 'quantity': 2}], 
        'status': 'new', 
        'customer_type': 'regular'
    }
    result = process_order(order)
    assert result['total'] == 200
    assert result['discount'] == 0
    assert result['final_price'] == 200
    assert result['status'] == 'processed'

def test_order_not_new():
    order = {'id': 2, 'items': [], 'status': 'processed', 'customer_type': 'regular'}
    with pytest.raises(Exception, match="Order is not new"):
        process_order(order)

def test_invalid_price_qty():
    order = {
        'id': 3, 
        'items': [{'name': 'item', 'price': -10, 'quantity': 1}], 
        'status': 'new', 
        'customer_type': 'regular'
    }
    with pytest.raises(ValueError, match="Invalid price or quantity"):
        process_order(order)

def test_vip_discount():
    order = {
        'id': 4, 
        'items': [{'name': 'item', 'price': 500, 'quantity': 1}], 
        'status': 'new', 
        'customer_type': 'vip'
    }
    result = process_order(order)
    assert result['discount'] == 50.0
    assert result['final_price'] == 450.0

def test_large_order_discount():
    order = {
        'id': 5, 
        'items': [{'name': 'item', 'price': 1500, 'quantity': 1}], 
        'status': 'new', 
        'customer_type': 'regular'
    }
    result = process_order(order)
    assert result['discount'] == 30.0  # 2% of 1500
    assert result['final_price'] == 1470.0

def test_vip_and_large_order_discount():
    order = {
        'id': 6, 
        'items': [{'name': 'item', 'price': 1500, 'quantity': 1}], 
        'status': 'new', 
        'customer_type': 'vip'
    }
    result = process_order(order)
    assert result['discount'] == 180.0  # 10% + 2%
    assert result['final_price'] == 1320.0
