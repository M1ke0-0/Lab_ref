# Отчет по лабораторной работе №2
## Рефакторинг приложений с изучением модульного тестирования

**Студент:** [ФИО Студента]
**Группа:** [Группа]

### 1. Цели работы
1. Изучить основные принципы и задачи модульного тестирования.
2. Научиться разрабатывать модульные тесты для проверки функциональности.
3. Применить модульное тестирование для контроля качества кода в процессе рефакторинга.
4. Освоить использование инструментов для модульного тестирования (`pytest`).

### 2. Исходное состояние кода
Для выполнения лабораторной работы был выбран небольшой модуль `order_processor.py`, который вычисляет итоговую стоимость заказа, применяет скидки в зависимости от типа клиента и обновляет статус заказа. 

**Проблемы исходного кода:**
- Функция `process_order` слишком велика и берет на себя много ответственностей (вычисление суммы, расчет скидок, обновление словаря).
- Итерация по элементам реализована через конструкции `for i in range(len(...))`, что не является Python-way.
- Отсутствуют аннотации типов (type hints).
- "Магические" числа скидок жестко зашиты в код без пояснений.
- Обращение к элементам словаря идет напрямую без использования `.get()`, что может вызвать `KeyError` при отсутствии ключей.

**Исходный код `src/order_processor.py` (до рефакторинга):**
```python
def process_order(order):
    if order['status'] != 'new':
        raise Exception("Order is not new")
    
    total = 0
    for i in range(len(order['items'])):
        item = order['items'][i]
        price = item['price']
        qty = item['quantity']
        if price < 0 or qty < 0:
            raise ValueError("Invalid price or quantity")
        total += price * qty
    
    discount = 0.0
    if order['customer_type'] == 'vip':
        discount = total * 0.1
    elif order['customer_type'] == 'premium':
        discount = total * 0.05
    
    if total > 1000:
        discount += total * 0.02
        
    final_price = total - discount
    
    order['total'] = total
    order['discount'] = discount
    order['final_price'] = final_price
    order['status'] = 'processed'
    
    return order
```

### 3. Модульные тесты
Для проверки функциональности были написаны тесты с использованием фреймворка `pytest`. 
Основные тестовые сценарии:
1. `test_process_order_basic` — проверка базового расчета.
2. `test_order_not_new` — проверка возникновения исключения, если заказ не в статусе 'new'.
3. `test_invalid_price_qty` — проверка исключения при отрицательной цене или количестве.
4. `test_vip_discount` — проверка начисления скидки 10% для VIP клиентов.
5. `test_large_order_discount` — проверка начисления скидки 2% при сумме больше 1000.
6. `test_vip_and_large_order_discount` — суммирование скидок.

**Файл тестов `tests/test_order_processor.py`:**
```python
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
    assert result['discount'] == 30.0
    assert result['final_price'] == 1470.0

def test_vip_and_large_order_discount():
    order = {
        'id': 6, 
        'items': [{'name': 'item', 'price': 1500, 'quantity': 1}], 
        'status': 'new', 
        'customer_type': 'vip'
    }
    result = process_order(order)
    assert result['discount'] == 180.0
    assert result['final_price'] == 1320.0
```

### 4. Внесенные изменения (Рефакторинг)
Код был отрефакторен со следующими улучшениями:
- **Разделение ответственностей (Single Responsibility Principle):** логика расчета суммы вынесена в отдельную функцию `_calculate_total()`, а логика расчета скидок — в `_calculate_discount()`. Это делает основную функцию `process_order` компактной и понятной.
- **Типизация:** добавлены аннотации типов `Dict`, `Any`, `List` из модуля `typing`, что упростит анализ кода IDE и предотвращает ошибки типов.
- **Безопасность словарей:** вместо прямого обращения (например `item['price']`) использован метод `item.get('price', 0)`, который защищает от прерываний программы в случае отсутствия ключей.
- **Документирование:** были добавлены комментарии (docstrings) для описания назначения функций.
- **Итерация:** заменили `range(len(...))` на прямую итерацию по элементам коллекции `for item in items:`.

**Код `src/order_processor.py` (после рефакторинга):**
```python
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
```

### 5. Результаты выполнения тестов
Тесты запускались до и после рефакторинга.

**Результат до рефакторинга:**
```text
tests/test_order_processor.py::test_process_order_basic PASSED           [ 16%]
tests/test_order_processor.py::test_order_not_new PASSED                 [ 33%]
tests/test_order_processor.py::test_invalid_price_qty PASSED             [ 50%]
tests/test_order_processor.py::test_vip_discount PASSED                  [ 66%]
tests/test_order_processor.py::test_large_order_discount PASSED          [ 83%]
tests/test_order_processor.py::test_vip_and_large_order_discount PASSED  [100%]

============================== 6 passed in 0.01s ==============================
```

**Результат после рефакторинга:**
```text
tests/test_order_processor.py::test_process_order_basic PASSED           [ 16%]
tests/test_order_processor.py::test_order_not_new PASSED                 [ 33%]
tests/test_order_processor.py::test_invalid_price_qty PASSED             [ 50%]
tests/test_order_processor.py::test_vip_discount PASSED                  [ 66%]
tests/test_order_processor.py::test_large_order_discount PASSED          [ 83%]
tests/test_order_processor.py::test_vip_and_large_order_discount PASSED  [100%]

============================== 6 passed in 0.02s ==============================
```

**Вывод:** Рефакторинг был проведен успешно, структура кода значительно улучшена без нарушения его функциональности. Все модульные тесты прошли успешно как до рефакторинга, так и после него.
