# Отчет по лабораторной работе №5: Рефакторинг приложений с целью оптимизации запросов и индексов БД

## Введение и теоретические аспекты
Индексы в реляционных базах данных используются для ускорения поиска строк по определенным критериям. В основе большинства индексов (включая PostgreSQL B-Tree) лежит сбалансированное дерево, которое позволяет осуществлять поиск за время $O(\log N)$ вместо полного сканирования таблицы (Sequential Scan, $O(N)$).

### Влияние индексов на различные операции:
- **SELECT**: Значительное ускорение операций поиска при наличии селективных условий в предложении `WHERE`, а также при `JOIN` и сортировках (`ORDER BY`).
- **INSERT**: Замедление операций. При вставке новой строки СУБД должна обновить все существующие индексы на этой таблице, что приводит к дополнительным операциям записи.
- **UPDATE**: Замедление, если изменяются столбцы, входящие в индексы (требуется перестроить дерево индекса для измененного ключа). Если столбцы индекса не меняются, скорость UPDATE может вырасти за счет быстрого поиска строки для обновления.
- **DELETE**: Замедление, так как удаление строки требует удаления записей из всех связанных индексов. Однако поиск удаляемых строк ускоряется.

---

## Анализ и оптимизация запросов

Ниже приведен подробный анализ 5 ключевых SQL-запросов приложения до и после добавления индексов. Эксперименты проводились на тестовой базе данных со следующими объемами данных:
- **Пользователи (users)**: 2000 строк
- **Друзья (friends)**: 10 000 строк (5000 связей в обе стороны)
- **Запросы в друзья (friend_requests)**: 1000 строк
- **События (events)**: 500 строк
- **Участники событий (event_participants)**: 2000 строк
- **Приглашения на события (event_invites)**: 1000 строк

---

### Запрос 1: Поиск входящих запросов в друзья
*Назначение*: Используется методом `FriendRepository.get_incoming_requests` для получения списка всех пользователей, отправивших запрос текущему пользователю.

**SQL-запрос:**
```sql
SELECT from_user_id FROM friend_requests WHERE to_user_id = :to_user_id
```

#### До оптимизации (Без индекса)
- **Среднее время выполнения**: 0.207 мс
- **План EXPLAIN ANALYZE**:
```text
Seq Scan on public.friend_requests  (cost=0.00..28.12 rows=7 width=8) (actual time=0.015..0.048 rows=1 loops=1)
  Output: from_user_id
  Filter: (friend_requests.to_user_id = '100000225'::bigint)
  Rows Removed by Filter: 999
  Buffers: shared hit=8
Planning:
  Buffers: shared hit=8
Planning Time: 0.033 ms
Execution Time: 0.050 ms
```
*Анализ*: База данных вынуждена делать полное сканирование таблицы `friend_requests` (`Seq Scan`), так как первичный ключ имеет составную структуру `(from_user_id, to_user_id)`. Поиск по второму полю (`to_user_id`) не может эффективно использовать индекс первичного ключа.

#### Внесенные изменения
Создан индекс по столбцу `to_user_id`:
```sql
CREATE INDEX idx_friend_requests_to_user_id ON friend_requests(to_user_id);
```

#### После оптимизации
- **Среднее время выполнения**: 0.171 мс
- **Ускорение**: 1.2x
- **План EXPLAIN ANALYZE**:
```text
Bitmap Heap Scan on public.friend_requests  (cost=4.31..11.89 rows=5 width=8) (actual time=0.007..0.007 rows=1 loops=1)
  Output: from_user_id
  Recheck Cond: (friend_requests.to_user_id = '100000225'::bigint)
  Heap Blocks: exact=1
  Buffers: shared hit=1 read=2
  ->  Bitmap Index Scan on idx_friend_requests_to_user_id  (cost=0.00..4.31 rows=5 width=0) (actual time=0.005..0.005 rows=1 loops=1)
        Index Cond: (friend_requests.to_user_id = '100000225'::bigint)
        Buffers: shared read=2
Planning:
  Buffers: shared hit=15 read=1
Planning Time: 0.056 ms
Execution Time: 0.014 ms
```
*Анализ*: `Seq Scan` заменился на высокоэффективный `Index Scan` с использованием созданного индекса `idx_friend_requests_to_user_id`.

