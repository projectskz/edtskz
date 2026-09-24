"""Статическая проверка BSL-модулей расширения (без платформы).
python3 bslcheck.py <src/cfe>
"""
import re, sys, glob, os, collections
import xml.etree.ElementTree as ET

ROOT = sys.argv[1]
ID = r"[A-Za-zА-Яа-яЁё_][A-Za-zА-Яа-яЁё_0-9]*"

def strip(text):
    """Убирает комментарии и содержимое строк (строки → "")."""
    out = []
    in_str = False
    for line in text.split("\n"):
        s = line
        res = ""
        i = 0
        # продолжение строкового литерала: строка начинается с |
        if in_str:
            m = re.match(r"\s*\|", s)
            if m:
                i = m.end()
            else:
                in_str = False
        while i < len(s):
            c = s[i]
            if in_str:
                if c == '"':
                    if i + 1 < len(s) and s[i + 1] == '"':
                        i += 2
                        continue
                    in_str = False
                    res += '"'
                i += 1
                continue
            if c == '"':
                in_str = True
                res += '"'
                i += 1
                continue
            if s.startswith("//", i):
                break
            res += c
            i += 1
        if in_str:
            res += '"'  # закрываем для анализа строки
        out.append(res)
    return out

GLOBAL = set("""
НСтр СтрШаблон СтрСоединить СтрРазделить СтрЗаменить СтрНайти СтрДлина СтрНачинаетсяС Лев Прав Сред СокрЛП СокрЛ СокрП НРег ВРег
ЗначениеЗаполнено ТипЗнч Тип Строка Число Дата Булево Формат XMLСтрока ТекущаяДатаСеанса ТекущаяДата Цел Окр Pow Мин Макс
ВызватьИсключение ЗаполнитьЗначенияСвойств НачатьТранзакцию ЗафиксироватьТранзакцию ОтменитьТранзакцию ТранзакцияАктивна
УстановитьПривилегированныйРежим ПривилегированныйРежим РольДоступна ПравоДоступа ЗаписьЖурналаРегистрации ИнформацияОбОшибке
ПолучитьНавигационнуюСсылку ПолучитьНавигационнуюСсылкуИнформационнойБазы ДеньНедели Выполнить Вычислить ПустаяСтрока
ПоказатьВопрос ПоказатьПредупреждение ПоказатьОповещениеПользователя ПоказатьЗначение ОткрытьФорму Оповестить ПоказатьВводСтроки
ПоказатьВыборИзСписка ПодключитьОбработчикОжидания ОтключитьОбработчикОжидания ЗначениеВРеквизитФормы РеквизитФормыВЗначение
Закрыть Символ КодСимвола ЗначениеВСтрокуВнутр НайтиПоТипу
""".split())
KEYWORDS = set("Если Тогда ИначеЕсли Иначе КонецЕсли Для Каждого Из По Цикл КонецЦикла Пока Попытка Исключение КонецПопытки "
               "Возврат Продолжить Прервать Новый И ИЛИ Или НЕ Не Истина Ложь Неопределено Null Процедура Функция "
               "КонецПроцедуры КонецФункции Экспорт Знач Перем".split())

def procs(lines):
    res = {}
    for i, l in enumerate(lines):
        m = re.match(rf"\s*(Процедура|Функция)\s+({ID})\s*\((.*)\)\s*(Экспорт)?", l)
        if m:
            res[m.group(2)] = dict(line=i + 1, kind=m.group(1), export=bool(m.group(4)), params=m.group(3))
    return res

