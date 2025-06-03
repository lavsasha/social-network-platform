# Statistic Service

Отвечает за сбор статистики по просмотрам, лайкам и комментариям. Обеспечивает API для получения данных о количестве
просмотров, лайков и комментариев на публикации.

## Генерация файлов с помощью proto

```
python3 -m grpc_tools.protoc -I=. --python_out=. --grpc_python_out=. ./proto/statistic.proto
```

## Запуск тестов

```
python3 -m pytest api_gateway/tests/test_statistic.py
```

```
python3 -m pytest statistic_service/tests/test_statistic_db.py
``` 

```
python3 -m pytest statistic_service/tests/test_statistic_service.py
``` 

```
python3 -m pytest statistic_service/tests/test_unit_models.py
``` 

## Подключение к БД

```
docker exec -it social-network-platform-clickhouse-1 clickhouse-client --user default --password password
```

## Просмотр логов сервиса агрегации

```
docker logs -f social-network-platform-aggregator-1
```

## Подготовка (регистрация и авторизация пользователей)

```
curl -X POST http://localhost:8080/api/v1/register \
-H "Content-Type: application/json" \
-d '{
    "login": "jane_austen",
    "password": "J@neAusten2005",
    "email": "jane.austen@example.com",
    "first_name": "Jane",
    "last_name": "Austen"
}'
```

```
curl -X POST http://localhost:8080/api/v1/login -H "Content-Type: application/json" -d '{
    "login": "jane_austen",
    "password": "J@neAusten2005"
}'
```

```
curl -X POST http://localhost:8080/api/v1/register \
-H "Content-Type: application/json" \
-d '{
    "login": "poll_mackartney",
    "password": "P@llMackartney2003",
    "email": "poll.mackartney@example.com",
    "first_name": "Poll",
    "last_name": "Mackartney"
}'
```

```
curl -X POST http://localhost:8080/api/v1/login -H "Content-Type: application/json" -d '{
    "login": "poll_mackartney",
    "password": "P@llMackartney2003"
}'
```

```
curl -X POST http://localhost:8080/api/v1/register \
-H "Content-Type: application/json" \
-d '{
    "login": "albert_einstein",
    "password": "E=mc^21905!",
    "email": "albert.einstein@example.com",
    "first_name": "Albert",
    "last_name": "Einstein"
}'
```

```
curl -X POST http://localhost:8080/api/v1/login \
-H "Content-Type: application/json" \
-d '{
    "login": "albert_einstein",
    "password": "E=mc^21905!"
}'
```

```
curl -X POST http://localhost:8080/api/v1/register \
-H "Content-Type: application/json" \
-d '{
    "login": "marie_curie",
    "password": "Rad!um1898",
    "email": "marie.curie@example.com",
    "first_name": "Marie",
    "last_name": "Curie"
}'
```

```
curl -X POST http://localhost:8080/api/v1/login \
-H "Content-Type: application/json" \
-d '{
    "login": "marie_curie",
    "password": "Rad!um1898"
}'
```

```
curl -X POST http://localhost:8080/api/v1/register \
-H "Content-Type: application/json" \
-d '{
    "login": "leo_davinci",
    "password": "MonaL!sa1503",
    "email": "leonardo.davinci@example.com",
    "first_name": "Leonardo",
    "last_name": "daVinci"
}'
```

```
curl -X POST http://localhost:8080/api/v1/login \
-H "Content-Type: application/json" \
-d '{
    "login": "leo_davinci",
    "password": "MonaL!sa1503"
}'
```

```
curl -X POST http://localhost:8080/api/v1/register \
-H "Content-Type: application/json" \
-d '{
    "login": "fyodor_dostoevsky",
    "password": "Cr!me&Pun1866",
    "email": "fyodor.dostoevsky@example.com",
    "first_name": "Fyodor",
    "last_name": "Dostoevsky"
}'
```

```
curl -X POST http://localhost:8080/api/v1/login \
-H "Content-Type: application/json" \
-d '{
    "login": "fyodor_dostoevsky",
    "password": "Cr!me&Pun1866"
}'
```

```
curl -X POST http://localhost:8080/api/v1/register \
-H "Content-Type: application/json" \
-d '{
    "login": "amelia_earhart",
    "password": "Fly!ng1932",
    "email": "amelia.earhart@example.com",
    "first_name": "Amelia",
    "last_name": "Earhart"
}'
```

```
curl -X POST http://localhost:8080/api/v1/login \
-H "Content-Type: application/json" \
-d '{
    "login": "amelia_earhart",
    "password": "Fly!ng1932"
}'
```

```
curl -X POST http://localhost:8080/api/v1/register \
-H "Content-Type: application/json" \
-d '{
    "login": "niccolo_paganini",
    "password": "V!olin1782",
    "email": "niccolo.paganini@example.com",
    "first_name": "Niccolo",
    "last_name": "Paganini"
}'
```

```
curl -X POST http://localhost:8080/api/v1/login \
-H "Content-Type: application/json" \
-d '{
    "login": "niccolo_paganini",
    "password": "V!olin1782"
}'
```

```
curl -X POST http://localhost:8080/api/v1/register \
-H "Content-Type: application/json" \
-d '{
    "login": "cleopatra",
    "password": "N!leRiver69BC",
    "email": "cleopatra@example.com",
    "first_name": "Cleopatra",
    "last_name": "VII"
}'
```

```
curl -X POST http://localhost:8080/api/v1/login \
-H "Content-Type: application/json" \
-d '{
    "login": "cleopatra",
    "password": "N!leRiver69BC"
}'
```

```
curl -X POST http://localhost:8080/api/v1/register \
-H "Content-Type: application/json" \
-d '{
    "login": "isaac_newton",
    "password": "App!e1687",
    "email": "isaac.newton@example.com",
    "first_name": "Isaac",
    "last_name": "Newton"
}'
```

