# User Service
Хранит данные о пользователях, управляет их регистрацией и аутентификацией.

## Подключение к БД
```docker exec -it social-network-platform-db-1 psql -U user -d user_db```

## Примеры curl-запросов

### Регистрация пользователя

```
curl -X POST http://localhost:5000/register -H "Content-Type: application/json" -d '{
    "login": "jane_austen",
    "password": "J@neAusten2025",
    "email": "jane.austen@example.com",
    "first_name": "Jane",
    "last_name": "Austen"
}'
```

### Регистрация с уже занятым логином
```
curl -X POST http://localhost:5000/register -H "Content-Type: application/json" -d '{
    "login": "jane_austen",
    "password": "AnotherP@ssword1!",
    "email": "jane.austen.new@example.com",
    "first_name": "Jane",
    "last_name": "Austen"
}'
```

### Регистрация с уже занятой почтой
```
curl -X POST http://localhost:5000/register -H "Content-Type: application/json" -d '{
    "login": "jane_austen_new",
    "password": "J@neAusten2025",
    "email": "jane.austen@example.com",
    "first_name": "Jane",
    "last_name": "Austen"
}'
```

### Регистрация с некорректным паролем
```
curl -X POST http://localhost:5000/register -H "Content-Type: application/json" -d '{
    "login": "emily_bronte",
    "password": "weak",
    "email": "emily.bronte@example.com",
    "first_name": "Emily",
    "last_name": "Bronte"
}'
```

### Регистрация с некорректной почтой
```
curl -X POST http://localhost:5000/register -H "Content-Type: application/json" -d '{
    "login": "charlotte_bronte",
    "password": "Ch@rlotte2025",
    "email": "invalid-email",
    "first_name": "Charlotte",
    "last_name": "Bronte"
}'
```

### Регистрация с некорректным именем
```
curl -X POST http://localhost:5000/register -H "Content-Type: application/json" -d '{
    "login": "mary_shelley",
    "password": "M@ryShelley2025",
    "email": "mary.shelley@example.com",
    "first_name": "Mary123",
    "last_name": "Shelley"
}'
```

### Авторизация
```
curl -X POST http://localhost:5000/login -H "Content-Type: application/json" -d '{
    "login": "jane_austen",
    "password": "J@neAusten2025"
}'
```

### Получение профиля (с токеном)
```
curl -X GET http://localhost:5000/profile -H "Authorization: <ваш_токен>"
```

### Обновление профиля
```
curl -X PUT http://localhost:5000/profile -H "Authorization: <ваш_токен>" -H "Content-Type: application/json" -d '{
    "first_name": "Janney",
    "profile": {
        "avatar_url": "http://example.com/avatar_jane.jpg",
        "about_me": "Renowned English novelist.",
        "date_of_birth": "2001-12-16"
    }
}'
```

### Попытка обновления логина или пароля
```
curl -X PUT http://localhost:5000/profile -H "Authorization: <ваш_токен>" -H "Content-Type: application/json" -d '{
    "login": "jane_new",
    "password": "NewP@ssword2025"
}'
```

### Попытка обновления профиля с некорректной датой рождения

```
curl -X PUT http://localhost:5000/profile -H "Authorization: <ваш_токен>" -H "Content-Type: application/json" -d '{
    "profile": {
        "date_of_birth": "2125-04-16"
    }
}'
```

### Попытка обновления профиля с некорректным номером телефона
```
curl -X PUT http://localhost:5000/profile -H "Authorization: <ваш_токен>" -H "Content-Type: application/json" -d '{
    "profile": {
        "phone_number": "123"
    }
}'
```
