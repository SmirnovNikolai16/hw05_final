# Проект Backend для Yatube
____

## О проекте
____

Проект "Backend для Yatube", создан для работы с проектом социальной сети для публикации личных дневников/постов. В проект добавлен функционал при помощи которых у пользователей появилась возможность чтение записей всех записей конкретного пользователя либо всех пользователей, создания/удаления/изменения записей, добавления/изменения/удаления комментариев к записям, авторизации и подписки. Также проект покрыт тестами.

## Используемые технологииё
____

* Django 2.2.6
* Запросы через Django ORM
* Git
* SQLLite
* DebugToolbarMiddleware

## Как запустить проект:
____

Клонировать репозиторий и перейти в него в командной строке:

```
git clone https://github.com/SmirnovNikolai16/api_final_yatube.git
```

```
cd hw05_final
```

Cоздать и активировать виртуальное окружение:

```
python3 -m venv env
```

```
source env/bin/activate
```

Установить зависимости из файла requirements.txt:

```
python3 -m pip install --upgrade pip
```

```
pip install -r requirements.txt
```

Выполнить миграции:

```
python3 manage.py migrate
```

Запустить проект:

```
python3 manage.py runserver
```

## Основная ссылка после запуска проекта:
____

```
http://127.0.0.1:8000/
```

Для того, чтобы воспользоваться всеми возможностями сайта, рекомендую зарегистрироваться.