```
curl -X POST http://localhost:8080/api/v1/login \
-H "Content-Type: application/json" \
-d '{
    "login": "isaac_newton",
    "password": "App!e1687"
}'
```

```
curl -X POST http://localhost:8080/api/v1/register \
-H "Content-Type: application/json" \
-d '{
    "login": "vincent_van_gogh",
    "password": "St@rryNight1889",
    "email": "vincent.vangogh@example.com",
    "first_name": "Vincent",
    "last_name": "vanGogh"
}'
```

```
curl -X POST http://localhost:8080/api/v1/login \
-H "Content-Type: application/json" \
-d '{
    "login": "vincent_van_gogh",
    "password": "St@rryNight1889"
}'
```

### Создание постов

```
curl -X POST http://localhost:8080/api/v1/posts -H "Authorization: jane_token" -H "Content-Type: application/json" -d '{
    "title": "Exploring the Universe",
    "description": "A journey through space and time",
    "is_private": false,
    "tags": ["space", "universe", "science"]
}'
```

```
curl -X POST http://localhost:8080/api/v1/posts -H "Authorization: jane_token" -H "Content-Type: application/json" -d '{
    "title": "My Personal Thoughts",
    "description": "Reflections on life",
    "is_private": true,
    "tags": ["personal", "thoughts"]
}'
```

```
curl -X POST http://localhost:8080/api/v1/posts -H "Authorization: jane_token" -H "Content-Type: application/json" -d '{
    "title": "Art and Creativity",
    "description": "The importance of art in our lives",
    "is_private": false,
    "tags": ["art", "creativity"]
}'
```

```
curl -X POST http://localhost:8080/api/v1/posts -H "Authorization: jane_token" -H "Content-Type: application/json" -d '{
    "title": "My Secret Recipe",
    "description": "A family recipe passed down through generations",
    "is_private": true,
    "tags": ["family", "recipe"]
}'
```

```
curl -X POST http://localhost:8080/api/v1/posts -H "Authorization: jane_token" -H "Content-Type: application/json" -d '{
    "title": "The Wonders of Nature",
    "description": "Exploring the beauty of the natural world",
    "is_private": false,
    "tags": ["nature", "exploration"]
}'
```

```
curl -X POST http://localhost:8080/api/v1/posts -H "Authorization: poll_token" -H "Content-Type: application/json" -d '{
    "title": "The Future of AI",
    "description": "How artificial intelligence will shape our world",
    "is_private": false,
    "tags": ["AI", "technology", "future"]
}'
```

```
curl -X POST http://localhost:8080/api/v1/posts -H "Authorization: poll_token" -H "Content-Type: application/json" -d '{
    "title": "My Thoughts on Philosophy",
    "description": "Deep thoughts on existence and reality",
    "is_private": true,
    "tags": ["philosophy", "existence"]
}'
```

```
curl -X POST http://localhost:8080/api/v1/posts -H "Authorization: poll_token" -H "Content-Type: application/json" -d '{
    "title": "Traveling Through Europe",
    "description": "My adventures across Europe",
    "is_private": false,
    "tags": ["travel", "europe"]
}'
```

```
curl -X POST http://localhost:8080/api/v1/posts -H "Authorization: poll_token" -H "Content-Type: application/json" -d '{
    "title": "Personal Growth Journey",
    "description": "Reflections on my personal development",
    "is_private": true,
    "tags": ["growth", "personal"]
}'
```

```
curl -X POST http://localhost:8080/api/v1/posts -H "Authorization: poll_token" -H "Content-Type: application/json" -d '{
    "title": "Culinary Delights",
    "description": "Exploring different cuisines around the world",
    "is_private": false,
    "tags": ["food", "cuisine", "cooking"]
}'
```

### Просмотр поста

```
curl -X POST http://localhost:8080/api/v1/posts/1/view \
  -H "Content-Type: application/json" \
  -H "Authorization: poll_token"
```

### Лайк поста

```
curl -X POST http://localhost:8080/api/v1/posts/1/like \
  -H "Authorization: poll_token"
```

### Добавление комментария к посту

```
curl -X POST http://localhost:8080/api/v1/posts/1/comment \
  -H "Content-Type: application/json" \
  -H "Authorization: poll_token" \
  -d '{
    "text": "Great post about the universe!"
  }'
```

## Тестирование сервиса статистики

### Получение статистики по посту

```
curl -X GET "http://localhost:8080/api/v1/posts/1/stats" \
-H "Authorization: smb_token" \
-H "Content-Type: application/json"
```

### Получение динамики по посту (просмотров/лайков/комментариев в зависимости от параметра)

```
curl -X GET "http://localhost:8080/api/v1/posts/1/dynamic?metric=views" \
-H "Authorization: smb_token" \
-H "Content-Type: application/json"
```

### Получение топ-10 постов по количеству лайков, комментариев или просмотров

```
curl -X GET "http://localhost:8080/api/v1/posts/top?metric=likes" \
-H "Authorization: smb_token" \
-H "Content-Type: application/json"
```

### Получение топ-10 пользователей по количеству лайков, комментариев или просмотров

```
curl -X GET "http://localhost:8080/api/v1/users/top?metric=comments" \
-H "Authorization: smb_token" \
-H "Content-Type: application/json"
```

### Ручное добавление строк в таблицу post_daily_stats (если нужно проверить корректность метода динамики)

```
INSERT INTO post_daily_stats (post_id, date, views_count, likes_count, comments_count) VALUES
('1', '2025-05-01', 5, 2, 1),
('1', '2025-05-02', 10, 3, 0),
('1', '2025-05-03', 8, 5, 2);
```