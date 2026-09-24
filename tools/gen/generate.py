#!/usr/bin/env python3
"""Генератор XML-выгрузки расширения «Конструктор бизнес-процессов».

Читает docs/СпецификацияМетаданных.md и пишет файлы в формате выгрузки
Конфигуратора (DumpConfigToFiles -format Hierarchical, версия 2.20),
которые загружаются командой /LoadConfigFromFiles ... -Extension ...

Запуск:  python3 tools/gen/generate.py [--out build/cfe] [--users-uuid <UUID>] [--compat Version8_3_24]
                                        [--adopted <каталог выгрузки>] [--force-modules]
"""
import argparse
import re
import shutil
import sys
import uuid
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "docs" / "СпецификацияМетаданных.md"
EXT_NAME = "КонструкторБизнесПроцессов"
EXT_SYNONYM = "Конструктор бизнес-процессов"
PREFIX = "кбп_"
MAIN_ROLE = "кбп_ИспользованиеПроцессов"
SUBSYSTEM = "кбп_БизнесПроцессы"
# UUID справочника «Пользователи» в базе разработки (из выгрузки Конфигуратора).
# В БСП 3.1 (1c-syntax/ssl_3_1) — 579baaa4-6493-4d99-8744-6399757295c7. Другая база — ключ --users-uuid.
USERS_BASE_UUID = ["fa1ef4b3-fc76-4b08-bb66-d89a7a1b66b1"]
NS = uuid.UUID("6f1c3a52-3d8e-4b6a-9d61-6b0f2d1c7a10")

HEADER = ('﻿<?xml version="1.0" encoding="UTF-8"?>\n'
          '<MetaDataObject xmlns="http://v8.1c.ru/8.3/MDClasses" xmlns:app="http://v8.1c.ru/8.2/managed-application/core" '
          'xmlns:cfg="http://v8.1c.ru/8.1/data/enterprise/current-config" xmlns:cmi="http://v8.1c.ru/8.2/managed-application/cmi" '
          'xmlns:ent="http://v8.1c.ru/8.1/data/enterprise" xmlns:lf="http://v8.1c.ru/8.2/managed-application/logform" '
          'xmlns:style="http://v8.1c.ru/8.1/data/ui/style" xmlns:sys="http://v8.1c.ru/8.1/data/ui/fonts/system" '
          'xmlns:v8="http://v8.1c.ru/8.1/data/core" xmlns:v8ui="http://v8.1c.ru/8.1/data/ui" '
          'xmlns:web="http://v8.1c.ru/8.1/data/ui/colors/web" xmlns:win="http://v8.1c.ru/8.1/data/ui/colors/windows" '
          'xmlns:xen="http://v8.1c.ru/8.3/xcf/enums" xmlns:xpr="http://v8.1c.ru/8.3/xcf/predef" '
          'xmlns:xr="http://v8.1c.ru/8.3/xcf/readable" xmlns:xs="http://www.w3.org/2001/XMLSchema" '
          'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="2.20">\n')
FOOTER = "</MetaDataObject>\n"


def uid(*parts):
    return str(uuid.uuid5(NS, "/".join(parts)))


def synonym_from_name(name):
    """ДатаПубликации → Дата публикации; ИдКнопки → Ид кнопки; ЭтоHTML → Это HTML."""
    if name.startswith(PREFIX):
        name = name[len(PREFIX):]
    words = re.findall(r"[А-ЯЁA-Z]+(?![а-яёa-z])|[А-ЯЁA-Z][а-яёa-z]*|[а-яёa-z]+|\d+", name)
    if not words:
        return name
    out = [words[0]]
    for w in words[1:]:
        out.append(w if w.isupper() and len(w) > 1 else w.lower())
    return " ".join(out)


def lstr(text, indent):
    if not text:
        return None
    t = "\t" * indent
    return (f"{t}\t<v8:item>\n{t}\t\t<v8:lang>ru</v8:lang>\n"
            f"{t}\t\t<v8:content>{escape(text)}</v8:content>\n{t}\t</v8:item>\n")


def el(tag, value, indent):
    t = "\t" * indent
    if value is None or value == "":
        return f"{t}<{tag}/>\n"
    return f"{t}<{tag}>{value}</{tag}>\n"


def el_lstr(tag, text, indent):
    body = lstr(text, indent)
    t = "\t" * indent
    return f"{t}<{tag}/>\n" if body is None else f"{t}<{tag}>\n{body}{t}</{tag}>\n"


# ---------------------------------------------------------------- разбор спецификации

KIND_MAP = {
    "Перечисление": "Enum", "Справочник": "Catalog", "ПланВидовХарактеристик": "ChartOfCharacteristicTypes",
    "Документ": "Document", "РегистрСведений": "InformationRegister", "ОбщийМодуль": "CommonModule",
    "Роль": "Role", "РегламентноеЗадание": "ScheduledJob", "Подсистема": "Subsystem",
}


def parse_table(lines, i):
    """Таблица markdown с позиции i → (строки, следующая позиция)."""
    rows = []
    header = [c.strip() for c in lines[i].strip().strip("|").split("|")]
    i += 2  # заголовок и разделитель
    while i < len(lines) and lines[i].lstrip().startswith("|"):
        cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
        rows.append(dict(zip(header, cells)))
        i += 1
    return rows, i


