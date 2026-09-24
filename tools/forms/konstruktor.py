#!/usr/bin/env python3
"""Собирает обработку кбп_КонструкторСхем (метаданные, форма, модули) в src/cfe.

Одноразовая сборка прототипа этапа 0: после загрузки в базу и выгрузки из Конфигуратора
источником истины становится src/cfe, а форму дальше правят в Конфигураторе.
Файлы пишутся в формате выгрузки Конфигуратора: UTF-8 с BOM, CRLF.
"""
import re
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src" / "cfe"
BSL = Path(sys.argv[1]) if len(sys.argv) > 1 else None  # каталог с Форма.bsl; без него модуль формы не трогаем
NS = uuid.UUID("6f1c3a52-3d8e-4b6a-9d61-6b0f2d1c7a10")  # тот же, что в tools/gen/generate.py
NAME = "кбп_КонструкторСхем"
MD = f"DataProcessor.{NAME}"


def uid(*p):
    return str(uuid.uuid5(NS, "/".join(p)))


def write(rel, text):
    path = SRC / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    text = text.replace("\r\n", "\n").replace("\n", "\r\n")
    path.write_bytes(("﻿" + text.lstrip("﻿")).encode("utf-8"))


def ls(text, ind):
    t = "\t" * ind
    return (f"{t}<v8:item>\n{t}\t<v8:lang>ru</v8:lang>\n{t}\t<v8:content>{text}</v8:content>\n{t}</v8:item>\n")


MDHEAD = ('<?xml version="1.0" encoding="UTF-8"?>\n<MetaDataObject xmlns="http://v8.1c.ru/8.3/MDClasses" '
          'xmlns:app="http://v8.1c.ru/8.2/managed-application/core" xmlns:cfg="http://v8.1c.ru/8.1/data/enterprise/current-config" '
          'xmlns:cmi="http://v8.1c.ru/8.2/managed-application/cmi" xmlns:ent="http://v8.1c.ru/8.1/data/enterprise" '
          'xmlns:lf="http://v8.1c.ru/8.2/managed-application/logform" xmlns:style="http://v8.1c.ru/8.1/data/ui/style" '
          'xmlns:sys="http://v8.1c.ru/8.1/data/ui/fonts/system" xmlns:v8="http://v8.1c.ru/8.1/data/core" '
          'xmlns:v8ui="http://v8.1c.ru/8.1/data/ui" xmlns:web="http://v8.1c.ru/8.1/data/ui/colors/web" '
          'xmlns:win="http://v8.1c.ru/8.1/data/ui/colors/windows" xmlns:xen="http://v8.1c.ru/8.3/xcf/enums" '
          'xmlns:xpr="http://v8.1c.ru/8.3/xcf/predef" xmlns:xr="http://v8.1c.ru/8.3/xcf/readable" '
          'xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="2.20">\n')


def data_processor():
    return MDHEAD + f'''	<DataProcessor uuid="{uid(MD)}">
		<InternalInfo>
			<xr:GeneratedType name="DataProcessorObject.{NAME}" category="Object">
				<xr:TypeId>{uid(MD, "Object", "type")}</xr:TypeId>
				<xr:ValueId>{uid(MD, "Object", "value")}</xr:ValueId>
			</xr:GeneratedType>
			<xr:GeneratedType name="DataProcessorManager.{NAME}" category="Manager">
				<xr:TypeId>{uid(MD, "Manager", "type")}</xr:TypeId>
				<xr:ValueId>{uid(MD, "Manager", "value")}</xr:ValueId>
			</xr:GeneratedType>
		</InternalInfo>
		<Properties>
			<Name>{NAME}</Name>
			<Synonym>
{ls("Конструктор схем процессов", 4)}			</Synonym>
			<Comment/>
			<UseStandardCommands>true</UseStandardCommands>
			<DefaultForm>{MD}.Form.Форма</DefaultForm>
			<AuxiliaryForm/>
			<IncludeHelpInContents>false</IncludeHelpInContents>
			<ExtendedPresentation/>
			<Explanation/>
		</Properties>
		<ChildObjects>
			<Form>Форма</Form>
		</ChildObjects>
	</DataProcessor>
</MetaDataObject>
'''


