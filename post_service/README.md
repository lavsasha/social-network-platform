# Post Service
Отвечает за хранение данных о постах и комментариях, управляет их созданием и обновлением.

## Генерация файлов с помощью proto
```
python3 -m grpc_tools.protoc -I=. --python_out=. --grpc_python_out=. ./proto/post.proto
```

## Подключение к БД
```
docker exec -it social-network-platform-db-1 psql -U user -d post_db
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
    "login": "jane_austen",
    "password": "J@neAusten2005"
}'
```
```
curl -X POST http://localhost:8080/api/v1/login -H "Content-Type: application/json" -d '{
    "login": "poll_mackartney",
    "password": "P@llMackartney2003"
}'
```

## Тестирование сервиса постов
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

### Получение публичного поста (другой пользователь)
```
curl -X GET http://localhost:8080/api/v1/posts/1 \
-H "Authorization: poll_token"
```

### Попытка получения приватного поста (другой пользователь - должен получить 404)
```
curl -X GET http://localhost:8080/api/v1/posts/2 \
-H "Authorization: poll_token"
```

### Получение собственного приватного поста
```
curl -X GET http://localhost:8080/api/v1/posts/2 \
-H "Authorization: jane_token"
```

### Успешное обновление поста (владельцем)
```
curl -X PUT http://localhost:8080/api/v1/posts/1 \
-H "Authorization: jane_token" \
-H "Content-Type: application/json" \
-d '{
    "title": "Updated Public Post",
    "description": "This post has been updated",
    "is_private": false
}'
```

### Попытка обновления чужого поста (должна завершиться ошибкой)
```
curl -X PUT http://localhost:8080/api/v1/posts/1 \
-H "Authorization: poll_token" \
-H "Content-Type: application/json" \
-d '{
    "title": "Hacked Post",
    "description": "I should not be able to do this"
}'
```

### Пагинация (публичные + свои приватные)
```
curl -X GET "http://localhost:8080/api/v1/posts?page=1&per_page=5" \
-H "Authorization: jane_token"
```
```
curl -X GET "http://localhost:8080/api/v1/posts?page=1&per_page=5" \
-H "Authorization: poll_token"
```
### Успешное удаление поста (владельцем)
```
curl -X DELETE http://localhost:8080/api/v1/posts/1 \
-H "Authorization: jane_token"
```

### Попытка удаления чужого поста (должна завершиться ошибкой)
```
curl -X DELETE http://localhost:8080/api/v1/posts/2 \
-H "Authorization: poll_token"
```

### Создание поста без заголовка (должна быть ошибка)
```
curl -X POST http://localhost:8080/api/v1/posts \
-H "Authorization: jane_token" \
-H "Content-Type: application/json" \
-d '{
    "description": "Post without title",
    "is_private": false
}'
```

### Создание поста с более чем 10 тегами (должна быть ошибка)
```
curl -X POST http://localhost:8080/api/v1/posts \
-H "Authorization: jane_token" \
-H "Content-Type: application/json" \
-d '{
    "title": "Post with too many tags",
    "description": "This should fail",
    "is_private": false,
    "tags": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11"]
}'
```

### Получение несуществующего поста (должен вернуть 404)
```
curl -X GET http://localhost:8080/api/v1/posts/999 \
-H "Authorization: jane_token"
```

### Запрос без токена (должен вернуть 401)
```
curl -X GET http://localhost:8080/api/v1/posts/1
```

### Запрос с неверным токеном (должен вернуть 401)
```
curl -X GET http://localhost:8080/api/v1/posts/1 \
-H "Authorization: invalid_token"
```
