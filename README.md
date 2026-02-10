# order-inventory-platform

## Конфигурация

Это приложение нужно настроить с помощью переменных среды.

Нужно создать файл `.env` в корневом каталоге и поместить все переменные среды туда. 
Пример файла конфигурации представлен в корне проекта `.env.example`. 

Все переменные среды должны начинаться с префикса "ORDER_INVENTORY_PLATFORM_".

Например, если вы видите в своем "project/settings.py" переменную с именем `random_parameter`, вам следует указать переменную "ORDER_INVENTORY_PLATFORM_RANDOM_PARAMETER"
для настройки значения. Это поведение можно изменить, переопределив свойство `env_prefix`
в `project.settings.Settings.SettingsConfigDict`.

Подробнее о классе BaseSettings можно прочитать здесь: https://pydantic-docs.helpmanual.io/usage/settings/

## Docker

Вы можете запустить проект с помощью docker, используя эту команду:

```bash
docker compose up --build
```

Это запустит сервер на настроенном хосте.

Вы можете найти документацию swagger по адресу `/api/docs`.

## Pre-commit

Чтобы установить pre-commit, просто запустите в корне проекта:
```bash
pre-commit install
```

pre-commit очень полезен для проверки кода перед его публикацией.
Он настраивается с помощью файла .pre-commit-config.yaml.

На данный момент он запускает:
* black (форматирует код);
* mypy (проверяет типы);
* ruff (выявляет возможные ошибки);

Подробнее о pre-commit можно прочитать здесь: https://pre-commit.com/

## Миграции

```bash
# Для автогенерации миграции по изменённым моделям
make makemigration

# Для применения миграции
make migrate

# Для отката последней миграции
make revert
```

## Запуск тестов

```bash
make unittest
```