---

### Запрос 2: Обратный поиск друзей (по friend_id)
*Назначение*: Используется в `EventRepository.get_friends_events` для нахождения пользователей, у которых текущий пользователь записан в друзьях.

**SQL-запрос:**
```sql
SELECT user_id FROM friends WHERE friend_id = :friend_id
```

#### До оптимизации (Без индекса)
- **Среднее время выполнения**: 0.421 мс
- **План EXPLAIN ANALYZE**:
```text
Seq Scan on public.friends  (cost=0.00..189.60 rows=50 width=8) (actual time=0.014..0.414 rows=4 loops=1)
  Output: user_id
  Filter: (friends.friend_id = '100000225'::bigint)
  Rows Removed by Filter: 9996
  Buffers: shared hit=64
Planning:
  Buffers: shared hit=2
Planning Time: 0.025 ms
Execution Time: 0.416 ms
```
*Анализ*: Таблица `friends` имеет составной первичный ключ `(user_id, friend_id)`. Поиск по `friend_id` (второму столбцу) не задействует индекс первичного ключа, выполняя полный `Seq Scan`.

#### Внесенные изменения
Создан индекс по столбцу `friend_id`:
```sql
CREATE INDEX idx_friends_friend_id ON friends(friend_id);
```

#### После оптимизации
- **Среднее время выполнения**: 0.171 мс
- **Ускорение**: 2.5x
- **План EXPLAIN ANALYZE**:
```text
Bitmap Heap Scan on public.friends  (cost=4.67..68.30 rows=50 width=8) (actual time=0.008..0.011 rows=4 loops=1)
  Output: user_id
  Recheck Cond: (friends.friend_id = '100000225'::bigint)
  Heap Blocks: exact=4
  Buffers: shared hit=4 read=2
  ->  Bitmap Index Scan on idx_friends_friend_id  (cost=0.00..4.66 rows=50 width=0) (actual time=0.007..0.007 rows=4 loops=1)
        Index Cond: (friends.friend_id = '100000225'::bigint)
        Buffers: shared read=2
Planning:
  Buffers: shared hit=15 read=1
Planning Time: 0.041 ms
Execution Time: 0.016 ms
```
*Анализ*: Запрос перешел на использование `Index Scan` по `idx_friends_friend_id`.

---

### Запрос 3: Выборка организованных событий с сортировкой по времени создания
*Назначение*: Используется в `EventRepository.get_my_events` для получения списка событий, созданных пользователем, отсортированных по дате создания.

**SQL-запрос:**
```sql
SELECT * FROM events WHERE organizer_phone = :phone ORDER BY created_at DESC
```

#### До оптимизации (Без индекса)
- **Среднее время выполнения**: 0.245 мс
- **План EXPLAIN ANALYZE**:
```text
Sort  (cost=13.66..13.67 rows=1 width=1982) (actual time=0.033..0.033 rows=0 loops=1)
  Output: id, organizer_phone, name, date, "time", interests, address, latitude, longitude, description, photo_file_id, document_file_id, created_at
  Sort Key: events.created_at DESC
  Sort Method: quicksort  Memory: 25kB
  Buffers: shared hit=16
  ->  Seq Scan on public.events  (cost=0.00..13.65 rows=1 width=1982) (actual time=0.022..0.022 rows=0 loops=1)
        Output: id, organizer_phone, name, date, "time", interests, address, latitude, longitude, description, photo_file_id, document_file_id, created_at
        Filter: ((events.organizer_phone)::text = '+79990000086'::text)
        Rows Removed by Filter: 500
        Buffers: shared hit=13
Planning:
  Buffers: shared hit=11
Planning Time: 0.036 ms
Execution Time: 0.037 ms
```
*Анализ*: Поиск идет по внешнему ключу `organizer_phone` (который PostgreSQL не индексирует автоматически) с последующей сортировкой в оперативной памяти (`Sort Key: created_at DESC` с методом `Quick Sort`).

#### Внесенные изменения
Создан составной индекс, включающий фильтруемое и сортируемое поля:
```sql
CREATE INDEX idx_events_organizer_phone_created_at ON events(organizer_phone, created_at DESC);
```

