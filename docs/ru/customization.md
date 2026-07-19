# Настройка и безопасность

## Переопределение шаблонов

Каталоги проекта имеют приоритет над встроенными шаблонами:

```python
site = CabinetSite(
    brand_name="Внутренние инструменты",
    template_directories=("src/my_project/templates",),
)
```

Для замены карточки объекта создайте:

```text
src/my_project/templates/cabinet/pages/detail.html
```

## Права

Реализуйте порт прав:

```python
class ProjectPermissions:
    async def can(self, request, permission: str) -> bool:
        return permission in request.state.actor.permissions
```

и передайте его в `CabinetSite`. Права можно объявить для модуля, страницы, виджета, пункта меню и
маршрута операции. Скрытие ссылки не заменяет защиту маршрута — библиотека проверяет их отдельно.

## Аутентификация и CSRF

Подключающий проект обязан:

- аутентифицировать запрос до кабинета;
- закрыть mount path от анонимного доступа;
- положить CSRF-токен в `request.state.csrf_token`;
- проверить токен в middleware или обработчике изменения;
- повторно проверять право на бизнес-операцию в прикладном сценарии.

Формы библиотеки передают токен в поле `csrf_token`. Для семантических методов кроме POST поле
`_method` требует соответствующего middleware в проекте.
