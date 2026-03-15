# Отчет по лабораторной работе №3
## Изучение рефакторинга приложений

**Студент:** [ФИО Студента]
**Группа:** [Группа]

### 1. Цели работы
1. Ознакомиться с основными принципами и задачами рефакторинга.
2. Научиться выявлять проблемные участки кода (code smells) и устранять их.
3. Применить техники рефакторинга для улучшения читаемости, структуры и производительности кода.
4. Развить навыки анализа существующего кода.

### 2. Исходное состояние кода (Code Smells)
В качестве исходного примера был разработан скрипт системы бронирования отелей `src/hotel_booking.py`.

**Анализ исходного кода выявил следующие "запахи кода" (Code Smells):**

1. **Плохие имена (Poor Names):** 
   - Функция называется `calc_b_and_p` (совершенно неясно, что она делает).
   - Аргументы: `d, t, v, p` (без комментариев невозможно понять, что `d` это days, а `v` — is_vip).
   - Внутри используется переменная `bp`.

2. **Магические числа (Magic Numbers):**
   - В коде жестко зашиты числа типа `1, 2, 3` для типов комнат, а также множители `0.1`, `300`, `1000` без объяснения того, откуда они берутся.

3. **Монструозная функция / Длинный метод (Long Method):**
   - Вся логика расчета стоимости (со ставками, налогами, праздниками, скидками) засунута в одну длинную функцию, которая делает слишком много вещей.

4. **Дублирование кода (Duplicated Code):**
   - Постоянно повторяется `bp = bp + ...` или блоки `if t == 1`, `elif t == 2` в разных местах для разных расчетов.

**Исходный код `src/hotel_booking.py` (до рефакторинга):**
```python
def calc_b_and_p(d, t, v, p):
    # bad function name, bad variables:
    # d = days, t = room type, v = is_vip, p = is_holiday
    
    # booking price
    bp = 0
    if t == 1: # 1 = standard
        bp = 1000 * d
    elif t == 2: # 2 = deluxe
        bp = 2000 * d
    elif t == 3: # 3 = suite
        bp = 5000 * d
        
    # add tax
    if t == 1:
        bp = bp + (bp * 0.1)
    elif t == 2:
        bp = bp + (bp * 0.15)
...
# (Полный код см. в коммитах проекта)
```

### 3. Тестирование до рефакторинга
Чтобы гарантировать безопасность рефакторинга, были созданы unit-тесты (`tests/test_hotel_booking.py`), проверяющие 4 различных сценария бронирования.
```text
tests/test_hotel_booking.py::test_standard_room_normal PASSED           [ 25%]
tests/test_hotel_booking.py::test_deluxe_room_holiday PASSED            [ 50%]
tests/test_hotel_booking.py::test_suite_vip_normal PASSED               [ 75%]
tests/test_hotel_booking.py::test_standard_vip_holiday PASSED           [100%]
```

### 4. Внесенные изменения (Процесс Рефакторинга)

Были применены следующие техники рефакторинга:

1. **Переименование переменных и методов (Rename Method/Variable):**
   - Переменные переименованы в осмысленные: `days`, `room_type`, `is_vip`, `is_holiday`.
   - В главной функции аргументы и названия стали четкими, отражающими бизнес-логику.

2. **Замена магических чисел на константы (Replace Magic Number with Symbolic Constant):**
   - Введен класс `RoomType` (с константами `STANDARD = 1`, `DELUXE = 2`, `SUITE = 3`).

3. **Извлечение классов/структур данных (Extract Class):**
   - Вместо россыпи `if-elif` создана структура `RoomPricing` (`dataclass`), хранящая базовую цену, налог и доплату за праздники в едином объекте.
   - Создан словарь `ROOM_PRICING_MAP`, который связывает тип комнаты с её ценовой политикой.

4. **Извлечение методов (Extract Method):**
   - Логика была разбита на независимые маленькие функции:
     - `calculate_base_price()`
     - `calculate_taxes()`
     - `calculate_holiday_surcharge()`
     - `calculate_vip_discount()`
   - Теперь каждая функция отвечает ровно за один аспект расчета (Соблюден принцип единой ответственности - SRP).

### 5. Итоговое состояние кода

**Код `src/hotel_booking.py` (после рефакторинга):**
```python
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
```

### 6. Проверка работоспособности
После структурных изменений тесты были запущены заново.
```text
tests/test_hotel_booking.py::test_standard_room_normal PASSED           [ 25%]
tests/test_hotel_booking.py::test_deluxe_room_holiday PASSED            [ 50%]
tests/test_hotel_booking.py::test_suite_vip_normal PASSED               [ 75%]
tests/test_hotel_booking.py::test_standard_vip_holiday PASSED           [100%]
```
Все тесты прошли. Оптимизация структуры и внедрение паттернов проектирования не затронуло бизнес-логику приложения, выполнив главную цель рефакторинга.