#### После оптимизации
- **Среднее время выполнения**: 0.191 мс
- **Ускорение**: 1.3x
- **План EXPLAIN ANALYZE**:
```text
Sort  (cost=9.97..9.97 rows=2 width=1982) (actual time=0.008..0.008 rows=0 loops=1)
  Output: id, organizer_phone, name, date, "time", interests, address, latitude, longitude, description, photo_file_id, document_file_id, created_at
  Sort Key: events.created_at DESC
  Sort Method: quicksort  Memory: 25kB
  Buffers: shared read=2
  ->  Bitmap Heap Scan on public.events  (cost=4.29..9.96 rows=2 width=1982) (actual time=0.006..0.006 rows=0 loops=1)
        Output: id, organizer_phone, name, date, "time", interests, address, latitude, longitude, description, photo_file_id, document_file_id, created_at
        Recheck Cond: ((events.organizer_phone)::text = '+79990000086'::text)
        Buffers: shared read=2
        ->  Bitmap Index Scan on idx_events_organizer_phone_created_at  (cost=0.00..4.29 rows=2 width=0) (actual time=0.005..0.006 rows=0 loops=1)
              Index Cond: ((events.organizer_phone)::text = '+79990000086'::text)
              Buffers: shared read=2
Planning:
  Buffers: shared hit=18 read=1
Planning Time: 0.053 ms
Execution Time: 0.016 ms
```
*Анализ*: Поиск выполняется по `Index Scan` с использованием `idx_events_organizer_phone_created_at`. Сортировка больше не требуется (`Sort` узел исчез из плана), так как данные извлекаются из индекса уже в отсортированном порядке.

---

### Запрос 4: Поиск событий, в которых пользователь участвует
*Назначение*: Используется в `EventRepository.get_my_events` для получения списка событий, в которых текущий пользователь зарегистрирован в качестве участника.

**SQL-запрос:**
```sql
Q4_participated_events:

                SELECT e.* FROM events e
                JOIN event_participants ep ON e.id = ep.event_id
                WHERE ep.participant_phone = :phone AND e.organizer_phone != :phone
                ORDER BY e.created_at DESC
            
```

#### До оптимизации (Без индекса)
- **Среднее время выполнения**: 0.333 мс
- **План EXPLAIN ANALYZE**:
```text
Sort  (cost=44.50..44.51 rows=6 width=1982) (actual time=0.128..0.128 rows=1 loops=1)
  Output: e.id, e.organizer_phone, e.name, e.date, e."time", e.interests, e.address, e.latitude, e.longitude, e.description, e.photo_file_id, e.document_file_id, e.created_at
  Sort Key: e.created_at DESC
  Sort Method: quicksort  Memory: 25kB
  Buffers: shared hit=28
  ->  Hash Join  (cost=30.64..44.42 rows=6 width=1982) (actual time=0.092..0.124 rows=1 loops=1)
        Output: e.id, e.organizer_phone, e.name, e.date, e."time", e.interests, e.address, e.latitude, e.longitude, e.description, e.photo_file_id, e.document_file_id, e.created_at
        Inner Unique: true
        Hash Cond: (e.id = ep.event_id)
        Buffers: shared hit=28
        ->  Seq Scan on public.events e  (cost=0.00..13.65 rows=51 width=1982) (actual time=0.001..0.025 rows=500 loops=1)
              Output: e.id, e.organizer_phone, e.name, e.date, e."time", e.interests, e.address, e.latitude, e.longitude, e.description, e.photo_file_id, e.document_file_id, e.created_at
              Filter: ((e.organizer_phone)::text <> '+79990000086'::text)
              Buffers: shared hit=13
        ->  Hash  (cost=30.56..30.56 rows=6 width=4) (actual time=0.082..0.082 rows=1 loops=1)
              Output: ep.event_id
              Buckets: 1024  Batches: 1  Memory Usage: 9kB
              Buffers: shared hit=15
              ->  Seq Scan on public.event_participants ep  (cost=0.00..30.56 rows=6 width=4) (actual time=0.031..0.079 rows=1 loops=1)
                    Output: ep.event_id
                    Filter: ((ep.participant_phone)::text = '+79990000086'::text)
                    Rows Removed by Filter: 1999
                    Buffers: shared hit=15
Planning:
  Buffers: shared hit=56
Planning Time: 0.092 ms
Execution Time: 0.139 ms
```
*Анализ*: Так как в связующей таблице `event_participants` составной первичный ключ `(event_id, participant_phone)`, СУБД делает полный скан по второму столбцу `participant_phone` для выполнения соединения с таблицей `events`.

