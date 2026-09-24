#!/usr/bin/env python3
"""Собирает формы расширения в src/cfe: конструктор схем, «Мои задачи», запуск процесса, формы задачи и процесса.

Формы описаны на Python (tools/forms/formlib.py) и пишутся в формате выгрузки Конфигуратора.
Модули форм и общих модулей берутся из каталога исходников BSL (UTF-8, LF), если он передан аргументом:
    python3 tools/forms/build.py <каталог с .bsl>
Имена файлов исходников: «<ОбщийМодуль>.bsl» и «<Объект>.<Форма>.bsl» (см. MODULES).
Без аргумента пишутся только XML форм и метаданных.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from formlib import (Attr, Cmd, SRC, T_ANYREF, T_BOOL, T_DATETIME, T_GRAPH, T_VT, button, check, data_processor_md,
                     deco, field, form, form_md, group, label, page, pages, schema_field, t_cfg, t_num, t_str, table,
                     write)

BSL = Path(sys.argv[1]) if len(sys.argv) > 1 else None

REF_USER = t_cfg("CatalogRef.Пользователи")


def cols(table_name, spec, path=None, **common):
    """Колонки таблицы формы: [(имя, заголовок, вид, доп. свойства)]; вид — field/check/label.
    path — путь к данным таблицы, если он не совпадает с именем (например, «Объект.Переменные»)."""
    path = path or table_name
    items = []
    for name, title, kind, *extra in spec:
        kw = dict(common)
        if extra:
            kw.update(extra[0])
        make = {"field": field, "check": check, "label": label}[kind]
        items.append(make(f"{table_name}{name}", f"{path}.{name}", title, **kw))
    return items


def on_change(handler):
    return {"OnChange": handler}


# --------------------------------------------------------------------------------------------------------------------
# Конструктор схем
# --------------------------------------------------------------------------------------------------------------------

KONSTR = "кбп_КонструкторСхем"

KONSTR_COMMANDS = [
    Cmd("Сохранить", "Сохранить", "Сохранить черновик и синхронизировать шаги и переходы", "StdPicture.Write"),
    Cmd("Проверить", "Проверить", "Проверить схему перед публикацией", "StdPicture.CheckSyntax"),
    Cmd("Опубликовать", "Опубликовать", "Проверить и опубликовать черновик"),
    Cmd("ИзменитьСхему", "Изменить схему", "Создать черновик из опубликованной версии"),
    Cmd("ЗапуститьПроцесс", "Запустить процесс", "Запустить процесс по опубликованной версии схемы"),
    Cmd("Редактирование", "Редактирование", "Включить или выключить правку схемы", "StdPicture.Change"),
    Cmd("СвойстваЭлемента", "Свойства элемента", "Показать свойства выделенного элемента схемы"),
    Cmd("Перечитать", "Перечитать", "Перечитать версию из базы", "StdPicture.Refresh"),
    Cmd("СтруктураСхемы", "Структура схемы", "Диагностика: виды и свойства элементов графической схемы"),
    Cmd("ЗаписатьСвойства", "Записать свойства", "Записать свойства выбранного шага или линии", "StdPicture.Write"),
]


def konstruktor_form():
    ch = on_change("СвойствоПриИзменении")
    header = group("Шапка", [
        field("Схема", "Схема", "Схема", events=on_change("СхемаПриИзменении")),
        field("Версия", "Версия", "Версия", events=on_change("ВерсияПриИзменении")),
        field("ТипПредмета", "ТипПредмета", "Предмет процесса", events=on_change("ТипПредметаПриИзменении"),
              ToolTip="Тип объектов, по которым запускается процесс; пусто — процесс без предмета",
              ListChoiceMode=True, Width=30, HorizontalStretch=False),
        label("Статус", "Статус", TitleLocation="None"),
    ], horizontal=True)

    steps = table("Шаги", "Шаги", cols("Шаги", [
        ("Ошибка", "!", "check"),
        ("Наименование", "Элемент", "field"),
        ("Вид", "Вид", "field", {"Width": 10}),
    ]), events={"Selection": "ШагиВыбор", "OnActivateRow": "ШагиПриАктивизацииСтроки"}, bar=[],
        ReadOnly=True, ChangeRowSet=False, ChangeRowOrder=False, Height=8, Title="Шаги и линии схемы",
        TitleLocation="Top", Header=False)

    page_step = page("СтраницаШаг", "Шаг", [
        label("ЭлементШагаНаименование", "ЭлементШага.Description", "Наименование"),
        label("ЭлементШагаТипШага", "ЭлементШага.ТипШага", "Тип шага"),
        field("ЭлементШагаИнструкция", "ЭлементШага.Инструкция", "Инструкция исполнителю", events=ch,
              TitleLocation="Top", MultiLine=True, Height=3),
        group("ГруппаСрок", [
            field("ЭлементШагаСрокЗначение", "ЭлементШага.СрокЗначение", "Срок", events=ch, Width=6,
                  HorizontalStretch=False),
            field("ЭлементШагаСрокЕдиница", "ЭлементШага.СрокЕдиница", None, events=ch, TitleLocation="None"),
        ], title="Срок", horizontal=True),
        field("ЭлементШагаРежимНазначения", "ЭлементШага.РежимНазначения", "Назначить", events=ch,
              ToolTip="Каждому — задача каждому исполнителю, шаг завершается, когда выполнят все; "
                      "любому из — первый выполнивший завершает шаг"),
        check("ЭлементШагаВзятьВРаботу", "ЭлементШага.ВзятьВРаботу", "Принятие к исполнению снимает задачу с остальных",
              events=ch),
        check("ЭлементШагаРазрешенВозврат", "ЭлементШага.РазрешенВозврат", "Разрешён возврат на доработку", events=ch),
        field("ЭлементШагаРежимВозврата", "ЭлементШага.РежимВозврата", "После доработки", events=ch),
        check("ЭлементШагаТотЖеИсполнительПриВозврате", "ЭлементШага.ТотЖеИсполнительПриВозврате",
              "При возврате на этот шаг — тому же исполнителю", events=ch),
        field("ЭлементШагаОбработчик", "ЭлементШага.Обработчик", "Обработчик", events=ch),
    ])

    tch = {"OnChange": "СвойствоТаблицыПриИзменении"}
    page_exec = page("СтраницаИсполнители", "Исполнители", [
        table("ИсполнителиШага", "ИсполнителиШага", cols("ИсполнителиШага", [
            ("СпособАдресации", "Способ", "field"),
            ("Роль", "Роль", "field"),
            ("Пользователь", "Пользователь", "field"),
            ("ПутьОбъектаАдресации1", "Объект адресации (путь)", "field"),
            ("РеквизитПредмета", "Реквизит предмета", "field"),
            ("Обработчик", "Обработчик", "field"),
        ]), events=tch, Height=5, TitleLocation="None"),
        deco("ПодсказкаИсполнители", "Путь — от предмета через точку («Контрагент.ОсновнойМенеджер») "
                                     "или «Переменные.Имя»."),
    ])
    page_buttons = page("СтраницаКнопки", "Кнопки", [
        table("КнопкиШага", "КнопкиШага", cols("КнопкиШага", [
            ("Заголовок", "Кнопка", "field"),
            ("Вид", "Вид", "field"),
            ("Действие", "Действие", "field"),
            ("ИдПерехода", "Линия", "field", {"ListChoiceMode": True}),
            ("КомментарийОбязателен", "Коммент.", "check"),
            ("Подтверждение", "Подтв.", "check"),
            ("ТекстПодтверждения", "Текст подтверждения", "field"),
            ("Обработчик", "Обработчик", "field"),
        ]), events=tch, Height=5, TitleLocation="None"),
        deco("ПодсказкаКнопки", "Без настроенных кнопок каждая линия из задачи становится кнопкой "
                                "(заголовок — подпись линии), при одной линии — «Выполнено»."),
    ])
    page_line = page("СтраницаЛиния", "Линия", [
        label("Лин_Наименование", "Лин_Наименование", "Линия"),
        check("Лин_ПоУмолчанию", "Лин_ПоУмолчанию", "По умолчанию (ветка «Нет» у Условия)", events=ch),
        field("Лин_ИдКнопки", "Лин_ИдКнопки", "Результат задачи", events=ch, ListChoiceMode=True,
              ToolTip="Ветка выбирается, если задача выполнена этой кнопкой"),
        field("Лин_ВидУсловия", "Лин_ВидУсловия", "Условие", events=ch),
        field("Лин_ОбработчикУсловия", "Лин_ОбработчикУсловия", "Обработчик условия", events=ch),
        check("Лин_ЭтоВозврат", "Лин_ЭтоВозврат", "Это возврат (учитывать в статистике)", events=ch),
        field("Лин_Порядок", "Лин_Порядок", "Порядок проверки", events=ch, Width=5, HorizontalStretch=False),
    ])
    page_none = page("СтраницаПусто", "Нет элемента", [
        deco("ПодсказкаПусто", "Выберите шаг или линию в списке выше или дважды щёлкните элемент на схеме."),
    ])

    props = group("Свойства", [
        pages("СтраницыСвойств", [page_none, page_step, page_exec, page_buttons, page_line],
              PagesRepresentation="TabsOnTop"),
        button("ФормаЗаписатьСвойства", "ЗаписатьСвойства"),
    ], title="Свойства", show_title=True, representation="NormalSeparation", TitleDataPath="ЗаголовокСвойств")

    right = group("Правая", [steps, props], Width=48, HorizontalStretch=False)

    main = group("Основная", [
        schema_field("ГрафСхема", "ГрафСхема", "Схема процесса", events={"Selection": "ГрафСхемаВыбор"},
                     TitleLocation="None", Width=100, Height=30, Edit=True),
        right,
    ], horizontal=True)

    check_text = field("ТекстПроверки", "ТекстПроверки", "Результат проверки", ReadOnly=True, TitleLocation="Top",
                       Height=4, MultiLine=True)

    bar = [button(f"Форма{c.name}", c.name, usual=False) for c in KONSTR_COMMANDS if c.name != "ЗаписатьСвойства"]

    str0 = t_str(0)
    attrs = [
        Attr("Объект", t_cfg(f"DataProcessorObject.{KONSTR}"), main=True),
        Attr("Схема", t_cfg("CatalogRef.кбп_СхемыПроцессов"), "Схема"),
        Attr("Версия", t_cfg("CatalogRef.кбп_ВерсииСхем"), "Версия"),
        Attr("ГрафСхема", T_GRAPH, "Схема процесса"),
        Attr("Статус", str0, "Статус"),
        Attr("ЭтоЧерновик", T_BOOL, "Это черновик"),
        Attr("ТекстПроверки", str0, "Результат проверки"),
        Attr("Шаги", T_VT, "Шаги схемы", columns=[
            ("Ссылка", t_cfg("CatalogRef.кбп_ЭлементыСхем"), "Элемент"),
            ("ИдЭлемента", str0, "Ид элемента"),
            ("Наименование", str0, "Элемент"),
            ("ТипШага", t_cfg("EnumRef.кбп_ТипыШагов"), "Тип"),
            ("Ошибка", T_BOOL, "Ошибка"),
            ("Вид", str0, "Вид"),
            ("ЭтоЛиния", T_BOOL, "Это линия"),
        ]),
        Attr("ТипПредмета", t_str(255), "Предмет процесса"),
        Attr("ЭлементШага", t_cfg("CatalogObject.кбп_ЭлементыСхем"), "Шаг"),
        Attr("ИсполнителиШага", T_VT, "Исполнители", columns=[
            ("СпособАдресации", t_cfg("EnumRef.кбп_СпособыАдресации"), "Способ"),
            ("Роль", t_cfg("CatalogRef.кбп_РолиИсполнителей"), "Роль"),
            ("Пользователь", REF_USER, "Пользователь"),
            ("ПутьОбъектаАдресации1", t_str(255), "Объект адресации 1"),
            ("ПутьОбъектаАдресации2", t_str(255), "Объект адресации 2"),
            ("РеквизитПредмета", t_str(255), "Реквизит предмета"),
            ("Обработчик", t_cfg("CatalogRef.кбп_ОбработчикиПроцессов"), "Обработчик"),
        ]),
        Attr("КнопкиШага", T_VT, "Кнопки", columns=[
            ("ИдКнопки", t_str(36), "Ид кнопки"),
            ("Заголовок", t_str(100), "Кнопка"),
            ("Вид", t_cfg("EnumRef.кбп_ВидыКнопок"), "Вид"),
            ("Действие", t_cfg("EnumRef.кбп_ВидыДействий"), "Действие"),
            ("ИдПерехода", t_str(36), "Линия"),
            ("Подтверждение", T_BOOL, "Подтверждение"),
            ("ТекстПодтверждения", t_str(500), "Текст подтверждения"),
            ("КомментарийОбязателен", T_BOOL, "Комментарий обязателен"),
            ("Обработчик", t_cfg("CatalogRef.кбп_ОбработчикиПроцессов"), "Обработчик"),
        ]),
        Attr("ТекущийИд", t_str(36), "Текущий элемент"),
        Attr("ТекущийВид", t_str(10), "Вид текущего элемента"),
        Attr("СвойстваИзменены", T_BOOL, "Свойства изменены"),
        Attr("ЗаголовокСвойств", str0, "Заголовок свойств"),
        Attr("Лин_Наименование", str0, "Линия"),
        Attr("Лин_ПоУмолчанию", T_BOOL, "По умолчанию"),
        Attr("Лин_ИдКнопки", t_str(36), "Результат задачи"),
        Attr("Лин_ВидУсловия", t_cfg("EnumRef.кбп_ВидыУсловий"), "Условие"),
        Attr("Лин_ОбработчикУсловия", t_cfg("CatalogRef.кбп_ОбработчикиПроцессов"), "Обработчик условия"),
        Attr("Лин_ЭтоВозврат", T_BOOL, "Это возврат"),
        Attr("Лин_Порядок", t_num(5, 0, True), "Порядок"),
    ]
    return form([header, main, check_text], attrs, KONSTR_COMMANDS,
                params=[("Схема", t_cfg("CatalogRef.кбп_СхемыПроцессов"))],
                events={"BeforeClose": "ПередЗакрытием", "OnCreateAtServer": "ПриСозданииНаСервере"}, bar=bar)


# --------------------------------------------------------------------------------------------------------------------
# Мои задачи и запуск процесса
# --------------------------------------------------------------------------------------------------------------------

MOI = "кбп_МоиЗадачи"


def moi_zadachi_form():
    commands = [
        Cmd("Обновить", "Обновить", "Обновить списки", "StdPicture.Refresh"),
        Cmd("ОткрытьЗадачу", "Открыть", "Открыть задачу или процесс", "StdPicture.Change"),
        Cmd("ЗапуститьПроцесс", "Запустить процесс…", "Запустить новый процесс по схеме"),
    ]
    tasks = table("Задачи", "Задачи", cols("Задачи", [
        ("Наименование", "Задача", "field"),
        ("ПредставлениеПредмета", "Предмет", "field"),
        ("Процесс", "Процесс", "field"),
        ("Срок", "Срок", "field", {"Width": 12}),
        ("Состояние", "Состояние", "field", {"Width": 10}),
        ("Автор", "Автор процесса", "field"),
        ("ДатаСоздания", "Получена", "field", {"Width": 12}),
    ]), events={"Selection": "ЗадачиВыбор"}, bar=[], ReadOnly=True, ChangeRowSet=False, ChangeRowOrder=False,
        TitleLocation="None")
    processes = table("Процессы", "Процессы", cols("Процессы", [
        ("Ссылка", "Процесс", "field"),
        ("Состояние", "Состояние", "field", {"Width": 10}),
        ("ТекущиеШаги", "Сейчас у", "field"),
        ("ДатаСтарта", "Запущен", "field", {"Width": 12}),
        ("ДатаЗавершения", "Завершён", "field", {"Width": 12}),
    ]), events={"Selection": "ПроцессыВыбор"}, bar=[], ReadOnly=True, ChangeRowSet=False, ChangeRowOrder=False,
        TitleLocation="None")
    items = [pages("Страницы", [
        page("СтраницаЗадачи", "Мои задачи", [
            check("ПоказыватьВыполненные", "ПоказыватьВыполненные", "Показывать выполненные за 30 дней",
                  events=on_change("ПоказыватьВыполненныеПриИзменении")),
            tasks,
        ], TitleDataPath="ЗаголовокЗадачи"),
        page("СтраницаПроцессы", "Мои процессы", [processes]),
    ], PagesRepresentation="TabsOnTop")]
    attrs = [
        Attr("Объект", t_cfg(f"DataProcessorObject.{MOI}"), main=True),
        Attr("Задачи", T_VT, "Задачи", columns=[
            ("Ссылка", t_cfg("CatalogRef.кбп_Задачи"), "Задача"),
            ("Наименование", t_str(0), "Задача"),
            ("Процесс", t_cfg("CatalogRef.кбп_Процессы"), "Процесс"),
            ("ПредставлениеПредмета", t_str(0), "Предмет"),
            ("Срок", T_DATETIME, "Срок"),
            ("Состояние", t_cfg("EnumRef.кбп_СостоянияЗадач"), "Состояние"),
            ("Автор", REF_USER, "Автор процесса"),
            ("ДатаСоздания", T_DATETIME, "Получена"),
            ("Просрочена", T_BOOL, "Просрочена"),
            ("Активна", T_BOOL, "Активна"),
        ]),
        Attr("Процессы", T_VT, "Процессы", columns=[
            ("Ссылка", t_cfg("CatalogRef.кбп_Процессы"), "Процесс"),
            ("Схема", t_cfg("CatalogRef.кбп_СхемыПроцессов"), "Схема"),
            ("ПредставлениеПредмета", t_str(0), "Предмет"),
            ("Состояние", t_cfg("EnumRef.кбп_СостоянияПроцессов"), "Состояние"),
            ("ДатаСтарта", T_DATETIME, "Запущен"),
            ("ДатаЗавершения", T_DATETIME, "Завершён"),
            ("ТекущиеШаги", t_str(0), "Сейчас у"),
        ]),
        Attr("ПоказыватьВыполненные", T_BOOL, "Показывать выполненные"),
        Attr("ЗаголовокЗадачи", t_str(0), "Заголовок страницы задач"),
    ]
    bar = [button("Форма" + c.name, c.name, usual=False) for c in commands]
    return form(items, attrs, commands, bar=bar, bar_autofill=False, Title="Мои задачи",
                events={"OnCreateAtServer": "ПриСозданииНаСервере", "NotificationProcessing": "ОбработкаОповещения"})


def zapusk_form():
    commands = [Cmd("Запустить", "Запустить", "Запустить процесс")]
    items = [
        field("Схема", "Схема", "Схема процесса", events=on_change("СхемаПриИзменении")),
        field("Предмет", "Предмет", "Предмет"),
        field("Комментарий", "Комментарий", "Комментарий", TitleLocation="Top", MultiLine=True, Height=3),
    ]
    attrs = [
        Attr("Объект", t_cfg(f"DataProcessorObject.{MOI}"), main=True),
        Attr("Схема", t_cfg("CatalogRef.кбп_СхемыПроцессов"), "Схема процесса"),
        Attr("Предмет", T_ANYREF, "Предмет"),
        Attr("Комментарий", t_str(0), "Комментарий"),
        Attr("ТипПредмета", t_str(255), "Тип предмета"),
    ]
    bar = [button("ФормаЗапустить", "Запустить", usual=False, DefaultButton=True)]
    return form(items, attrs, commands, bar=bar, Title="Запуск процесса", WindowOpeningMode="LockOwnerWindow",
                params=[("Схема", t_cfg("CatalogRef.кбп_СхемыПроцессов")), ("Предмет", T_ANYREF)],
                events={"OnCreateAtServer": "ПриСозданииНаСервере"})


# --------------------------------------------------------------------------------------------------------------------
# Формы задачи и процесса
# --------------------------------------------------------------------------------------------------------------------

JOURNAL_COLUMNS = [
    ("Момент", T_DATETIME, "Когда"),
    ("Пользователь", t_str(0), "Кто"),
    ("Событие", t_str(0), "Событие"),
    ("Текст", t_str(0), "Подробности"),
]


def journal_table(name="Журнал"):
    return table(name, name, cols(name, [
        ("Момент", "Когда", "field", {"Width": 12}),
        ("Пользователь", "Кто", "field", {"Width": 15}),
        ("Событие", "Событие", "field", {"Width": 15}),
        ("Текст", "Подробности", "field"),
    ]), bar=[], ReadOnly=True, ChangeRowSet=False, ChangeRowOrder=False, TitleLocation="None", Height=6)


def zadacha_form():
    commands = [
        Cmd("ПринятьКИсполнению", "Принять к исполнению", "Отметить, что задача взята в работу"),
        Cmd("ДобавитьКомментарий", "Добавить комментарий", "Добавить комментарий в ленту процесса"),
        Cmd("ОткрытьПроцесс", "Процесс", "Открыть карточку процесса"),
        Cmd("Обновить", "Обновить", "Перечитать задачу", "StdPicture.Refresh"),
    ]
    ro = dict(ReadOnly=True)
    items = [
        group("Шапка", [
            label("Процесс", "Объект.Процесс", "Процесс", Hiperlink=True),
            label("Предмет", "Объект.Предмет", "Предмет", Hiperlink=True),
        ], horizontal=True),
        group("Реквизиты", [
            label("Состояние", "Объект.Состояние", "Состояние"),
            label("Срок", "Объект.Срок", "Срок"),
            label("Назначенный", "Объект.Назначенный", "Исполнитель"),
        ], horizontal=True),
        field("Инструкция", "Инструкция", "Что сделать", TitleLocation="Top", MultiLine=True, Height=3, **ro),
        group("Действия", [button("ФормаПринятьКИсполнению", "ПринятьКИсполнению")],
              title="Действия", horizontal=True),
        field("Комментарий", "Комментарий", "Комментарий", TitleLocation="Top", MultiLine=True, Height=3,
              InputHint="Комментарий к действию или в ленту процесса"),
        button("ФормаДобавитьКомментарий", "ДобавитьКомментарий"),
        label("Результат", "Результат", "Результат", Visible=False),
        group("ГруппаЖурнал", [journal_table()], title="История и комментарии", show_title=True,
              representation="NormalSeparation"),
    ]
    attrs = [
        Attr("Объект", t_cfg("CatalogObject.кбп_Задачи"), main=True, saved=True),
        Attr("Инструкция", t_str(0), "Что сделать"),
        Attr("Комментарий", t_str(0), "Комментарий"),
        Attr("Результат", t_str(0), "Результат"),
        Attr("Журнал", T_VT, "История", columns=JOURNAL_COLUMNS),
        Attr("Кнопки", T_VT, "Кнопки", columns=[
            ("ИмяКоманды", t_str(0), None),
            ("ИдКнопки", t_str(36), None),
            ("Заголовок", t_str(0), None),
            ("ЭтоВозврат", T_BOOL, None),
            ("Подтверждение", T_BOOL, None),
            ("ТекстПодтверждения", t_str(0), None),
            ("КомментарийОбязателен", T_BOOL, None),
        ]),
        Attr("МожноВыполнить", T_BOOL, "Можно выполнить"),
    ]
    bar = [button("ФормаОткрытьПроцесс", "ОткрытьПроцесс", usual=False),
           button("ФормаОбновить", "Обновить", usual=False)]
    return form(items, attrs, commands, bar=bar, bar_autofill=False,
                events={"OnCreateAtServer": "ПриСозданииНаСервере"})


def process_form():
    commands = [
        Cmd("ПрерватьПроцесс", "Прервать процесс", "Прервать процесс и отменить его задачи"),
        Cmd("ДобавитьКомментарий", "Добавить комментарий", "Добавить комментарий в ленту процесса"),
        Cmd("Обновить", "Обновить", "Перечитать процесс", "StdPicture.Refresh"),
    ]
    tasks = table("Задачи", "Задачи", cols("Задачи", [
        ("Наименование", "Задача", "field"),
        ("Назначенный", "Исполнитель", "field"),
        ("Состояние", "Состояние", "field", {"Width": 10}),
        ("Результат", "Результат", "field"),
        ("ДатаСоздания", "Создана", "field", {"Width": 12}),
        ("Срок", "Срок", "field", {"Width": 12}),
        ("ДатаВыполнения", "Выполнена", "field", {"Width": 12}),
    ]), events={"Selection": "ЗадачиВыбор"}, bar=[], ReadOnly=True, ChangeRowSet=False, ChangeRowOrder=False,
        TitleLocation="None", Height=6)
    variables = table("Переменные", "Объект.Переменные", cols("Переменные", [
        ("Переменная", "Переменная", "field"),
        ("Значение", "Значение", "field"),
    ], path="Объект.Переменные"), bar=[], ReadOnly=True, ChangeRowSet=False, ChangeRowOrder=False, TitleLocation="None", Height=4)
    items = [
        group("Шапка", [
            label("Схема", "Объект.Схема", "Схема", Hiperlink=True),
            label("ВерсияСхемы", "Объект.ВерсияСхемы", "Версия"),
            label("Предмет", "Объект.Предмет", "Предмет", Hiperlink=True),
        ], horizontal=True),
        group("Реквизиты", [
            label("Состояние", "Объект.Состояние", "Состояние"),
            label("Автор", "Объект.Автор", "Автор"),
            label("ДатаСтарта", "Объект.ДатаСтарта", "Запущен"),
            label("ДатаЗавершения", "Объект.ДатаЗавершения", "Завершён"),
        ], horizontal=True),
        pages("Страницы", [
            page("СтраницаЗадачи", "Задачи", [tasks]),
            page("СтраницаИстория", "История и комментарии", [
                journal_table(),
                field("Комментарий", "Комментарий", "Комментарий", TitleLocation="Top", MultiLine=True, Height=2),
                button("ФормаДобавитьКомментарий", "ДобавитьКомментарий"),
            ]),
            page("СтраницаСхема", "Схема", [
                schema_field("ГрафСхема", "ГрафСхема", "Схема", TitleLocation="None", Width=80, Height=20, Edit=False),
                deco("ЛегендаСхемы", "Зелёные — пройденные шаги, жёлтые — текущие."),
            ]),
            page("СтраницаПеременные", "Переменные", [variables]),
        ], PagesRepresentation="TabsOnTop"),
    ]
    attrs = [
        Attr("Объект", t_cfg("CatalogObject.кбп_Процессы"), main=True, saved=True),
        Attr("Задачи", T_VT, "Задачи", columns=[
            ("Ссылка", t_cfg("CatalogRef.кбп_Задачи"), "Задача"),
            ("Наименование", t_str(0), "Задача"),
            ("Назначенный", REF_USER, "Исполнитель"),
            ("Исполнитель", REF_USER, "Выполнил"),
            ("Состояние", t_cfg("EnumRef.кбп_СостоянияЗадач"), "Состояние"),
            ("Результат", t_str(0), "Результат"),
            ("ДатаСоздания", T_DATETIME, "Создана"),
            ("Срок", T_DATETIME, "Срок"),
            ("ДатаВыполнения", T_DATETIME, "Выполнена"),
        ]),
        Attr("Журнал", T_VT, "История", columns=JOURNAL_COLUMNS),
        Attr("Комментарий", t_str(0), "Комментарий"),
        Attr("ГрафСхема", T_GRAPH, "Схема"),
    ]
    bar = [button("ФормаПрерватьПроцесс", "ПрерватьПроцесс", usual=False), button("ФормаОбновить", "Обновить", usual=False)]
    return form(items, attrs, commands, bar=bar, bar_autofill=False,
                events={"OnCreateAtServer": "ПриСозданииНаСервере"})


# --------------------------------------------------------------------------------------------------------------------
# Метаданные
# --------------------------------------------------------------------------------------------------------------------

def register_catalog_form(catalog, form_name):
    """Добавляет форму в Catalogs/<catalog>.xml и делает её основной формой объекта."""
    path = SRC / "Catalogs" / f"{catalog}.xml"
    text = path.read_bytes().decode("utf-8-sig")
    full = f"Catalog.{catalog}.Form.{form_name}"
    text = re.sub(r"<DefaultObjectForm\s*/>|<DefaultObjectForm>[^<]*</DefaultObjectForm>",
                  f"<DefaultObjectForm>{full}</DefaultObjectForm>", text, count=1)
    if f"<Form>{form_name}</Form>" not in text:
        nl = "\r\n" if "\r\n" in text else "\n"
        idx = text.rindex("</ChildObjects>")
        text = text[:idx] + f"\t<Form>{form_name}</Form>{nl}\t\t" + text[idx:]
    path.write_bytes(("﻿" + text).encode("utf-8"))


FORMS = {
    # (путь каталога объекта, md-имя владельца, имя формы, синоним): построитель
    ("DataProcessors/кбп_КонструкторСхем", f"DataProcessor.{KONSTR}", "Форма", "Конструктор схем процессов"): konstruktor_form,
    ("DataProcessors/кбп_МоиЗадачи", f"DataProcessor.{MOI}", "Форма", "Мои задачи"): moi_zadachi_form,
    ("DataProcessors/кбп_МоиЗадачи", f"DataProcessor.{MOI}", "ЗапускПроцесса", "Запуск процесса"): zapusk_form,
    ("Catalogs/кбп_Задачи", "Catalog.кбп_Задачи", "ФормаЭлемента", "Задача"): zadacha_form,
    ("Catalogs/кбп_Процессы", "Catalog.кбп_Процессы", "ФормаЭлемента", "Процесс"): process_form,
}

# Исходник BSL → модуль в src/cfe
MODULES = {
    "Конструктор.Форма.bsl": "DataProcessors/кбп_КонструкторСхем/Forms/Форма/Ext/Form/Module.bsl",
    "МоиЗадачи.Форма.bsl": "DataProcessors/кбп_МоиЗадачи/Forms/Форма/Ext/Form/Module.bsl",
    "МоиЗадачи.ЗапускПроцесса.bsl": "DataProcessors/кбп_МоиЗадачи/Forms/ЗапускПроцесса/Ext/Form/Module.bsl",
    "Задачи.ФормаЭлемента.bsl": "Catalogs/кбп_Задачи/Forms/ФормаЭлемента/Ext/Form/Module.bsl",
    "Процессы.ФормаЭлемента.bsl": "Catalogs/кбп_Процессы/Forms/ФормаЭлемента/Ext/Form/Module.bsl",
}


def main():
    write(f"DataProcessors/{KONSTR}.xml", data_processor_md(KONSTR, "Конструктор схем процессов", ["Форма"], "Форма"))
    write(f"DataProcessors/{MOI}.xml", data_processor_md(MOI, "Мои задачи", ["Форма", "ЗапускПроцесса"], "Форма"))
    for (folder, owner, name, synonym), build in FORMS.items():
        write(f"{folder}/Forms/{name}.xml", form_md(owner, name, synonym))
        write(f"{folder}/Forms/{name}/Ext/Form.xml", build())
    register_catalog_form("кбп_Задачи", "ФормаЭлемента")
    register_catalog_form("кбп_Процессы", "ФормаЭлемента")
    if BSL is not None:
        for src, dst in MODULES.items():
            write(dst, (BSL / src).read_text(encoding="utf-8"))
        for path in sorted(BSL.glob("кбп_*.bsl")):
            write(f"CommonModules/{path.stem}/Ext/Module.bsl", path.read_text(encoding="utf-8"))
    print("ok")


if __name__ == "__main__":
    main()
