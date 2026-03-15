from src.hotel_booking import calc_b_and_p

def test_standard_room_normal():
    # 2 days, standard(1), no vip, no holiday
    price = calc_b_and_p(2, 1, False, False)
    # 1000 * 2 = 2000. Tax: + 10% = 2200
    assert price == 2200

def test_deluxe_room_holiday():
    # 1 day, deluxe(2), no vip, holiday
    price = calc_b_and_p(1, 2, False, True)
    # 2000 * 1 = 2000. Tax: + 15% = 2300. Holiday: + 500 = 2800
    assert price == 2800

def test_suite_vip_normal():
    # 3 days, suite(3), vip, no holiday
    price = calc_b_and_p(3, 3, True, False)
    # 5000 * 3 = 15000. Tax: + 20% = 18000. VIP: - 10% = 16200
    assert price == 16200

def test_standard_vip_holiday():
    # 2 days, standard(1), vip, holiday
    price = calc_b_and_p(2, 1, True, True)
    # 1000 * 2 = 2000. Tax: + 10% = 2200. Holiday: + 300*2 = 2800. VIP: - 5% = 2660
    assert price == 2660