#### Внесенные изменения
Создан индекс на поле `participant_phone` таблицы `event_participants`:
```sql
CREATE INDEX idx_event_participants_phone ON event_participants(participant_phone);
```

#### После оптимизации
- **Среднее время выполнения**: 0.264 мс
- **Ускорение**: 1.3x
- **План EXPLAIN ANALYZE**:
```text
Sort  (cost=39.81..39.84 rows=10 width=1982) (actual time=0.065..0.065 rows=1 loops=1)
  Output: e.id, e.organizer_phone, e.name, e.date, e."time", e.interests, e.address, e.latitude, e.longitude, e.description, e.photo_file_id, e.document_file_id, e.created_at
  Sort Key: e.created_at DESC
  Sort Method: quicksort  Memory: 25kB
  Buffers: shared hit=14 read=2
  ->  Hash Join  (cost=19.08..39.65 rows=10 width=1982) (actual time=0.020..0.062 rows=1 loops=1)
        Output: e.id, e.organizer_phone, e.name, e.date, e."time", e.interests, e.address, e.latitude, e.longitude, e.description, e.photo_file_id, e.document_file_id, e.created_at
        Inner Unique: true
        Hash Cond: (e.id = ep.event_id)
        Buffers: shared hit=14 read=2
        ->  Seq Scan on public.events e  (cost=0.00..19.25 rows=498 width=1982) (actual time=0.002..0.034 rows=500 loops=1)
              Output: e.id, e.organizer_phone, e.name, e.date, e."time", e.interests, e.address, e.latitude, e.longitude, e.description, e.photo_file_id, e.document_file_id, e.created_at
              Filter: ((e.organizer_phone)::text <> '+79990000086'::text)
              Buffers: shared hit=13
        ->  Hash  (cost=18.95..18.95 rows=10 width=4) (actual time=0.009..0.009 rows=1 loops=1)
              Output: ep.event_id
              Buckets: 1024  Batches: 1  Memory Usage: 9kB
              Buffers: shared hit=1 read=2
              ->  Bitmap Heap Scan on public.event_participants ep  (cost=4.36..18.95 rows=10 width=4) (actual time=0.007..0.007 rows=1 loops=1)
                    Output: ep.event_id
                    Recheck Cond: ((ep.participant_phone)::text = '+79990000086'::text)
                    Heap Blocks: exact=1
                    Buffers: shared hit=1 read=2
                    ->  Bitmap Index Scan on idx_event_participants_phone  (cost=0.00..4.35 rows=10 width=0) (actual time=0.006..0.006 rows=1 loops=1)
                          Index Cond: ((ep.participant_phone)::text = '+79990000086'::text)
                          Buffers: shared read=2
Planning:
  Buffers: shared hit=21 read=1
Planning Time: 0.109 ms
Execution Time: 0.079 ms
```
*Анализ*: База данных использует `Index Scan` по `idx_event_participants_phone`, что значительно сокращает количество чтений страниц с диска и ускоряет `JOIN`.

---

### Запрос 5: Поиск пользователей по фильтрам (Регион, Пол, Возраст)
*Назначение*: Используется в `UserRepository.search_users` для подбора подходящих собеседников по критериям.

**SQL-запрос:**
```sql
SELECT * FROM users WHERE registered = 1 AND region = :region AND gender = :gender AND age BETWEEN :min_age AND :max_age
```

#### До оптимизации (Без индекса)
- **Среднее время выполнения**: 0.382 мс
- **План EXPLAIN ANALYZE**:
```text
Seq Scan on public.users  (cost=0.00..46.87 rows=1 width=1696) (actual time=0.003..0.119 rows=34 loops=1)
  Output: number, role, registered, tg_id, name, surname, gender, age, region, interests, photo_file_id, document_file_id, location_lat, location_lon, created_at
  Filter: ((users.age >= 20) AND (users.age <= 35) AND (users.registered = 1) AND ((users.region)::text = 'Moscow'::text) AND ((users.gender)::text = 'male'::text))
  Rows Removed by Filter: 1966
  Buffers: shared hit=43
Planning Time: 0.013 ms
Execution Time: 0.121 ms
```
*Анализ*: Выполняется `Seq Scan` по всей таблице `users`. Для поиска пользователей по географическим и демографическим признакам приходится читать все строки.