def parse_spec(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    objects, cur, target = [], None, None
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^### (\S+): (\S+)\s*$", line)
        if m and m.group(1) in KIND_MAP:
            cur = {"kind": KIND_MAP[m.group(1)], "name": m.group(2), "synonym": None,
                   "props": {}, "rows": [], "ts": []}
            objects.append(cur)
            target = cur
            i += 1
            continue
        if line.startswith("## ") or (line.startswith("### ") and not m):
            cur = target = None
        if cur is not None:
            if line.startswith("Синоним:"):
                cur["synonym"] = line.split(":", 1)[1].strip()
            elif line.startswith("Свойства:"):
                for pair in line.split(":", 1)[1].split(";"):
                    if "=" in pair:
                        k, v = pair.split("=", 1)
                        cur["props"][k.strip()] = v.strip()
            elif line.startswith("#### ТЧ:"):
                ts = {"name": line.split(":", 1)[1].strip(), "rows": []}
                cur["ts"].append(ts)
                target = ts
            elif line.lstrip().startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|[-| ]+\|\s*$", lines[i + 1]):
                rows, i = parse_table(lines, i)
                target["rows"].extend(rows)
                continue
        i += 1
    return objects


# ---------------------------------------------------------------- типы

REF_PREFIX = {
    "СправочникСсылка": "CatalogRef", "ДокументСсылка": "DocumentRef",
    "ПеречислениеСсылка": "EnumRef", "ПВХСсылка": "ChartOfCharacteristicTypesRef",
}


def parse_type(spec, owner_path):
    """Строка типа из спецификации → (xml-фрагмент содержимого <Type>, путь LinkByType|None, признаки)."""
    parts = [p.strip() for p in spec.split("|")]
    types, quals, link = [], [], None
    info = {"bool": False, "string": False, "number": False, "date": False, "ref": False}
    for p in parts:
        m = re.fullmatch(r"Строка\((\d+)\)", p)
        if m:
            types.append("<v8:Type>xs:string</v8:Type>")
            quals.append(("s", f"<v8:StringQualifiers>\n\t<v8:Length>{m.group(1)}</v8:Length>\n"
                               f"\t<v8:AllowedLength>Variable</v8:AllowedLength>\n</v8:StringQualifiers>"))
            info["string"] = True
            continue
        m = re.fullmatch(r"Число\((\d+)(?:,(\d+))?\)(\+?)", p)
        if m:
            types.append("<v8:Type>xs:decimal</v8:Type>")
            sign = "Nonnegative" if m.group(3) else "Any"
            quals.append(("n", f"<v8:NumberQualifiers>\n\t<v8:Digits>{m.group(1)}</v8:Digits>\n"
                               f"\t<v8:FractionDigits>{m.group(2) or 0}</v8:FractionDigits>\n"
                               f"\t<v8:AllowedSign>{sign}</v8:AllowedSign>\n</v8:NumberQualifiers>"))
            info["number"] = True
            continue
        if p in ("Дата", "ДатаВремя"):
            types.append("<v8:Type>xs:dateTime</v8:Type>")
            quals.append(("d", "<v8:DateQualifiers>\n\t<v8:DateFractions>"
                               + ("Date" if p == "Дата" else "DateTime") + "</v8:DateFractions>\n</v8:DateQualifiers>"))
            info["date"] = True
            continue
        if p == "Булево":
            types.append("<v8:Type>xs:boolean</v8:Type>")
            info["bool"] = True
            continue
        if p == "ХранилищеЗначения":
            types.append("<v8:Type>v8:ValueStorage</v8:Type>")
            continue
        if p == "ЛюбаяСсылка":
            types.append("<v8:TypeSet>cfg:AnyIBRef</v8:TypeSet>")
            info["ref"] = True
            continue
        m = re.fullmatch(r"Характеристика\.(\S+)\((\S+)\)", p)
        if m:
            types.append(f"<v8:TypeSet>cfg:Characteristic.{m.group(1)}</v8:TypeSet>")
            link = m.group(2)
            info["ref"] = True
            continue
        m = re.fullmatch(r"(\w+)\.(\S+)", p)
        if m and m.group(1) in REF_PREFIX:
            types.append(f"<v8:Type>cfg:{REF_PREFIX[m.group(1)]}.{m.group(2)}</v8:Type>")
            info["ref"] = True
            continue
        raise ValueError(f"{owner_path}: неизвестный тип «{p}»")
    order = {"n": 0, "s": 1, "d": 2}
    body = types + [q for _, q in sorted(quals, key=lambda x: order[x[0]])]
    return body, link, info


def type_block(body, indent):
    t = "\t" * indent
    out = f"{t}<Type>\n"
    for b in body:
        for ln in b.split("\n"):
            out += f"{t}\t{ln}\n"
    return out + f"{t}</Type>\n"


def fill_value(info, body_len):
    if body_len == 1 and info["string"]:
        return '<FillValue xsi:type="xs:string"/>'
    return '<FillValue xsi:nil="true"/>'


# ---------------------------------------------------------------- реквизиты

def attribute_xml(tag, row, owner_path, kind, indent, link_path_prefix):
    """kind: catalog | ts | document | register_dim | register_res | register_attr | ccht."""
    name = row["Имя"]
    path = f"{owner_path}.{tag}.{name}"
    body, link, info = parse_type(row["Тип"], path)
    syn = row.get("Синоним") or synonym_from_name(name)
    idx = {"И": "Index", "ИД": "IndexWithAdditionalOrder"}.get(row.get("Инд.", ""), "DontIndex")
    t = "\t" * indent
    p = indent + 2
    out = f'{t}<{tag} uuid="{uid(path)}">\n{t}\t<Properties>\n'
    out += el("Name", name, p) + el_lstr("Synonym", syn, p) + el("Comment", None, p)
    out += type_block(body, p)
    out += (el("PasswordMode", "false", p) + el("Format", None, p) + el("EditFormat", None, p)
            + el("ToolTip", None, p) + el("MarkNegatives", "false", p) + el("Mask", None, p)
            + el("MultiLine", "false", p) + el("ExtendedEdit", "false", p)
            + "\t" * p + '<MinValue xsi:nil="true"/>\n' + "\t" * p + '<MaxValue xsi:nil="true"/>\n')
    if kind != "ts":
        out += el("FillFromFillingValue", "false", p) + "\t" * p + fill_value(info, len([b for b in body if "Type" in b])) + "\n"
    out += (el("FillChecking", "DontCheck", p) + el("ChoiceFoldersAndItems", "Items", p)
            + el("ChoiceParameterLinks", None, p) + el("ChoiceParameters", None, p)
            + el("QuickChoice", "Auto", p) + el("CreateOnInput", "Auto", p) + el("ChoiceForm", None, p))
    if link:
        out += (f"{t}\t\t<LinkByType>\n{t}\t\t\t<xr:DataPath>{link_path_prefix}.{link}</xr:DataPath>\n"
                f"{t}\t\t\t<xr:LinkItem>0</xr:LinkItem>\n{t}\t\t</LinkByType>\n")
    else:
        out += el("LinkByType", None, p)
    out += el("ChoiceHistoryOnInput", "Auto", p)
    if kind == "register_dim":
        out += (el("Master", "false", p) + el("MainFilter", "true", p) + el("DenyIncompleteValues", "false", p))
    if kind == "catalog":
        out += el("Use", "ForItem", p)
    out += el("Indexing", idx, p)
    if kind == "ccht":  # у ПВХ Конфигуратор выгружает Use после Indexing
        out += el("Use", "ForItem", p)
    out += el("FullTextSearch", "Use", p) + el("DataHistory", "Use", p)
    if kind == "register_dim":
        out += el("TypeReductionMode", "TransformValues", p)
    out += f"{t}\t</Properties>\n{t}</{tag}>\n"
    return out


def generated_types(md_path, pairs, indent):
    t = "\t" * indent
    out = f"{t}<InternalInfo>\n"
    for prefix, category in pairs:
        name = f"{prefix}.{md_path.split('.', 1)[1]}"
        out += (f'{t}\t<xr:GeneratedType name="{name}" category="{category}">\n'
                f"{t}\t\t<xr:TypeId>{uid(md_path, prefix, 'type')}</xr:TypeId>\n"
                f"{t}\t\t<xr:ValueId>{uid(md_path, prefix, 'value')}</xr:ValueId>\n"
                f"{t}\t</xr:GeneratedType>\n")
    return out + f"{t}</InternalInfo>\n"


# Длина номера строки ТЧ: 9 допустимо только с режима совместимости 8.3.27, ниже — строго 5.
LINE_NUMBER_LENGTH = ["5"]


def compat_version(compat):
    m = re.fullmatch(r"Version(\d+)_(\d+)_(\d+)", compat)
    if not m:
        sys.exit(f"Неверный режим совместимости: {compat} (ожидается вида Version8_3_24)")
    return tuple(int(x) for x in m.groups())


def tabular_section_xml(ts, owner_md, kind_prefix, indent):
    md = f"{owner_md}.TabularSection.{ts['name']}"
    t = "\t" * indent
    tail = owner_md.split(".", 1)[1] + "." + ts["name"]
    out = f'{t}<TabularSection uuid="{uid(md)}">\n{t}\t<InternalInfo>\n'
    for cat, suffix in (("TabularSection", "TabularSection"), ("TabularSectionRow", "TabularSectionRow")):
        out += (f'{t}\t\t<xr:GeneratedType name="{kind_prefix}{suffix}.{tail}" category="{cat}">\n'
                f"{t}\t\t\t<xr:TypeId>{uid(md, cat, 'type')}</xr:TypeId>\n"
                f"{t}\t\t\t<xr:ValueId>{uid(md, cat, 'value')}</xr:ValueId>\n{t}\t\t</xr:GeneratedType>\n")
    p = indent + 2
    out += f"{t}\t</InternalInfo>\n{t}\t<Properties>\n"
    out += (el("Name", ts["name"], p) + el_lstr("Synonym", synonym_from_name(ts["name"]), p) + el("Comment", None, p)
            + el("ToolTip", None, p) + el("FillChecking", "DontCheck", p))
    if kind_prefix in ("Catalog", "ChartOfCharacteristicTypes"):
        out += el("Use", "ForItem", p)
    out += el("LineNumberLength", LINE_NUMBER_LENGTH[0], p) + f"{t}\t</Properties>\n{t}\t<ChildObjects>\n"
    for row in ts["rows"]:
        out += attribute_xml("Attribute", row, md, "ts", indent + 2, md + ".Attribute")
    return out + f"{t}\t</ChildObjects>\n{t}</TabularSection>\n"


def input_by_string(md, fields, indent):
    t = "\t" * indent
    out = f"{t}<InputByString>\n"
    for f in fields:
        out += f"{t}\t<xr:Field>{md}.StandardAttribute.{f}</xr:Field>\n"
    return out + f"{t}</InputByString>\n"


def wrap(tag, md, inner):
    return HEADER + f'\t<{tag} uuid="{uid(md)}">\n' + inner + f"\t</{tag}>\n" + FOOTER


# ---------------------------------------------------------------- объекты

def gen_enum(o):
    md = f"Enum.{o['name']}"
    s = generated_types(md, [("EnumRef", "Ref"), ("EnumManager", "Manager"), ("EnumList", "List")], 2)
    s += "\t\t<Properties>\n" + el("Name", o["name"], 3) + el_lstr("Synonym", o["synonym"], 3) + el("Comment", None, 3)
    s += (el("UseStandardCommands", "false", 3) + el("Characteristics", None, 3) + el("QuickChoice", "true", 3)
          + el("ChoiceMode", "BothWays", 3) + el("DefaultListForm", None, 3) + el("DefaultChoiceForm", None, 3)
          + el("AuxiliaryListForm", None, 3) + el("AuxiliaryChoiceForm", None, 3) + el("ListPresentation", None, 3)
          + el("ExtendedListPresentation", None, 3) + el("Explanation", None, 3) + el("ChoiceHistoryOnInput", "Auto", 3))
    s += "\t\t</Properties>\n\t\t<ChildObjects>\n"
    for r in o["rows"]:
        v = r["Значение"]
        s += (f'\t\t\t<EnumValue uuid="{uid(md, "EnumValue", v)}">\n\t\t\t\t<Properties>\n'
              + el("Name", v, 5) + el_lstr("Synonym", r.get("Синоним") or synonym_from_name(v), 5) + el("Comment", None, 5)
              + "\t\t\t\t</Properties>\n\t\t\t</EnumValue>\n")
    s += "\t\t</ChildObjects>\n"
    return wrap("Enum", md, s)


def yes(v):
    return str(v).lower() in ("да", "true", "1")


def gen_catalog(o):
    md = f"Catalog.{o['name']}"
    pr = o["props"]
    code_len = int(pr.get("ДлинаКода", 0))
    desc_len = int(pr.get("ДлинаНаименования", 150))
    hier = yes(pr.get("Иерархический", "Нет"))
    owner = pr.get("Владелец")
    s = generated_types(md, [("CatalogObject", "Object"), ("CatalogRef", "Ref"), ("CatalogSelection", "Selection"),
                             ("CatalogList", "List"), ("CatalogManager", "Manager")], 2)
    p = 3
    s += "\t\t<Properties>\n" + el("Name", o["name"], p) + el_lstr("Synonym", o["synonym"], p) + el("Comment", None, p)
    s += (el("Hierarchical", str(hier).lower(), p)
          + el("HierarchyType", "HierarchyFoldersAndItems" if pr.get("ВидИерархии", "ГруппыИЭлементы") == "ГруппыИЭлементы" else "HierarchyOfItems", p)
          + el("LimitLevelCount", "false", p) + el("LevelCount", "2", p) + el("FoldersOnTop", "true", p)
          + el("UseStandardCommands", "true", p))
    if owner:
        s += f"\t\t\t<Owners>\n\t\t\t\t<xr:Item xsi:type=\"xr:MDObjectRef\">Catalog.{owner}</xr:Item>\n\t\t\t</Owners>\n"
    else:
        s += el("Owners", None, p)
    s += (el("SubordinationUse", "ToItems", p) + el("CodeLength", code_len, p) + el("DescriptionLength", desc_len, p)
          + el("CodeType", "String", p) + el("CodeAllowedLength", "Variable", p)
          + el("CodeSeries", "WithinSubordination" if owner else "WholeCatalog", p)
          + el("CheckUnique", str(code_len > 0).lower(), p)
          + el("Autonumbering", str(yes(pr.get("Автонумерация", "Нет"))).lower(), p)
          + el("DefaultPresentation", "AsDescription", p) + el("Characteristics", None, p)
          + el("PredefinedDataUpdate", "Auto", p) + el("EditType", "InDialog", p) + el("QuickChoice", "false", p)
          + el("ChoiceMode", "BothWays", p))
    fields = ["Description"] + (["Code"] if code_len else [])
    s += input_by_string(md, fields, p)
    s += (el("SearchStringModeOnInputByString", "Begin", p) + el("FullTextSearchOnInputByString", "DontUse", p)
          + el("ChoiceDataGetModeOnInputByString", "Directly", p))
    for f in ("DefaultObjectForm", "DefaultFolderForm", "DefaultListForm", "DefaultChoiceForm", "DefaultFolderChoiceForm",
              "AuxiliaryObjectForm", "AuxiliaryFolderForm", "AuxiliaryListForm", "AuxiliaryChoiceForm", "AuxiliaryFolderChoiceForm"):
        s += el(f, None, p)
    s += (el("IncludeHelpInContents", "false", p) + el("BasedOn", None, p) + el("DataLockFields", None, p)
          + el("DataLockControlMode", "Managed", p) + el("FullTextSearch", "Use", p) + el("ObjectPresentation", None, p)
          + el("ExtendedObjectPresentation", None, p) + el("ListPresentation", None, p)
          + el("ExtendedListPresentation", None, p) + el("Explanation", None, p) + el("CreateOnInput", "DontUse", p)
          + el("ChoiceHistoryOnInput", "Auto", p) + el("DataHistory", "DontUse", p)
          + el("UpdateDataHistoryImmediatelyAfterWrite", "false", p)
          + el("ExecuteAfterWriteDataHistoryVersionProcessing", "false", p))
    s += "\t\t</Properties>\n\t\t<ChildObjects>\n"
    for r in o["rows"]:
        s += attribute_xml("Attribute", r, md, "catalog", 3, md + ".Attribute")
    for ts in o["ts"]:
        s += tabular_section_xml(ts, md, "Catalog", 3)
    s += "\t\t</ChildObjects>\n"
    return wrap("Catalog", md, s)


def gen_ccht(o):
    md = f"ChartOfCharacteristicTypes.{o['name']}"
    pr = o["props"]
    s = generated_types(md, [("ChartOfCharacteristicTypesObject", "Object"), ("ChartOfCharacteristicTypesRef", "Ref"),
                             ("ChartOfCharacteristicTypesSelection", "Selection"), ("ChartOfCharacteristicTypesList", "List"),
                             ("Characteristic", "Characteristic"), ("ChartOfCharacteristicTypesManager", "Manager")], 2)
    p = 3
    body, _, _ = parse_type("Булево | Строка(1024) | ДатаВремя | Число(17,5) | ЛюбаяСсылка", md)
    s += "\t\t<Properties>\n" + el("Name", o["name"], p) + el_lstr("Synonym", o["synonym"], p) + el("Comment", None, p)
    s += (el("UseStandardCommands", "true", p) + el("IncludeHelpInContents", "false", p)
          + el("CharacteristicExtValues", None, p) + type_block(body, p)
          + el("Hierarchical", "false", p) + el("FoldersOnTop", "true", p) + el("CodeLength", "0", p)
          + el("CodeAllowedLength", "Variable", p) + el("DescriptionLength", pr.get("ДлинаНаименования", 150), p)
          + el("CodeSeries", "WholeCharacteristicKind", p) + el("CheckUnique", "false", p)
          + el("Autonumbering", "false", p) + el("DefaultPresentation", "AsDescription", p)
          + el("Characteristics", None, p) + el("PredefinedDataUpdate", "Auto", p) + el("EditType", "InDialog", p)
          + el("QuickChoice", "false", p) + el("ChoiceMode", "BothWays", p))
    s += input_by_string(md, ["Description"], p)
    s += (el("CreateOnInput", "DontUse", p) + el("SearchStringModeOnInputByString", "Begin", p)
          + el("ChoiceDataGetModeOnInputByString", "Directly", p) + el("FullTextSearchOnInputByString", "DontUse", p)
          + el("ChoiceHistoryOnInput", "Auto", p))
    for f in ("DefaultObjectForm", "DefaultFolderForm", "DefaultListForm", "DefaultChoiceForm", "DefaultFolderChoiceForm",
              "AuxiliaryObjectForm", "AuxiliaryFolderForm", "AuxiliaryListForm", "AuxiliaryChoiceForm", "AuxiliaryFolderChoiceForm"):
        s += el(f, None, p)
    s += (el("BasedOn", None, p) + el("DataLockFields", None, p) + el("DataLockControlMode", "Managed", p)
          + el("FullTextSearch", "Use", p) + el("ObjectPresentation", None, p) + el("ExtendedObjectPresentation", None, p)
          + el("ListPresentation", None, p) + el("ExtendedListPresentation", None, p) + el("Explanation", None, p)
          + el("DataHistory", "DontUse", p) + el("UpdateDataHistoryImmediatelyAfterWrite", "false", p)
          + el("ExecuteAfterWriteDataHistoryVersionProcessing", "false", p))
    s += "\t\t</Properties>\n\t\t<ChildObjects>\n"
    for r in o["rows"]:
        s += attribute_xml("Attribute", r, md, "ccht", 3, md + ".Attribute")
    for ts in o["ts"]:
        s += tabular_section_xml(ts, md, "ChartOfCharacteristicTypes", 3)
    s += "\t\t</ChildObjects>\n"
    return wrap("ChartOfCharacteristicTypes", md, s)


def gen_document(o):
    md = f"Document.{o['name']}"
    pr = o["props"]
    s = generated_types(md, [("DocumentObject", "Object"), ("DocumentRef", "Ref"), ("DocumentSelection", "Selection"),
                             ("DocumentList", "List"), ("DocumentManager", "Manager")], 2)
    p = 3
    s += "\t\t<Properties>\n" + el("Name", o["name"], p) + el_lstr("Synonym", o["synonym"], p) + el("Comment", None, p)
    s += (el("UseStandardCommands", "true", p) + el("Numerator", None, p) + el("NumberType", "String", p)
          + el("NumberLength", pr.get("ДлинаНомера", 11), p) + el("NumberAllowedLength", "Variable", p)
          + el("NumberPeriodicity", "Year", p) + el("CheckUnique", "true", p) + el("Autonumbering", "true", p)
          + el("Characteristics", None, p) + el("BasedOn", None, p))
    s += input_by_string(md, ["Number"], p)
    s += (el("CreateOnInput", "DontUse", p) + el("SearchStringModeOnInputByString", "Begin", p)
          + el("FullTextSearchOnInputByString", "DontUse", p) + el("ChoiceDataGetModeOnInputByString", "Directly", p))
    for f in ("DefaultObjectForm", "DefaultListForm", "DefaultChoiceForm", "AuxiliaryObjectForm", "AuxiliaryListForm",
              "AuxiliaryChoiceForm"):
        s += el(f, None, p)
    regs = [r.strip() for r in pr.get("Движения", "").split(",") if r.strip()]
    s += (el("Posting", "Allow" if regs else "Deny", p) + el("RealTimePosting", "Deny", p)
          + el("RegisterRecordsDeletion", "AutoDeleteOnUnpost", p) + el("RegisterRecordsWritingOnPost", "WriteModified", p)
          + el("SequenceFilling", "AutoFill", p))
    if regs:
        s += "\t\t\t<RegisterRecords>\n" + "".join(
            f'\t\t\t\t<xr:Item xsi:type="xr:MDObjectRef">InformationRegister.{r}</xr:Item>\n' for r in regs) + "\t\t\t</RegisterRecords>\n"
    else:
        s += el("RegisterRecords", None, p)
    s += (el("PostInPrivilegedMode", "true", p) + el("UnpostInPrivilegedMode", "true", p)
          + el("IncludeHelpInContents", "false", p) + el("DataLockFields", None, p)
          + el("DataLockControlMode", "Managed", p) + el("FullTextSearch", "Use", p) + el("ObjectPresentation", None, p)
          + el("ExtendedObjectPresentation", None, p) + el("ListPresentation", None, p)
          + el("ExtendedListPresentation", None, p) + el("Explanation", None, p) + el("ChoiceHistoryOnInput", "Auto", p)
          + el("DataHistory", "DontUse", p) + el("UpdateDataHistoryImmediatelyAfterWrite", "false", p)
          + el("ExecuteAfterWriteDataHistoryVersionProcessing", "false", p))
    s += "\t\t</Properties>\n\t\t<ChildObjects>\n"
    for r in o["rows"]:
        s += attribute_xml("Attribute", r, md, "document", 3, md + ".Attribute")
    for ts in o["ts"]:
        s += tabular_section_xml(ts, md, "Document", 3)
    s += "\t\t</ChildObjects>\n"
    return wrap("Document", md, s)


def gen_register(o):
    md = f"InformationRegister.{o['name']}"
    pr = o["props"]
    subordinate = pr.get("РежимЗаписи") == "ПодчинениеРегистратору"
    s = generated_types(md, [("InformationRegisterRecord", "Record"), ("InformationRegisterManager", "Manager"),
                             ("InformationRegisterSelection", "Selection"), ("InformationRegisterList", "List"),
                             ("InformationRegisterRecordSet", "RecordSet"), ("InformationRegisterRecordKey", "RecordKey"),
                             ("InformationRegisterRecordManager", "RecordManager")], 2)
    p = 3
    s += "\t\t<Properties>\n" + el("Name", o["name"], p) + el_lstr("Synonym", o["synonym"], p) + el("Comment", None, p)
    s += (el("UseStandardCommands", "true", p) + el("EditType", "InDialog", p) + el("DefaultRecordForm", None, p)
          + el("DefaultListForm", None, p) + el("AuxiliaryRecordForm", None, p) + el("AuxiliaryListForm", None, p)
          + el("InformationRegisterPeriodicity", "Nonperiodical", p)
          + el("WriteMode", "RecorderSubordinate" if subordinate else "Independent", p)
          + el("MainFilterOnPeriod", "false", p) + el("IncludeHelpInContents", "false", p)
          + el("DataLockControlMode", "Managed", p) + el("FullTextSearch", "DontUse", p)
          + el("EnableTotalsSliceFirst", "false", p) + el("EnableTotalsSliceLast", "false", p)
          + el("RecordPresentation", None, p) + el("ExtendedRecordPresentation", None, p)
          + el("ListPresentation", None, p) + el("ExtendedListPresentation", None, p) + el("Explanation", None, p)
          + el("DataHistory", "DontUse", p) + el("UpdateDataHistoryImmediatelyAfterWrite", "false", p)
          + el("ExecuteAfterWriteDataHistoryVersionProcessing", "false", p))
    s += "\t\t</Properties>\n\t\t<ChildObjects>\n"
    kinds = {"Ресурс": ("Resource", "register_res"), "Реквизит": ("Attribute", "register_attr"),
             "Измерение": ("Dimension", "register_dim")}
    for vid in ("Ресурс", "Реквизит", "Измерение"):  # порядок как в выгрузке Конфигуратора
        tag, kind = kinds[vid]
        for r in o["rows"]:
            if r["Вид"] == vid:
                if vid != "Реквизит" and "ХранилищеЗначения" in r["Тип"]:
                    raise ValueError(f"{md}.{r['Имя']}: ХранилищеЗначения допустимо только в реквизитах регистра")
                link_prefix = md + ".Dimension"
                s += attribute_xml(tag, r, md, kind, 3, link_prefix)
    s += "\t\t</ChildObjects>\n"
    return wrap("InformationRegister", md, s)


MODULE_FLAGS = {"С": "Server", "ВС": "ServerCall", "К": "ClientManagedApplication", "ВН": "ExternalConnection",
                "П": "Privileged"}


def gen_common_module(row):
    name = row["Модуль"]
    md = f"CommonModule.{name}"
    flags = {f.strip() for f in row["Контекст"].split(",")}
    if "ВС" in flags:
        flags.add("С")
    p = 3
    s = "\t\t<Properties>\n" + el("Name", name, p) + el_lstr("Synonym", synonym_from_name(name), p) + el("Comment", None, p)
    s += (el("Global", "false", p) + el("ClientManagedApplication", str("К" in flags).lower(), p)
          + el("Server", str("С" in flags).lower(), p) + el("ExternalConnection", str("ВН" in flags).lower(), p)
          + el("ClientOrdinaryApplication", "false", p) + el("ServerCall", str("ВС" in flags).lower(), p)
          + el("Privileged", str("П" in flags).lower(), p)
          + el("ReturnValuesReuse", "DuringSession" if "ПИ" in flags else "DontUse", p))
    s += "\t\t</Properties>\n"
    return wrap("CommonModule", md, s)


def gen_role(name):
    md = f"Role.{name}"
    s = "\t\t<Properties>\n" + el("Name", name, 3) + el_lstr("Synonym", synonym_from_name(name), 3) + el("Comment", None, 3)
    return wrap("Role", md, s + "\t\t</Properties>\n")


RIGHTS = {
    ("Catalog", "Ч"): ["Read", "View", "InputByString"],
    ("Catalog", "И"): ["Read", "Insert", "Update", "Delete", "View", "InteractiveInsert", "Edit",
                       "InteractiveSetDeletionMark", "InteractiveClearDeletionMark", "InputByString"],
    ("ChartOfCharacteristicTypes", "Ч"): ["Read", "View", "InputByString"],
    ("ChartOfCharacteristicTypes", "И"): ["Read", "Insert", "Update", "Delete", "View", "InteractiveInsert", "Edit",
                                          "InteractiveSetDeletionMark", "InteractiveClearDeletionMark", "InputByString"],
    ("InformationRegister", "Ч"): ["Read", "View"],
    ("InformationRegister", "И"): ["Read", "Update", "View", "Edit"],
    ("DataProcessor", "Ч"): ["Use", "View"],
    ("DataProcessor", "И"): ["Use", "View"],
    ("Document", "Ч"): ["Read", "View", "InputByString"],
    ("Document", "И"): ["Read", "Insert", "Update", "Delete", "View", "InteractiveInsert", "Edit",
                        "InteractiveSetDeletionMark", "InteractiveClearDeletionMark", "InputByString"],
    ("Document", "П"): ["Read", "Insert", "Update", "Delete", "Posting", "UndoPosting", "View", "InteractiveInsert",
                        "Edit", "InteractiveSetDeletionMark", "InteractiveClearDeletionMark", "InteractivePosting",
                        "InteractivePostingRegular", "InteractiveUndoPosting", "InteractiveChangeOfPosted",
                        "InputByString"],
}


def parse_role_groups(text):
    """Таблица групп прав из п. 11 → {группа: [md-имена]}."""
    kinds = {"справочник": "Catalog", "справочники": "Catalog", "ПВХ": "ChartOfCharacteristicTypes",
             "регистр": "InformationRegister", "регистры": "InformationRegister", "документ": "Document",
             "обработка": "DataProcessor", "обработки": "DataProcessor"}
    sec = text.split("## 11. Роли", 1)[1].split("\n## ", 1)[0]
    rows, _ = parse_table(sec.splitlines(), next(i for i, l in enumerate(sec.splitlines()) if l.startswith("| Группа")))
    groups = {}
    for r in rows:
        mds, kind = [], None
        for tok in re.findall(r"`[^`]+`|[А-Яа-яЁё]+", r["Объекты"]):
            if tok in kinds:
                kind = kinds[tok]
            elif tok.startswith("`"):
                mds.append(f"{kind}.{tok.strip('`')}")
        groups[r["Группа"]] = mds
    return groups


def gen_rights(role_row, groups):
    s = ('﻿<?xml version="1.0" encoding="UTF-8"?>\n<Rights xmlns="http://v8.1c.ru/8.2/roles" '
         'xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
         'xsi:type="Rights" version="2.20">\n\t<setForNewObjects>false</setForNewObjects>\n'
         '\t<setForAttributesByDefault>true</setForAttributesByDefault>\n'
         '\t<independentRightsOfChildObjects>false</independentRightsOfChildObjects>\n')
    any_right = False
    for group, mds in groups.items():
        level = role_row.get(group, "")
        if not level:
            continue
        for md in mds:
            kind = md.split(".")[0]
            rights = RIGHTS.get((kind, level)) or RIGHTS[(kind, "И")]
            any_right = True
            s += f"\t<object>\n\t\t<name>{md}</name>\n"
            for r in rights:
                s += f"\t\t<right>\n\t\t\t<name>{r}</name>\n\t\t\t<value>true</value>\n\t\t</right>\n"
            s += "\t</object>\n"
    if any_right:
        s += (f"\t<object>\n\t\t<name>Subsystem.{SUBSYSTEM}</name>\n\t\t<right>\n\t\t\t<name>View</name>\n"
              "\t\t\t<value>true</value>\n\t\t</right>\n\t</object>\n")
    return s + "</Rights>\n"


def gen_scheduled_job(row):
    name = row["Задание"]
    md = f"ScheduledJob.{name}"
    p = 3
    s = "\t\t<Properties>\n" + el("Name", name, p) + el_lstr("Synonym", synonym_from_name(name), p) + el("Comment", None, p)
    s += (el("MethodName", f"CommonModule.кбп_РегламентныеЗадания.{row['Метод модуля кбп_РегламентныеЗадания']}", p)
          + el("Description", escape(row["Назначение"]), p) + el("Key", None, p) + el("Use", "false", p)
          + el("Predefined", "true", p) + el("RestartCountOnFailure", "3", p) + el("RestartIntervalOnFailure", "60", p))
    return wrap("ScheduledJob", md, s + "\t\t</Properties>\n")


def gen_subsystem(o, content):
    md = f"Subsystem.{o['name']}"
    p = 3
    s = "\t\t<Properties>\n" + el("Name", o["name"], p) + el_lstr("Synonym", o["synonym"], p) + el("Comment", None, p)
    s += (el("IncludeHelpInContents", "true", p) + el("IncludeInCommandInterface", "true", p)
          + el("UseOneCommand", "false", p) + el("Explanation", None, p) + el("Picture", None, p))
    s += "\t\t\t<Content>\n" + "".join(f'\t\t\t\t<xr:Item xsi:type="xr:MDObjectRef">{c}</xr:Item>\n' for c in content)
    s += "\t\t\t</Content>\n\t\t</Properties>\n\t\t<ChildObjects/>\n"
    return wrap("Subsystem", md, s)


def gen_adopted_users():
    md = "Catalog.Пользователи"
    s = generated_types(md, [("CatalogObject", "Object"), ("CatalogRef", "Ref"), ("CatalogSelection", "Selection"),
                             ("CatalogList", "List"), ("CatalogManager", "Manager")], 2)
    s += ("\t\t<Properties>\n" + el("ObjectBelonging", "Adopted", 3) + el("Name", "Пользователи", 3) + el("Comment", None, 3)
          + el("ExtendedConfigurationObject", USERS_BASE_UUID[0], 3) + "\t\t</Properties>\n\t\t<ChildObjects/>\n")
    return wrap("Catalog", md, s)


def gen_language():
    md = "Language.Русский"
    s = ("\t\t<InternalInfo/>\n\t\t<Properties>\n" + el("ObjectBelonging", "Adopted", 3) + el("Name", "Русский", 3)
         + el("Comment", None, 3) + el("LanguageCode", "ru", 3) + "\t\t</Properties>\n")
    return wrap("Language", md, s)


CONTAINED_CLASS_IDS = [
    "9cd510cd-abfc-11d4-9434-004095e12fc7", "9fcd25a0-4822-11d4-9414-008048da11f9",
    "e3687481-0a87-462c-a166-9f34594f9bba", "9de14907-ec23-4a07-96f0-85521cb6b53b",
    "51f2d5d8-ea4d-4064-8892-82951750031e", "e68182ea-4237-4383-967f-90c1e3370bc7",
    "fb282519-d103-4dd3-bc12-cb271d631dfc",
]
CHILD_ORDER = ["Language", "Subsystem", "Role", "CommonModule", "ScheduledJob", "Catalog", "Document", "Enum",
               "InformationRegister", "ChartOfCharacteristicTypes"]


def gen_configuration(children, compat):
    md = f"Configuration.{EXT_NAME}"
    s = "\t\t<InternalInfo>\n"
    for cid in CONTAINED_CLASS_IDS:
        s += (f"\t\t\t<xr:ContainedObject>\n\t\t\t\t<xr:ClassId>{cid}</xr:ClassId>\n"
              f"\t\t\t\t<xr:ObjectId>{uid(md, cid)}</xr:ObjectId>\n\t\t\t</xr:ContainedObject>\n")
    s += "\t\t</InternalInfo>\n\t\t<Properties>\n"
    p = 3
    s += (el("ObjectBelonging", "Adopted", p) + el("Name", EXT_NAME, p) + el_lstr("Synonym", EXT_SYNONYM, p)
          + el("Comment", None, p) + el("ConfigurationExtensionPurpose", "AddOn", p)
          + el("KeepMappingToExtendedConfigurationObjectsByIDs", "false", p) + el("NamePrefix", PREFIX, p)
          + el("ConfigurationExtensionCompatibilityMode", compat, p) + el("DefaultRunMode", "ManagedApplication", p)
          + '\t\t\t<UsePurposes>\n\t\t\t\t<v8:Value xsi:type="app:ApplicationUsePurpose">PlatformApplication</v8:Value>\n\t\t\t</UsePurposes>\n'
          + el("ScriptVariant", "Russian", p)
          + f'\t\t\t<DefaultRoles>\n\t\t\t\t<xr:Item xsi:type="xr:MDObjectRef">Role.{MAIN_ROLE}</xr:Item>\n\t\t\t</DefaultRoles>\n'
          + el("Vendor", None, p) + el("Version", "0.1.0", p) + el("DefaultLanguage", "Language.Русский", p)
          + el("BriefInformation", None, p) + el("DetailedInformation", None, p) + el("Copyright", None, p)
          + el("VendorInformationAddress", None, p) + el("ConfigurationInformationAddress", None, p))
    s += "\t\t</Properties>\n\t\t<ChildObjects>\n"
    for kind in CHILD_ORDER:
        for name in children.get(kind, []):
            s += f"\t\t\t<{kind}>{name}</{kind}>\n"
    s += "\t\t</ChildObjects>\n"
    return wrap("Configuration", md, s)


# ---------------------------------------------------------------- заготовки модулей

MODULE_STUBS = {
    "кбп_ПроцессыAPI": [
        ("Функция", "ЗапуститьПроцесс(Схема, Предмет = Неопределено, Переменные = Неопределено, Родитель = Неопределено)"),
        ("Функция", "ВыполнитьДействие(Задача, ИдКнопки, Комментарий = \"\", ЗначенияПолей = Неопределено)"),
        ("Функция", "ВернутьНаДоработку(Задача, ИдШагаВозврата, Комментарий)"),
        ("Процедура", "Переадресовать(Задача, НовыйИсполнитель, Комментарий)"),
        ("Процедура", "ДобавитьКомментарий(Процесс, Текст, Задача = Неопределено, Файлы = Неопределено)"),
        ("Процедура", "Прервать(Процесс, Комментарий)"),
        ("Процедура", "Приостановить(Процесс, Комментарий = \"\")"),
        ("Процедура", "Продолжить(Процесс, Комментарий = \"\")"),
        ("Функция", "АктивныеПроцессыПредмета(Предмет)"),
        ("Функция", "ЗадачиПользователя(Пользователь, Отбор = Неопределено)"),
        ("Функция", "СостояниеПроцесса(Процесс)"),
    ],
    "кбп_АдаптерКонфигурации": [
        ("Функция", "ПодсистемаСуществует(ПолноеИмяПодсистемы)"),
        ("Процедура", "ОтправитьПочту(Письмо)"),
        ("Функция", "РуководительПользователя(Пользователь)"),
        ("Функция", "ПроизводственныйКалендарь()"),
        ("Функция", "ДобавитьРабочиеЧасы(Дата, Часы)"),
        ("Функция", "ТипыОбъектовДляПроцессов()"),
        ("Функция", "ПредставлениеОбъекта(Ссылка)"),
    ],
    "кбп_ПроцессыПереопределяемый": [
        ("Процедура", "ПриРегистрацииОбработчиков(Обработчики)"),
        ("Процедура", "ПриРегистрацииКаналов(Каналы)"),
        ("Процедура", "ПриОпределенииИсполнителей(Контекст, Исполнители, СтандартнаяОбработка)"),
        ("Процедура", "ПередЗапускомПроцесса(Схема, Предмет, Переменные, Отказ)"),
        ("Процедура", "ПриЗавершенииПроцесса(Процесс)"),
        ("Процедура", "ПриФормированииПанелиПроцесса(Форма, Предмет, Панель)"),
    ],
    "кбп_РегламентныеЗадания": [
        ("Процедура", "ОбработкаОчередиОповещений()"),
        ("Процедура", "ОбработкаОчередиДействий()"),
        ("Процедура", "КонтрольСроков()"),
        ("Процедура", "РассылкиПоРасписанию()"),
        ("Процедура", "ОчисткаЖурнала()"),
    ],
}

SPECIAL_BODIES = {
    "кбп_Лицензирование": '''#Область ПрограммныйИнтерфейс

// Проверяет, доступно ли действие по лицензии (Архитектура п. 10.1).
// В MVP всегда Истина; защита подключается заменой реализации (этап 7).
//
// Параметры:
//  Вид - Строка - "ЗапускПроцесса", "ПубликацияСхемы", "ОткрытиеКонструктора".
//
// Возвращаемое значение:
//  Булево
//
Функция ДоступноДействие(Вид) Экспорт
	Возврат Истина;
КонецФункции

#КонецОбласти
''',
}

ADAPTER_PRODUCT = '''// Возвращает код продукта базовой конфигурации: "ERP", "КА", "УТ", "УНФ", "БП", "УХ" или "Другое".
//
// Возвращаемое значение:
//  Строка
//
Функция ТекущийПродукт() Экспорт

	Имя = Метаданные.Имя;
	Если СтрНачинаетсяС(Имя, "УправлениеПредприятием") Тогда
		Возврат "ERP";
	ИначеЕсли СтрНачинаетсяС(Имя, "КомплекснаяАвтоматизация") Тогда
		Возврат "КА";
	ИначеЕсли СтрНачинаетсяС(Имя, "УправлениеТорговлей") Тогда
		Возврат "УТ";
	ИначеЕсли СтрНачинаетсяС(Имя, "УправлениеНебольшойФирмой") Тогда
		Возврат "УНФ";
	ИначеЕсли СтрНачинаетсяС(Имя, "Бухгалтерия") Тогда
		Возврат "БП";
	ИначеЕсли СтрНачинаетсяС(Имя, "УправлениеХолдингом") Тогда
		Возврат "УХ";
	КонецЕсли;
	Возврат "Другое";

КонецФункции

'''


def module_text(name):
    if name in SPECIAL_BODIES:
        return SPECIAL_BODIES[name]
    stubs = MODULE_STUBS.get(name, [])
    region = "ПрограммныйИнтерфейс" if stubs or name == "кбп_АдаптерКонфигурации" else "СлужебныеПроцедурыИФункции"
    out = f"#Область {region}\n\n"
    if name == "кбп_АдаптерКонфигурации":
        out += ADAPTER_PRODUCT
    for kind, sig in stubs:
        end = "КонецФункции" if kind == "Функция" else "КонецПроцедуры"
        if name == "кбп_ПроцессыПереопределяемый":
            body = "\t// Переопределяется расширением внедрения (&После).\n"
        else:
            body = '\tВызватьИсключение НСтр("ru = \'Не реализовано\'");\n'
        out += f"{kind} {sig} Экспорт\n{body}{end}\n\n"
    out += "#КонецОбласти\n"
    return out


# ---------------------------------------------------------------- сборка

def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(ROOT / "build" / "cfe"))
    ap.add_argument("--compat", default="Version8_3_24")
    ap.add_argument("--users-uuid", default=USERS_BASE_UUID[0],
                    help="UUID справочника Пользователи в базе, куда загружается выгрузка")
    ap.add_argument("--adopted", help="каталог выгрузки с заимствованным Catalogs/Пользователи.xml")
    ap.add_argument("--force-modules", action="store_true", help="перезаписать Ext/ (модули, права)")
    args = ap.parse_args()
    out = Path(args.out)
    USERS_BASE_UUID[0] = args.users_uuid
    LINE_NUMBER_LENGTH[0] = "9" if compat_version(args.compat) >= (8, 3, 27) else "5"

    text = SPEC.read_text(encoding="utf-8")
    objects = parse_spec(SPEC)
    children = {k: [] for k in CHILD_ORDER}
    names = set()
    files = {}

    def add(kind, name, rel, content):
        if (kind, name) in names:
            raise ValueError(f"Дубль объекта {kind}.{name}")
        names.add((kind, name))
        children[kind].append(name)
        files[rel] = content

    ext_files = {}
    add("Language", "Русский", "Languages/Русский.xml", gen_language())
    if args.adopted:
        src = Path(args.adopted) / "Catalogs" / "Пользователи.xml"
        add("Catalog", "Пользователи", "Catalogs/Пользователи.xml", "\ufeff" + src.read_text(encoding="utf-8-sig"))
    else:
        add("Catalog", "Пользователи", "Catalogs/Пользователи.xml", gen_adopted_users())

    subsystem = None
    role_rows = []
    for o in objects:
        k, n = o["kind"], o["name"]
        if k == "Enum":
            add(k, n, f"Enums/{n}.xml", gen_enum(o))
        elif k == "Catalog":
            add(k, n, f"Catalogs/{n}.xml", gen_catalog(o))
        elif k == "ChartOfCharacteristicTypes":
            add(k, n, f"ChartsOfCharacteristicTypes/{n}.xml", gen_ccht(o))
        elif k == "Document":
            add(k, n, f"Documents/{n}.xml", gen_document(o))
        elif k == "InformationRegister":
            add(k, n, f"InformationRegisters/{n}.xml", gen_register(o))
        elif k == "CommonModule":
            for r in o["rows"]:
                m = r["Модуль"]
                add(k, m, f"CommonModules/{m}.xml", gen_common_module(r))
                ext_files[f"CommonModules/{m}/Ext/Module.bsl"] = module_text(m)
        elif k == "Role":
            role_rows = o["rows"]
        elif k == "ScheduledJob":
            for r in o["rows"]:
                add(k, r["Задание"], f"ScheduledJobs/{r['Задание']}.xml", gen_scheduled_job(r))
        elif k == "Subsystem":
            subsystem = o

    groups = parse_role_groups(text)
    for r in role_rows:
        add("Role", r["Роль"], f"Roles/{r['Роль']}.xml", gen_role(r["Роль"]))
        ext_files[f"Roles/{r['Роль']}/Ext/Rights.xml"] = gen_rights(r, groups)

    if subsystem:
        content = [f"Catalog.{c}" for c in ("кбп_Задачи", "кбп_Процессы", "кбп_СхемыПроцессов", "кбп_РолиИсполнителей",
                                            "кбп_ШаблоныСообщений")] + ["Document.кбп_Замещение"]
        content.insert(2, "DataProcessor.кбп_КонструкторСхем")
        add("Subsystem", subsystem["name"], f"Subsystems/{subsystem['name']}.xml", gen_subsystem(subsystem, content))

    check_references(files, names)
    files["Configuration.xml"] = gen_configuration(children, args.compat)

    for rel, content in files.items():
        write(out / rel, content)
    skipped = 0
    for rel, content in ext_files.items():
        p = out / rel
        if p.exists() and not args.force_modules:
            skipped += 1
            continue
        write(p, content)
    stale = out / "ConfigDumpInfo.xml"
    if stale.exists():
        stale.unlink()  # сведения о выгрузке устарели — Конфигуратор пересоздаст при следующей выгрузке

    counts = {k: len(v) for k, v in children.items() if v}
    print(f"Сгенерировано в {out}: " + ", ".join(f"{k} {v}" for k, v in counts.items()))
    if skipped:
        print(f"Не перезаписано файлов Ext/ (уже есть): {skipped}; ключ --force-modules перезапишет")


def check_references(files, names):
    """Каждая ссылка cfg:XxxRef.Имя / MDObjectRef должна указывать на объект расширения."""
    kind_of = {"CatalogRef": "Catalog", "DocumentRef": "Document", "EnumRef": "Enum",
               "ChartOfCharacteristicTypesRef": "ChartOfCharacteristicTypes",
               "Characteristic": "ChartOfCharacteristicTypes"}
    errors = set()
    for rel, content in files.items():
        for kind, name in re.findall(r"cfg:(\w+)\.([^<\s]+)<", content):
            if (kind_of.get(kind), name) not in names:
                errors.add(f"{rel}: нет объекта для типа {kind}.{name}")
        for kind, name in re.findall(r'MDObjectRef">(\w+)\.([^<]+)<', content):
            # обработки создаются вне генератора (src/cfe), на них можно ссылаться
            if (kind, name) not in names and kind not in ("Role", "DataProcessor"):
                errors.add(f"{rel}: нет объекта {kind}.{name}")
    if errors:
        sys.exit("Ошибки ссылок:\n" + "\n".join(sorted(errors)))


if __name__ == "__main__":
    main()