def form_md():
    return MDHEAD + f'''	<Form uuid="{uid(MD, "Form", "Форма")}">
		<Properties>
			<Name>Форма</Name>
			<Synonym>
{ls("Конструктор схем процессов", 4)}			</Synonym>
			<Comment/>
			<FormType>Managed</FormType>
			<IncludeHelpInContents>false</IncludeHelpInContents>
			<UsePurposes>
				<v8:Value xsi:type="app:ApplicationUsePurpose">PlatformApplication</v8:Value>
			</UsePurposes>
			<ExtendedPresentation/>
		</Properties>
	</Form>
</MetaDataObject>
'''


class Ids:
    def __init__(self):
        self.n = 0

    def __call__(self):
        self.n += 1
        return self.n


def title(text, ind):
    t = "\t" * ind
    return f"{t}<Title>\n{ls(text, ind + 1)}{t}</Title>\n"


def button(ids, name, command, ind):
    t = "\t" * ind
    return (f'{t}<Button name="{name}" id="{ids()}">\n{t}\t<Type>CommandBarButton</Type>\n'
            f"{t}\t<CommandName>Form.Command.{command}</CommandName>\n"
            f'{t}\t<ExtendedTooltip name="{name}РасширеннаяПодсказка" id="{ids()}"/>\n{t}</Button>\n')


def input_field(ids, name, path, caption, ind, events=None, extra="", read_only=False):
    t = "\t" * ind
    s = f'{t}<InputField name="{name}" id="{ids()}">\n{t}\t<DataPath>{path}</DataPath>\n'
    if read_only:
        s += f"{t}\t<ReadOnly>true</ReadOnly>\n"
    s += title(caption, ind + 1) + extra
    s += (f'{t}\t<ContextMenu name="{name}КонтекстноеМеню" id="{ids()}"/>\n'
          f'{t}\t<ExtendedTooltip name="{name}РасширеннаяПодсказка" id="{ids()}"/>\n')
    if events:
        s += f"{t}\t<Events>\n" + "".join(f'{t}\t\t<Event name="{e}">{h}</Event>\n' for e, h in events) + f"{t}\t</Events>\n"
    return s + f"{t}</InputField>\n"


COMMANDS = [
    # имя, заголовок, подсказка, картинка
    ("Сохранить", "Сохранить", "Сохранить черновик и синхронизировать шаги и переходы", "StdPicture.Write"),
    ("Проверить", "Проверить", "Проверить схему перед публикацией", "StdPicture.CheckSyntax"),
    ("Опубликовать", "Опубликовать", "Проверить и опубликовать черновик", None),
    ("ИзменитьСхему", "Изменить схему", "Создать черновик из опубликованной версии", None),
    ("Редактирование", "Редактирование", "Включить или выключить правку схемы", "StdPicture.Change"),
    ("СвойстваЭлемента", "Свойства элемента", "Открыть настройки выделенного элемента схемы", None),
    ("Перечитать", "Перечитать", "Перечитать версию из базы", "StdPicture.Refresh"),
    ("СтруктураСхемы", "Структура схемы", "Диагностика: виды и свойства элементов графической схемы", None),
]