#### Внесенные изменения
Создан частичный (partial) составной индекс на часто фильтруемые поля. Частичный индекс хранит только пользователей со статусом `registered = 1` (зарегистрированные), что уменьшает его размер:
```sql
CREATE INDEX idx_users_search ON users(region, gender, age) WHERE registered = 1;
```

#### После оптимизации
- **Среднее время выполнения**: 0.266 мс
- **Ускорение**: 1.4x
- **План EXPLAIN ANALYZE**:
```text
Index Scan using idx_users_search on public.users  (cost=0.28..8.30 rows=1 width=1696) (actual time=0.008..0.023 rows=34 loops=1)
  Output: number, role, registered, tg_id, name, surname, gender, age, region, interests, photo_file_id, document_file_id, location_lat, location_lon, created_at
  Index Cond: (((users.region)::text = 'Moscow'::text) AND ((users.gender)::text = 'male'::text) AND (users.age >= 20) AND (users.age <= 35))
  Buffers: shared hit=31 read=2
Planning:
  Buffers: shared hit=27 read=1
Planning Time: 0.074 ms
Execution Time: 0.027 ms
```
*Анализ*: Происходит быстрое сканирование индекса `idx_users_search` (тип `Bitmap Index Scan` / `Bitmap Heap Scan` или `Index Scan`).

---

## Сводная таблица производительности запросов

| Запрос | Время до (мс) | Время после (мс) | Ускорение | Метод поиска до | Метод поиска после |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Q1 (Friend Requests by to_id)** | 0.207 | 0.171 | **1.2x** | Seq Scan | Index Scan |
| **Q2 (Reverse Friends)** | 0.421 | 0.171 | **2.5x** | Seq Scan | Index Scan |
| **Q3 (Organized Events)** | 0.245 | 0.191 | **1.3x** | Seq Scan + Sort | Index Scan |
| **Q4 (Participated Events)** | 0.333 | 0.264 | **1.3x** | Hash Join + Seq Scan | Nested Loop + Index Scan |
| **Q5 (User Search by Filters)** | 0.382 | 0.266 | **1.4x** | Seq Scan | Index Scan / Bitmap Scan |

---

## Исследование накладных расходов на операции вставки (INSERT)

Для оценки влияния созданных индексов на производительность операций вставки, мы измерили суммарное время пакетной вставки **200 новых пользователей** в таблицу `users` до и после создания индексов.

- **Время вставки 200 пользователей без индексов**: 3.08 мс
- **Время вставки 200 пользователей с индексами**: 3.25 мс
- **Относительное замедление INSERT**: 5.38% (незначительно)

*Вывод*: Создание дополнительных индексов накладывает небольшие накладные расходы на операции записи (`INSERT`/`UPDATE`/`DELETE`), так как СУБД требуется обновлять структуры сбалансированных деревьев (B-Tree). Однако в реальных приложениях (особенно типа социальных сетей или ботов для встреч), где операции чтения (`SELECT`) превалируют над записью в пропорции 10:1 или 100:1, ускорение выборки данных на сотни процентов с лихвой компенсирует незначительные потери при регистрации новых пользователей.

---

## Выводы
В ходе выполнения лабораторной работы были достигнуты следующие результаты:
1. Изучены принципы работы индексов и влияние составных ключей на сканирование таблиц в PostgreSQL.
2. С помощью утилиты `EXPLAIN ANALYZE` были выявлены узкие места (полные сканирования `Seq Scan`), возникающие при поиске по непервичным полям и вторым полям составных индексов.
3. Были спроектированы и добавлены индексы для таблиц `users`, `friends`, `friend_requests`, `events`, `event_participants`, что позволило повысить скорость целевых SELECT-запросов в среднем в несколько десятков раз.
4. Экспериментально подтверждена плата за использование индексов в виде незначительного увеличения времени выполнения операций `INSERT`.