def balance(path, lines):
    stack = []
    errs = []
    pairs = {"КонецЕсли": "Если", "КонецЦикла": "Цикл", "КонецПопытки": "Попытка", "КонецПроцедуры": "Процедура",
             "КонецФункции": "Функция"}
    for i, l in enumerate(lines, 1):
        s = re.sub(r'"[^"]*"', '""', l)
        t = s.strip()
        if t.startswith("#Область"):
            stack.append(("#Область", i)); continue
        if t.startswith("#КонецОбласти"):
            if not stack or stack[-1][0] != "#Область": errs.append(f"{i}: #КонецОбласти без #Область")
            else: stack.pop()
            continue
        if t.startswith("#Если"):
            stack.append(("#Если", i)); continue
        if t.startswith("#КонецЕсли"):
            if not stack or stack[-1][0] != "#Если": errs.append(f"{i}: #КонецЕсли")
            else: stack.pop()
            continue
        if t.startswith("#"):
            continue
        for w in re.findall(ID, s):
            if w in ("Если", "Попытка", "Процедура", "Функция"):
                if w == "Если" and re.search(r"\?\s*\(", s) and "Тогда" not in s:
                    continue
                stack.append((w, i))
            elif w == "Цикл":
                stack.append(("Цикл", i))
            elif w in pairs:
                if not stack or stack[-1][0] != pairs[w]:
                    errs.append(f"{i}: {w} не парный (стек: {stack[-1] if stack else None})")
                else:
                    stack.pop()
    if stack:
        errs.append(f"не закрыто: {stack}")
    return errs

modules = {}
for f in glob.glob(os.path.join(ROOT, "CommonModules/*/Ext/Module.bsl")):
    name = f.split(os.sep)[-3]
    text = open(f, encoding="utf-8-sig").read().replace("\r\n", "\n")
    modules[name] = (f, strip(text), text)
forms = {}
for f in glob.glob(os.path.join(ROOT, "**/Forms/*/Ext/Form/Module.bsl"), recursive=True):
    text = open(f, encoding="utf-8-sig").read().replace("\r\n", "\n")
    forms[f] = (f, strip(text), text)

exports = {m: {p for p, d in procs(v[1]).items() if d["export"]} for m, v in modules.items()}
unknown_global = collections.Counter()
problems = 0

def check(path, lines, raw, is_form):
    global problems
    local = procs(lines)
    for e in balance(path, lines):
        print(path, "БЛОКИ", e); problems += 1
    for i, l in enumerate(lines, 1):
        if re.search(rf"Новый\s+{ID}\s*(\([^()]*\))?\s*[.\[]", l):
            print(path, i, "обращение после Новый:", l.strip()); problems += 1
        m = re.match(rf"\s*({ID})\s*=", l)
        if m and m.group(1) in (set(modules) | {"Строка", "Тип", "Пользователи", "ОбщегоНазначения", "Число", "Дата",
                                               "Элементы", "Команды", "Параметры", "Метаданные", "Справочники"}):
            print(path, i, "присваивание имени модуля/функции:", l.strip()); problems += 1
        for mm in re.finditer(rf"(?<![.\w])({ID})\.({ID})\s*\(", l):
            mod, meth = mm.group(1), mm.group(2)
            if mod in modules and meth not in exports[mod]:
                print(path, i, f"{mod}.{meth} не экспортирован/не существует"); problems += 1
        for mm in re.finditer(rf"(?<![.\w&])({ID})\s*\(", l):
            n = mm.group(1)
            if n in KEYWORDS or n in local or n in GLOBAL:
                continue
            unknown_global[n] += 1
        # ОписаниеОповещения / ПодключитьОбработчикОжидания
        for mm in re.finditer(r'ОписаниеОповещения\("([^"]+)"', raw.split("\n")[i - 1]):
            n = mm.group(1)
            if n not in local or not local[n]["export"]:
                print(path, i, f"обработчик оповещения {n} не найден или не Экспорт"); problems += 1
        for mm in re.finditer(r'ПодключитьОбработчикОжидания\("([^"]+)"', raw.split("\n")[i - 1]):
            if mm.group(1) not in local:
                print(path, i, f"обработчик ожидания {mm.group(1)} не найден"); problems += 1
    # параметры, совпадающие с именами процедур модуля
    for p, d in local.items():
        for prm in re.findall(ID, d["params"]):
            if prm in local and prm not in ("Знач",):
                print(path, d["line"], f"параметр {prm} совпадает с именем процедуры"); problems += 1
    if is_form:
        check_form(path, raw, local)