def form_xml():
    ids = Ids()
    s = ('<?xml version="1.0" encoding="UTF-8"?>\n<Form xmlns="http://v8.1c.ru/8.3/xcf/logform" '
         'xmlns:app="http://v8.1c.ru/8.2/managed-application/core" xmlns:cfg="http://v8.1c.ru/8.1/data/enterprise/current-config" '
         'xmlns:dcscor="http://v8.1c.ru/8.1/data-composition-system/core" xmlns:dcssch="http://v8.1c.ru/8.1/data-composition-system/schema" '
         'xmlns:dcsset="http://v8.1c.ru/8.1/data-composition-system/settings" xmlns:ent="http://v8.1c.ru/8.1/data/enterprise" '
         'xmlns:lf="http://v8.1c.ru/8.2/managed-application/logform" xmlns:style="http://v8.1c.ru/8.1/data/ui/style" '
         'xmlns:sys="http://v8.1c.ru/8.1/data/ui/fonts/system" xmlns:v8="http://v8.1c.ru/8.1/data/core" '
         'xmlns:v8ui="http://v8.1c.ru/8.1/data/ui" xmlns:web="http://v8.1c.ru/8.1/data/ui/colors/web" '
         'xmlns:win="http://v8.1c.ru/8.1/data/ui/colors/windows" xmlns:xr="http://v8.1c.ru/8.3/xcf/readable" '
         'xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="2.20">\n')
    s += '\t<AutoCommandBar name="ФормаКоманднаяПанель" id="-1">\n\t\t<ChildItems>\n'
    for cmd, *_ in COMMANDS:
        s += button(ids, "Форма" + cmd, cmd, 3)
    s += "\t\t</ChildItems>\n\t</AutoCommandBar>\n"
    s += ("\t<Events>\n\t\t<Event name=\"BeforeClose\">ПередЗакрытием</Event>\n"
          "\t\t<Event name=\"OnCreateAtServer\">ПриСозданииНаСервере</Event>\n\t</Events>\n\t<ChildItems>\n")
    # Шапка
    s += f'\t\t<UsualGroup name="Шапка" id="{ids()}">\n' + title("Шапка", 3)
    s += ("\t\t\t<Group>Horizontal</Group>\n\t\t\t<Behavior>Usual</Behavior>\n\t\t\t<Representation>None</Representation>\n"
          f"\t\t\t<ShowTitle>false</ShowTitle>\n\t\t\t<ExtendedTooltip name=\"ШапкаРасширеннаяПодсказка\" id=\"{ids()}\"/>\n"
          "\t\t\t<ChildItems>\n")
    s += input_field(ids, "Схема", "Схема", "Схема", 4, [("OnChange", "СхемаПриИзменении")])
    s += input_field(ids, "Версия", "Версия", "Версия", 4, [("OnChange", "ВерсияПриИзменении")])
    s += (f'\t\t\t\t<LabelField name="Статус" id="{ids()}">\n\t\t\t\t\t<DataPath>Статус</DataPath>\n'
          "\t\t\t\t\t<TitleLocation>None</TitleLocation>\n"
          f'\t\t\t\t\t<ContextMenu name="СтатусКонтекстноеМеню" id="{ids()}"/>\n'
          f'\t\t\t\t\t<ExtendedTooltip name="СтатусРасширеннаяПодсказка" id="{ids()}"/>\n\t\t\t\t</LabelField>\n')
    s += "\t\t\t</ChildItems>\n\t\t</UsualGroup>\n"
    # Схема + список шагов
    s += f'\t\t<UsualGroup name="Основная" id="{ids()}">\n' + title("Основная", 3)
    s += ("\t\t\t<Group>Horizontal</Group>\n\t\t\t<Behavior>Usual</Behavior>\n\t\t\t<Representation>None</Representation>\n"
          f"\t\t\t<ShowTitle>false</ShowTitle>\n\t\t\t<ExtendedTooltip name=\"ОсновнаяРасширеннаяПодсказка\" id=\"{ids()}\"/>\n"
          "\t\t\t<ChildItems>\n")
    s += (f'\t\t\t\t<GraphicalSchemaField name="ГрафСхема" id="{ids()}">\n\t\t\t\t\t<DataPath>ГрафСхема</DataPath>\n'
          + title("Схема процесса", 5) +
          "\t\t\t\t\t<TitleLocation>None</TitleLocation>\n\t\t\t\t\t<Width>100</Width>\n\t\t\t\t\t<Height>30</Height>\n"
          "\t\t\t\t\t<Edit>true</Edit>\n"
          f'\t\t\t\t\t<ContextMenu name="ГрафСхемаКонтекстноеМеню" id="{ids()}"/>\n'
          f'\t\t\t\t\t<ExtendedTooltip name="ГрафСхемаРасширеннаяПодсказка" id="{ids()}"/>\n'
          '\t\t\t\t\t<Events>\n\t\t\t\t\t\t<Event name="Selection">ГрафСхемаВыбор</Event>\n\t\t\t\t\t</Events>\n'
          "\t\t\t\t</GraphicalSchemaField>\n")
    t = "\t" * 4
    s += (f'{t}<Table name="Шаги" id="{ids()}">\n{t}\t<Representation>List</Representation>\n'
          f"{t}\t<ReadOnly>true</ReadOnly>\n{t}\t<ChangeRowSet>false</ChangeRowSet>\n{t}\t<ChangeRowOrder>false</ChangeRowOrder>\n"
          f"{t}\t<Width>35</Width>\n{t}\t<DataPath>Шаги</DataPath>\n" + title("Шаги схемы", 5) +
          f"{t}\t<RowFilter xsi:nil=\"true\"/>\n"
          f'{t}\t<ContextMenu name="ШагиКонтекстноеМеню" id="{ids()}"/>\n'
          f'{t}\t<AutoCommandBar name="ШагиКоманднаяПанель" id="{ids()}">\n{t}\t\t<Autofill>false</Autofill>\n{t}\t</AutoCommandBar>\n'
          f'{t}\t<ExtendedTooltip name="ШагиРасширеннаяПодсказка" id="{ids()}"/>\n')
    for add, typ in (("СтрокаПоиска", "SearchStringRepresentation"), ("СостояниеПросмотра", "ViewStatusRepresentation"),
                     ("УправлениеПоиском", "SearchControl")):
        tag = {"СтрокаПоиска": "SearchStringAddition", "СостояниеПросмотра": "ViewStatusAddition",
               "УправлениеПоиском": "SearchControlAddition"}[add]
        s += (f'{t}\t<{tag} name="Шаги{add}" id="{ids()}">\n{t}\t\t<AdditionSource>\n{t}\t\t\t<Item>Шаги</Item>\n'
              f"{t}\t\t\t<Type>{typ}</Type>\n{t}\t\t</AdditionSource>\n"
              f'{t}\t\t<ContextMenu name="Шаги{add}КонтекстноеМеню" id="{ids()}"/>\n'
              f'{t}\t\t<ExtendedTooltip name="Шаги{add}РасширеннаяПодсказка" id="{ids()}"/>\n{t}\t</{tag}>\n')
    s += f'{t}\t<Events>\n{t}\t\t<Event name="Selection">ШагиВыбор</Event>\n{t}\t</Events>\n{t}\t<ChildItems>\n'
    for col, cap in (("Ошибка", "!"), ("Наименование", "Шаг"), ("ТипШага", "Тип")):
        s += (f'{t}\t\t<InputField name="Шаги{col}" id="{ids()}">\n{t}\t\t\t<DataPath>Шаги.{col}</DataPath>\n'
              + title(cap, 7) +
              f'{t}\t\t\t<ContextMenu name="Шаги{col}КонтекстноеМеню" id="{ids()}"/>\n'
              f'{t}\t\t\t<ExtendedTooltip name="Шаги{col}РасширеннаяПодсказка" id="{ids()}"/>\n{t}\t\t</InputField>\n')
    s += f"{t}\t</ChildItems>\n{t}</Table>\n"
    s += "\t\t\t</ChildItems>\n\t\t</UsualGroup>\n"
    s += input_field(ids, "ТекстПроверки", "ТекстПроверки", "Результат проверки", 2,
                     read_only=True, extra="\t\t\t<TitleLocation>Top</TitleLocation>\n"
                           "\t\t\t<Height>4</Height>\n\t\t\t<MultiLine>true</MultiLine>\n")
    s += "\t</ChildItems>\n"

    def attr(name, aid, type_xml, cap=None, extra=""):
        a = f'\t\t<Attribute name="{name}" id="{aid}">\n'
        if cap:
            a += title(cap, 3)
        return a + f"\t\t\t<Type>\n{type_xml}\t\t\t</Type>\n{extra}\t\t</Attribute>\n"

    def ty(x):
        return f"\t\t\t\t<v8:Type>{x}</v8:Type>\n"

    string0 = ("\t\t\t\t<v8:Type>xs:string</v8:Type>\n\t\t\t\t<v8:StringQualifiers>\n\t\t\t\t\t<v8:Length>0</v8:Length>\n"
               "\t\t\t\t\t<v8:AllowedLength>Variable</v8:AllowedLength>\n\t\t\t\t</v8:StringQualifiers>\n")
    s += "\t<Attributes>\n"
    s += attr("Объект", 1, ty(f"cfg:DataProcessorObject.{NAME}"), extra="\t\t\t<MainAttribute>true</MainAttribute>\n")
    s += attr("Схема", 2, ty("cfg:CatalogRef.кбп_СхемыПроцессов"), "Схема")
    s += attr("Версия", 3, ty("cfg:CatalogRef.кбп_ВерсииСхем"), "Версия")
    s += attr("ГрафСхема", 4, '\t\t\t\t<v8:Type xmlns:d5p1="http://v8.1c.ru/8.2/data/graphscheme">d5p1:FlowchartContextType</v8:Type>\n',
              "Схема процесса")
    s += attr("Статус", 5, string0, "Статус")
    s += attr("ЭтоЧерновик", 6, ty("xs:boolean"), "Это черновик")
    s += attr("ТекстПроверки", 7, string0, "Результат проверки")
    cols = [("Ссылка", ty("cfg:CatalogRef.кбп_ЭлементыСхем"), "Элемент"),
            ("ИдЭлемента", string0, "Ид элемента"),
            ("Наименование", string0, "Шаг"),
            ("ТипШага", ty("cfg:EnumRef.кбп_ТипыШагов"), "Тип"),
            ("Ошибка", ty("xs:boolean"), "Ошибка")]
    col_xml = "\t\t\t<Columns>\n"
    for i, (c, tx, cap) in enumerate(cols, 1):
        col_xml += (f'\t\t\t\t<Column name="{c}" id="{i}">\n' + title(cap, 5).replace("\t\t\t\t\t<", "\t\t\t\t\t<")
                    + "\t\t\t\t\t<Type>\n" + tx.replace("\t\t\t\t<", "\t\t\t\t\t\t<") + "\t\t\t\t\t</Type>\n\t\t\t\t</Column>\n")
    col_xml += "\t\t\t</Columns>\n"
    s += attr("Шаги", 8, ty("v8:ValueTable"), "Шаги схемы", extra=col_xml)
    s += "\t</Attributes>\n\t<Commands>\n"
    for i, (cmd, cap, tip, pic) in enumerate(COMMANDS, 1):
        s += f'\t\t<Command name="{cmd}" id="{i}">\n' + title(cap, 3)
        s += f"\t\t\t<ToolTip>\n{ls(tip, 4)}\t\t\t</ToolTip>\n"
        if pic:
            s += f"\t\t\t<Picture>\n\t\t\t\t<xr:Ref>{pic}</xr:Ref>\n\t\t\t\t<xr:LoadTransparent>true</xr:LoadTransparent>\n\t\t\t</Picture>\n"
        s += f"\t\t\t<Action>{cmd}</Action>\n"
        if pic:
            s += "\t\t\t<Representation>TextPicture</Representation>\n"
        s += "\t\t\t<CurrentRowUse>DontUse</CurrentRowUse>\n\t\t</Command>\n"
    s += "\t</Commands>\n\t<Parameters>\n\t\t<Parameter name=\"Схема\">\n\t\t\t<Type>\n"
    s += "\t\t\t\t<v8:Type>cfg:CatalogRef.кбп_СхемыПроцессов</v8:Type>\n\t\t\t</Type>\n\t\t</Parameter>\n\t</Parameters>\n</Form>\n"
    return s


def main():
    write(f"DataProcessors/{NAME}.xml", data_processor())
    write(f"DataProcessors/{NAME}/Forms/Форма.xml", form_md())
    write(f"DataProcessors/{NAME}/Forms/Форма/Ext/Form.xml", form_xml())
    if BSL is not None:
        write(f"DataProcessors/{NAME}/Forms/Форма/Ext/Form/Module.bsl", (BSL / "Форма.bsl").read_text(encoding="utf-8"))
    print("ok")


if __name__ == "__main__":
    main()
