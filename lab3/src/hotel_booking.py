from dataclasses import dataclass
from typing import Optional

class RoomType:
    STANDARD = 1
    DELUXE = 2
    SUITE = 3

@dataclass
class RoomPricing:
    base_rate: float
    tax_rate: float
    holiday_surcharge: float

ROOM_PRICING_MAP = {
    RoomType.STANDARD: RoomPricing(base_rate=1000.0, tax_rate=0.10, holiday_surcharge=300.0),
    RoomType.DELUXE: RoomPricing(base_rate=2000.0, tax_rate=0.15, holiday_surcharge=500.0),
    RoomType.SUITE: RoomPricing(base_rate=5000.0, tax_rate=0.20, holiday_surcharge=1000.0),
}

def calculate_base_price(days: int, room_type: int) -> float:
    pricing = ROOM_PRICING_MAP.get(room_type)
    if not pricing:
        raise ValueError(f"Unknown room type: {room_type}")
    return pricing.base_rate * days

def calculate_taxes(base_price: float, room_type: int) -> float:
    pricing = ROOM_PRICING_MAP.get(room_type)
    return base_price * pricing.tax_rate

def calculate_holiday_surcharge(days: int, room_type: int, is_holiday: bool) -> float:
    if not is_holiday:
        return 0.0
    pricing = ROOM_PRICING_MAP.get(room_type)
    return pricing.holiday_surcharge * days

def calculate_vip_discount(total_so_far: float, room_type: int, is_vip: bool) -> float:
    if not is_vip:
        return 0.0
    discount_rate = 0.10 if room_type == RoomType.SUITE else 0.05
    return total_so_far * discount_rate

def calc_b_and_p(days: int, room_type: int, is_vip: bool, is_holiday: bool) -> float:
    """Calculate booking price. Maintained signature for backwards compatibility."""
    
    base_price = calculate_base_price(days, room_type)
    tax = calculate_taxes(base_price, room_type)
    
    total = base_price + tax
    total += calculate_holiday_surcharge(days, room_type, is_holiday)
    total -= calculate_vip_discount(total, room_type, is_vip)
    
    return total

def print_receipt(customer_name: str, reservation_id: str, days: int, room_type: int, is_vip: bool, is_holiday: bool) -> float:
    price = calc_b_and_p(days, room_type, is_vip, is_holiday)
    
    receipt_lines = [
        "-" * 25,
        f"Name: {customer_name}",
        f"Res ID: {reservation_id}",
        f"Total Price: {price:.2f}",
        "-" * 25
    ]
    
    for line in receipt_lines:
        print(line)
        
    return price