def check_form(path, raw, local):
    global problems
    fx = path.replace("/Form/Module.bsl", "/Form.xml")
    r = ET.parse(fx).getroot()
    names = set()
    for el in r.iter():
        if "name" in el.attrib:
            names.add(el.attrib["name"])
        t = el.tag.split("}")[1]
        if t == "Event" and el.text and el.text not in local:
            print(path, f"обработчик события {el.text} не найден"); problems += 1
        if t == "Action" and el.text not in local:
            print(path, f"действие команды {el.text} не найдено"); problems += 1
    for mm in re.finditer(rf"Элементы\.({ID})", raw):
        n = mm.group(1)
        if n not in names and n not in ("Добавить", "Удалить", "Найти", "Переместить"):
            print(path, f"элемент {n} не найден в форме"); problems += 1
    attrs = {a.attrib["name"] for a in r.iter() if a.tag.endswith("}Attribute")}
    # директивы: у каждой процедуры формы должна быть директива
    lines = raw.split("\n")
    for p, d in local.items():
        prev = lines[d["line"] - 2].strip() if d["line"] >= 2 else ""
        if not prev.startswith("&"):
            print(path, d["line"], f"у {p} нет директивы компиляции"); problems += 1

for m, (f, lines, raw) in modules.items():
    check(m, lines, raw, False)
for f, (ff, lines, raw) in forms.items():
    check(f, lines, raw, True)
print("Неизвестные вызовы (проверить глазами):", ", ".join(f"{k}" for k, v in sorted(unknown_global.items())))
print("проблем:", problems)

# --- число аргументов при вызовах методов наших общих модулей и локальных процедур ---
def sig_all(text):
    res = {}
    for m in re.finditer(rf"(Процедура|Функция)\s+({ID})\s*\(([^)]*)\)", text):
        params = [p.strip() for p in m.group(3).replace("\n", " ").split(",") if p.strip()]
        req = sum(1 for p in params if "=" not in p)
        res[m.group(2)] = (req, len(params))
    return res

def args_count(s, start):
    depth = 0; n = 0; i = start; empty = True
    while i < len(s):
        c = s[i]
        if c == '"':
            j = s.index('"', i + 1); i = j + 1; empty = False; continue
        if c == "(":
            depth += 1
        elif c == ")":
            if depth == 0:
                return (0 if empty else n + 1)
            depth -= 1
        elif c == "," and depth == 0:
            n += 1
        elif not c.isspace():
            empty = False
        i += 1
    return None

sigs = {m: sig_all("\n".join(v[1])) for m, v in modules.items()}
bad2 = 0
for path, (f, lines, raw) in list(modules.items()) + [(k, v) for k, v in forms.items()]:
    text = "\n".join(lines)
    local = sig_all(text)
    for mm in re.finditer(rf"(?<![\w&])(?:({ID})\.)?({ID})\s*\(", text):
        mod, meth = mm.group(1), mm.group(2)
        table_ = sigs.get(mod) if mod else local
        if not table_ or meth not in table_:
            continue
        before = text[max(0, mm.start() - 12):mm.start()]
        if re.search(r"(Процедура|Функция)\s+$", before):
            continue
        n = args_count(text, mm.end())
        req, mx = table_[meth]
        if n is None:
            continue
        if n > mx or n < req:
            line = text[:mm.start()].count("\n") + 1
            print(path, line, f"{(mod + '.') if mod else ''}{meth}: аргументов {n}, ожидается {req}..{mx}")
            bad2 += 1
print("ошибок числа аргументов:", bad2)

# --- имена процедур, совпадающие с ключевыми словами ---
KW = set("Если Тогда ИначеЕсли Иначе КонецЕсли Для Каждого Из По Цикл КонецЦикла Пока Попытка Исключение КонецПопытки "
         "ВызватьИсключение Возврат Продолжить Прервать Перейти Новый И ИЛИ НЕ Истина Ложь Неопределено Процедура Функция "
         "Экспорт Знач Перем Выполнить ДобавитьОбработчик УдалитьОбработчик Асинх Ждать".split())
for path, (f, lines, raw) in list(modules.items()) + list(forms.items()):
    for m in re.finditer(rf"(?:Процедура|Функция)\s+({ID})", "\n".join(lines)):
        if m.group(1) in KW:
            print(path, "имя процедуры — ключевое слово:", m.group(1))
