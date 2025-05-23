# Общие принципы работы сервиса:

## Структура проекта

Yadro\
$\quad$ - migrations -  Папка с миграциями и настройками alembic\
$\quad$ $\quad$ - - versions/ - Папка с миграциями\
$\quad$ $\quad$ - - alembic.ini - конфигурация alembic\
$\quad$ - database.py - Подключение к базе данных\
$\quad$ - models.py - Модели базы данных\
$\quad$ - main.py - Обработчики приложения\
$\quad$ - tests.py - Тесты\
$\quad$ - .env - Переменные окружения\
$\quad$ - .env.example - Пример переменных окружения\
$\quad$ - Dockerfile\
$\quad$ - docker-compose.yml

## Основные функции (main.py):
### Валидация графов:

 - graph_data_validation - проверяет корректность графа:
   - Отсутствие повторяющихся имен узлов
   - Отсутствие ссылок на несуществующие узлы в ребрах
   - Отсутствие циклов
 - is_acyclic - проверяет граф на ацикличность с помощью алгоритма обхода в глубину (DFS)

### Обработчики API
 - create_graph - создание нового графа
 - get_graph - получение графа (вершины и ребра)
 - get_adjacency_list - получение матрицы смежности
 - get_reverse_adjacency_list - получение транспонированной матрицы смежности
 - delete_node - удаление узла графа

## Перед запуском:
1. Необходимо создать файл .env, используя .env.example, как шаблон
2. Указать название, логин и пароль для базы данных, если необходимо

## Для запуска приложения:
```commandline
docker-compose up -d --build
```

Приложение будет доступно на `http://localhost:8080`

Для запуска тестов:

Вариант №1 (Основной compose-файл):

Тесты автоматически запускаются при запуске контейнера. 

Для того, чтобы их найти:
```commandline
docker-compose up -d --build
docker-compose logs app
```

Вариант №2 (Через compose-файл для тестов):

Запустить docker-compose файл для тестирования:
```commandline
docker-compose -f docker-compose-tests.yml up --build --abort-on-container-exit
```


