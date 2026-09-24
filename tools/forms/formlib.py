"""Построитель XML управляемых форм и метаданных форм в формате выгрузки Конфигуратора (Hierarchical 2.20).

Порядок тегов внутри элементов взят из форм БСП (github.com/1c-syntax/ssl_3_1): свойства сериализуются
в каноническом порядке ORDER, поэтому порядок записи в описании формы не важен.
Файлы пишутся как у Конфигуратора: UTF-8 с BOM, CRLF.
"""
import uuid
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src" / "cfe"
NS = uuid.UUID("6f1c3a52-3d8e-4b6a-9d61-6b0f2d1c7a10")  # тот же, что в tools/gen/generate.py


def uid(*p):
    return str(uuid.uuid5(NS, "/".join(p)))


def write(rel, text):
    path = SRC / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    text = text.replace("\r\n", "\n").replace("\n", "\r\n")
    path.write_bytes(("﻿" + text.lstrip("﻿")).encode("utf-8"))


def lstr(text, ind):
    t = "\t" * ind
    return f"{t}<v8:item>\n{t}\t<v8:lang>ru</v8:lang>\n{t}\t<v8:content>{escape(text)}</v8:content>\n{t}</v8:item>\n"


# Канонический порядок дочерних тегов (из форм БСП).
ORDER = {
    "Form": "Title Width Height WindowOpeningMode AutoSaveDataInSettings EnterKeyBehavior SaveDataInSettings "
            "SaveWindowSettings AutoTitle AutoURL Group AutoFillCheck Customizable Enabled VerticalAlign VerticalSpacing "
            "CommandBarLocation ShowTitle VerticalScroll ConversationsRepresentation MobileDeviceCommandBarContent "
            "CommandSet ReportResult DetailsData ReportFormType ShowCloseButton UseForFoldersAndItems VariantAppearance "
            "AutoShowState CustomSettingsFolder ReportResultViewMode ViewModeApplicationOnSetReportResult AutoCommandBar "
            "Events ChildItems Attributes Commands Parameters CommandInterface",
    "InputField": "DataPath DefaultItem Visible Enabled UserVisible ReadOnly SkipOnInput Title TitleBackColor TitleFont "
                  "TitleTextColor TitleLocation GroupVerticalAlign Shortcut TitleHeight ToolTip ToolTipRepresentation "
                  "HorizontalAlign GroupHorizontalAlign VerticalAlign WarningOnEditRepresentation WarningOnEdit EditMode "
                  "CellHyperlink AutoCellHeight FooterHorizontalAlign HeaderHorizontalAlign HeaderPicture ShowInHeader "
                  "ShowInFooter Width AutoMaxWidth MaxWidth Height AutoMaxHeight MaxHeight HorizontalStretch "
                  "VerticalStretch Wrap DropListButton MultiLine PasswordMode ExtendedEdit ChoiceButton "
                  "ChoiceButtonRepresentation ClearButton Mask SpinButton OpenButton ChoiceForm CreateButton "
                  "ListChoiceMode AutoChoiceIncomplete ExtendedEditMultipleValues Format EditFormat QuickChoice "
                  "ChoiceFoldersAndItems AutoMarkIncomplete ChooseType AutoShowOpenButtonMode IncompleteChoiceMode "
                  "SpellCheckingOnTextInput TypeDomainEnabled AvailableTypes MinValue MaxValue TextEdit ChoiceListButton "
                  "ChoiceParameterLinks ChoiceParameters EditTextUpdate ChoiceButtonPicture ChoiceList "
                  "AutoCorrectionOnTextInput ChoiceListHeight DropListWidth BackColor TextColor BorderColor "
                  "HeightControlVariant InputHint ChoiceHistoryOnInput TypeLink ContextMenu ExtendedTooltip Events",
    "CheckBoxField": "DataPath Visible Enabled UserVisible ReadOnly SkipOnInput Title TitleTextColor TitleLocation "
                     "HorizontalAlign TitleHeight ToolTip FooterHorizontalAlign ToolTipRepresentation EditMode "
                     "GroupHorizontalAlign GroupVerticalAlign ShowInHeader HeaderPicture HeaderHorizontalAlign "
                     "ShowInFooter ThreeState VerticalAlign CheckBoxType ContextMenu ExtendedTooltip Events",
    "LabelField": "DataPath Visible UserVisible DefaultItem ReadOnly SkipOnInput Title TitleBackColor TitleFont "
                  "TitleTextColor TitleLocation ToolTip HorizontalAlign ToolTipRepresentation VerticalAlign EditMode "
                  "FixingInTable CellHyperlink AutoCellHeight FooterHorizontalAlign GroupHorizontalAlign "
                  "GroupVerticalAlign ShowInHeader ShowInFooter Width AutoMaxWidth MaxWidth Height AutoMaxHeight "
                  "HorizontalStretch Format MaxHeight VerticalStretch Border BackColor Hiperlink TextColor Font "
                  "ContextMenu ExtendedTooltip Events",
    "LabelDecoration": "Enabled Visible Width AutoMaxWidth MaxWidth Height AutoMaxHeight MaxHeight HorizontalStretch "
                       "VerticalStretch SkipOnInput TextColor Font Title ToolTip ToolTipRepresentation "
                       "GroupHorizontalAlign GroupVerticalAlign Hyperlink HorizontalAlign VerticalAlign BackColor "
                       "Border TitleHeight ContextMenu ExtendedTooltip Events",
    "UsualGroup": "UserVisible ReadOnly Visible Enabled EnableContentChange Title Shortcut TitleTextColor TitleFont "
                  "ToolTip ToolTipRepresentation Width Height HorizontalStretch VerticalStretch GroupHorizontalAlign "
                  "GroupVerticalAlign Group ChildrenAlign HorizontalSpacing VerticalSpacing HorizontalAlign "
                  "VerticalAlign Behavior CollapsedRepresentationTitle Collapsed ControlRepresentation Representation "
                  "Format ShowLeftMargin United ChildItemsWidth ShowTitle BackColor ThroughAlign TitleDataPath "
                  "ExtendedTooltip ChildItems",
    "Pages": "EnableContentChange Enabled UserVisible Visible Title GroupVerticalAlign Height ToolTip "
             "ToolTipRepresentation Width HorizontalStretch VerticalStretch PagesRepresentation ExtendedTooltip "
             "Events ChildItems",
    "Page": "Visible Enabled ReadOnly EnableContentChange Title HorizontalAlign Shortcut TitleDataPath TitleTextColor "
            "ToolTip Picture ToolTipRepresentation VerticalSpacing Width HorizontalStretch VerticalStretch Group "
            "ChildItemsWidth VerticalAlign ShowTitle BackColor ExtendedTooltip ChildItems",
    "Table": "Representation TitleLocation CommandBarLocation UserVisible VerticalScrollBar Visible Autofill ReadOnly "
             "SkipOnInput DefaultItem ChangeRowSet ChangeRowOrder Width AutoMaxWidth Height MaxWidth AutoMaxHeight "
             "HeightControlVariant AutoMaxRowsCount HeightInTableRows ChoiceMode MultipleChoice RowInputMode "
             "SelectionMode RowSelectionMode Header FooterHeight HeaderHeight HorizontalScrollBar HorizontalLines "
             "VerticalLines UseAlternationRowColor AutoInsertNewRow AutoAddIncomplete AutoMarkIncomplete "
             "SearchOnInput InitialListView InitialTreeView HorizontalStretch Output VerticalStretch EnableStartDrag "
             "EnableDrag FileDragMode DataPath RowPictureDataPath RowsPicture BackColor BorderColor Title "
             "GroupVerticalAlign TitleTextColor CommandSet ToolTip ToolTipRepresentation SearchStringLocation "
             "ViewStatusLocation SearchControlLocation CurrentRowUse AutoRefresh AutoRefreshPeriod Period "
             "ChoiceFoldersAndItems RestoreCurrentRow RowFilter TopLevelParent ShowRoot AllowRootChoice "
             "UpdateOnDataChange UserSettingsGroup AllowGettingCurrentRowURL ViewMode "
             "SettingsNamedItemDetailedRepresentation ContextMenu AutoCommandBar ExtendedTooltip "
             "SearchStringAddition ViewStatusAddition SearchControlAddition Events ChildItems",
    "Button": "Type TitleHeight UserVisible Visible Representation DefaultButton SkipOnInput Enabled DefaultItem Width "
              "AutoMaxWidth HorizontalStretch GroupHorizontalAlign Check MaxWidth AutoMaxHeight Height MaxHeight "
              "VerticalStretch GroupVerticalAlign CommandName DataPath Font Picture TextColor BackColor BorderColor "
              "Title PictureLocation ToolTipRepresentation RepresentationInContextMenu LocationInCommandBar "
              "ShapeRepresentation ExtendedTooltip",
    "GraphicalSchemaField": "DataPath ReadOnly Title TitleLocation Width Height Edit ContextMenu ExtendedTooltip Events",
}
ORDER = {k: v.split() for k, v in ORDER.items()}

def T(i):
    return "\t" * i


LOCALIZED = {"Title", "ToolTip", "InputHint"}


class Ids:
    def __init__(self):
        self.n = 0

    def __call__(self):
        self.n += 1
        return self.n


def _val(tag, v, ind):
    t = "\t" * ind
    if tag in LOCALIZED:
        return f"{t}<{tag}>\n{lstr(v, ind + 1)}{t}</{tag}>\n"
    if isinstance(v, bool):
        v = "true" if v else "false"
    if isinstance(v, Raw):
        return v.text(ind)
    return f"{t}<{tag}>{v}</{tag}>\n"


class Raw:
    """Готовый XML свойства (с отступами относительно ind)."""

    def __init__(self, fn):
        self.fn = fn

    def text(self, ind):
        return self.fn(ind)


class El:
    def __init__(self, kind, name, children=None, events=None, **props):
        self.kind, self.name = kind, name
        self.children = children or []
        self.events = events or {}
        self.props = props

    def xml(self, ids, ind):
        t = "\t" * ind
        s = f'{t}<{self.kind} name="{self.name}" id="{ids()}">\n'
        parts = {key: v for key, v in self.props.items() if v is not None}
        k = self.kind
        if k in ("InputField", "CheckBoxField", "LabelField", "LabelDecoration", "GraphicalSchemaField"):
            parts["ContextMenu"] = Raw(lambda i: f'{T(i)}<ContextMenu name="{self.name}КонтекстноеМеню" id="{ids()}"/>\n')
        if k == "Table":
            parts["ContextMenu"] = Raw(lambda i: f'{T(i)}<ContextMenu name="{self.name}КонтекстноеМеню" id="{ids()}"/>\n')
            parts["AutoCommandBar"] = Raw(lambda i: self._table_bar(ids, i))
        parts["ExtendedTooltip"] = Raw(lambda i: f'{T(i)}<ExtendedTooltip name="{self.name}РасширеннаяПодсказка" id="{ids()}"/>\n')
        if k == "Table":
            for add, typ, tag in (("СтрокаПоиска", "SearchStringRepresentation", "SearchStringAddition"),
                                  ("СостояниеПросмотра", "ViewStatusRepresentation", "ViewStatusAddition"),
                                  ("УправлениеПоиском", "SearchControl", "SearchControlAddition")):
                parts[tag] = Raw(lambda i, add=add, typ=typ, tag=tag: (
                    f'{T(i)}<{tag} name="{self.name}{add}" id="{ids()}">\n'
                    f'{T(i)}\t<AdditionSource>\n{T(i)}\t\t<Item>{self.name}</Item>\n{T(i)}\t\t<Type>{typ}</Type>\n'
                    f'{T(i)}\t</AdditionSource>\n'
                    f'{T(i)}\t<ContextMenu name="{self.name}{add}КонтекстноеМеню" id="{ids()}"/>\n'
                    f'{T(i)}\t<ExtendedTooltip name="{self.name}{add}РасширеннаяПодсказка" id="{ids()}"/>\n'
                    f'{T(i)}</{tag}>\n'))
        if self.events:
            parts["Events"] = Raw(lambda i: f'{T(i)}<Events>\n' + "".join(
                f'{T(i)}\t<Event name="{e}">{h}</Event>\n' for e, h in self.events.items()) + f'{T(i)}</Events>\n')
        if self.children and k != "Table":
            parts["ChildItems"] = Raw(lambda i: f'{T(i)}<ChildItems>\n' + "".join(
                c.xml(ids, i + 1) for c in self.children) + f'{T(i)}</ChildItems>\n')
        if k == "Table" and self.children:
            parts["ChildItems"] = Raw(lambda i: f'{T(i)}<ChildItems>\n' + "".join(
                c.xml(ids, i + 1) for c in self.children) + f'{T(i)}</ChildItems>\n')
        order = ORDER[k]
        unknown = [p for p in parts if p not in order]
        if unknown:
            raise ValueError(f"{k} {self.name}: неизвестные свойства {unknown}")
        for tag in order:
            if tag in parts:
                s += _val(tag, parts[tag], ind + 1)
        return s + f"{t}</{self.kind}>\n"


# --- Конструкторы элементов -------------------------------------------------------------------------------------

def group(name, children, title=None, horizontal=False, show_title=False, representation="None", **kw):
    p = dict(Title=title or name, Group="Horizontal" if horizontal else "Vertical", Behavior="Usual",
             Representation=representation, ShowTitle=show_title)
    p.update(kw)
    return El("UsualGroup", name, children, **p)


def pages(name, children, events=None, **kw):
    return El("Pages", name, children, events, **kw)


def page(name, title, children, **kw):
    return El("Page", name, children, Title=title, **kw)


def field(name, path, title=None, events=None, **kw):
    p = dict(DataPath=path)
    if title is not None:
        p["Title"] = title
    p.update(kw)
    return El("InputField", name, events=events, **p)


def check(name, path, title=None, events=None, **kw):
    p = dict(DataPath=path, TitleLocation="Right", CheckBoxType="Auto")
    if title is not None:
        p["Title"] = title
    p.update(kw)
    return El("CheckBoxField", name, events=events, **p)


def label(name, path, title=None, events=None, **kw):
    p = dict(DataPath=path)
    if title is not None:
        p["Title"] = title
    p.update(kw)
    return El("LabelField", name, events=events, **p)


def deco(name, text, events=None, **kw):
    return El("LabelDecoration", name, events=events, Title=text, **kw)


def button(name, command, usual=True, **kw):
    cmd = command if "." in command else f"Form.Command.{command}"
    return El("Button", name, Type="UsualButton" if usual else "CommandBarButton", CommandName=cmd, **kw)


class TableEl(El):
    def __init__(self, name, path, columns, events=None, bar=None, **props):
        super().__init__("Table", name, columns, events, **props)
        self.props["DataPath"] = path
        self.bar = bar  # None — автозаполнение; список кнопок — без автозаполнения

    def _table_bar(self, ids, i):
        t = "\t" * i
        s = f'{t}<AutoCommandBar name="{self.name}КоманднаяПанель" id="{ids()}">\n'
        if self.bar is None:
            return s + f"{t}</AutoCommandBar>\n"
        s += f"{t}\t<Autofill>false</Autofill>\n"
        if self.bar:
            s += f"{t}\t<ChildItems>\n" + "".join(b.xml(ids, i + 2) for b in self.bar) + f"{t}\t</ChildItems>\n"
        return s + f"{t}</AutoCommandBar>\n"


def table(name, path, columns, events=None, bar=None, **kw):
    p = dict(Representation="List", RowFilter=Raw(lambda i: f'{T(i)}<RowFilter xsi:nil="true"/>\n'))
    p.update(kw)
    return TableEl(name, path, columns, events, bar, **p)


def schema_field(name, path, title, events=None, **kw):
    return El("GraphicalSchemaField", name, events=events, DataPath=path, Title=title, **kw)


# --- Типы -------------------------------------------------------------------------------------------------------

def t_str(length=0):
    return ("<v8:Type>xs:string</v8:Type>\n<v8:StringQualifiers>\n\t<v8:Length>%d</v8:Length>\n"
            "\t<v8:AllowedLength>Variable</v8:AllowedLength>\n</v8:StringQualifiers>\n" % length)


def t_num(digits, frac=0, nonneg=False):
    return ("<v8:Type>xs:decimal</v8:Type>\n<v8:NumberQualifiers>\n\t<v8:Digits>%d</v8:Digits>\n"
            "\t<v8:FractionDigits>%d</v8:FractionDigits>\n\t<v8:AllowedSign>%s</v8:AllowedSign>\n"
            "</v8:NumberQualifiers>\n" % (digits, frac, "Nonnegative" if nonneg else "Any"))


T_BOOL = "<v8:Type>xs:boolean</v8:Type>\n"
T_DATETIME = "<v8:Type>xs:dateTime</v8:Type>\n<v8:DateQualifiers>\n\t<v8:DateFractions>DateTime</v8:DateFractions>\n</v8:DateQualifiers>\n"
T_ANYREF = "<v8:TypeSet>cfg:AnyIBRef</v8:TypeSet>\n"
T_VT = "<v8:Type>v8:ValueTable</v8:Type>\n"
T_VL = "<v8:Type>v8:ValueListType</v8:Type>\n"
T_GRAPH = '<v8:Type xmlns:d5p1="http://v8.1c.ru/8.2/data/graphscheme">d5p1:FlowchartContextType</v8:Type>\n'


def t_cfg(name):
    return f"<v8:Type>cfg:{name}</v8:Type>\n"


def _indent(text, ind):
    t = "\t" * ind
    return "".join(t + line + "\n" for line in text.rstrip("\n").split("\n"))


class Attr:
    def __init__(self, name, type_xml, title=None, main=False, saved=False, columns=None):
        self.name, self.type_xml, self.title, self.main, self.saved = name, type_xml, title, main, saved
        self.columns = columns or []  # [(имя, тип, заголовок)]

    def xml(self, aid):
        s = f'\t\t<Attribute name="{self.name}" id="{aid}">\n'
        if self.title:
            s += f"\t\t\t<Title>\n{lstr(self.title, 4)}\t\t\t</Title>\n"
        s += "\t\t\t<Type>\n" + _indent(self.type_xml, 4) + "\t\t\t</Type>\n"
        if self.main:
            s += "\t\t\t<MainAttribute>true</MainAttribute>\n"
        if self.saved:
            s += "\t\t\t<SavedData>true</SavedData>\n"
        if self.columns:
            s += "\t\t\t<Columns>\n"
            for i, (c, tx, cap) in enumerate(self.columns, 1):
                s += f'\t\t\t\t<Column name="{c}" id="{i}">\n'
                if cap:
                    s += f"\t\t\t\t\t<Title>\n{lstr(cap, 6)}\t\t\t\t\t</Title>\n"
                s += "\t\t\t\t\t<Type>\n" + _indent(tx, 6) + "\t\t\t\t\t</Type>\n\t\t\t\t</Column>\n"
            s += "\t\t\t</Columns>\n"
        return s + "\t\t</Attribute>\n"


class Cmd:
    def __init__(self, name, title, tooltip=None, picture=None, action=None, representation=None, modifies=False):
        self.name, self.title, self.tooltip, self.picture = name, title, tooltip, picture
        self.action = action or name
        self.representation = representation or ("TextPicture" if picture else None)
        self.modifies = modifies

    def xml(self, cid):
        s = f'\t\t<Command name="{self.name}" id="{cid}">\n\t\t\t<Title>\n{lstr(self.title, 4)}\t\t\t</Title>\n'
        if self.tooltip:
            s += f"\t\t\t<ToolTip>\n{lstr(self.tooltip, 4)}\t\t\t</ToolTip>\n"
        if self.picture:
            s += (f"\t\t\t<Picture>\n\t\t\t\t<xr:Ref>{self.picture}</xr:Ref>\n"
                  "\t\t\t\t<xr:LoadTransparent>true</xr:LoadTransparent>\n\t\t\t</Picture>\n")
        s += f"\t\t\t<Action>{self.action}</Action>\n"
        if self.representation:
            s += f"\t\t\t<Representation>{self.representation}</Representation>\n"
        if self.modifies:
            s += "\t\t\t<ModifiesSavedData>true</ModifiesSavedData>\n"
        return s + "\t\t\t<CurrentRowUse>DontUse</CurrentRowUse>\n\t\t</Command>\n"


FORM_HEAD = ('<?xml version="1.0" encoding="UTF-8"?>\n<Form xmlns="http://v8.1c.ru/8.3/xcf/logform" '
             'xmlns:app="http://v8.1c.ru/8.2/managed-application/core" xmlns:cfg="http://v8.1c.ru/8.1/data/enterprise/current-config" '
             'xmlns:dcscor="http://v8.1c.ru/8.1/data-composition-system/core" xmlns:dcssch="http://v8.1c.ru/8.1/data-composition-system/schema" '
             'xmlns:dcsset="http://v8.1c.ru/8.1/data-composition-system/settings" xmlns:ent="http://v8.1c.ru/8.1/data/enterprise" '
             'xmlns:lf="http://v8.1c.ru/8.2/managed-application/logform" xmlns:style="http://v8.1c.ru/8.1/data/ui/style" '
             'xmlns:sys="http://v8.1c.ru/8.1/data/ui/fonts/system" xmlns:v8="http://v8.1c.ru/8.1/data/core" '
             'xmlns:v8ui="http://v8.1c.ru/8.1/data/ui" xmlns:web="http://v8.1c.ru/8.1/data/ui/colors/web" '
             'xmlns:win="http://v8.1c.ru/8.1/data/ui/colors/windows" xmlns:xr="http://v8.1c.ru/8.3/xcf/readable" '
             'xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="2.20">\n')


def form(items, attrs, commands=(), params=(), events=None, bar=None, bar_autofill=True, **props):
    """bar — кнопки командной панели формы; bar_autofill=False — без стандартных команд."""
    ids = Ids()
    s = FORM_HEAD
    head = dict(props)
    for tag in ORDER["Form"]:
        if tag in ("AutoCommandBar", "Events", "ChildItems", "Attributes", "Commands", "Parameters", "CommandInterface"):
            continue
        if tag in head:
            s += _val(tag, head.pop(tag), 1)
    if head:
        raise ValueError(f"Form: неизвестные свойства {list(head)}")
    s += '\t<AutoCommandBar name="ФормаКоманднаяПанель" id="-1">\n'
    if not bar_autofill:
        s += "\t\t<Autofill>false</Autofill>\n"
    if bar:
        s += "\t\t<ChildItems>\n" + "".join(b.xml(ids, 3) for b in bar) + "\t\t</ChildItems>\n"
    s += "\t</AutoCommandBar>\n"
    if events:
        s += "\t<Events>\n" + "".join(f'\t\t<Event name="{e}">{h}</Event>\n' for e, h in events.items()) + "\t</Events>\n"
    s += "\t<ChildItems>\n" + "".join(i.xml(ids, 2) for i in items) + "\t</ChildItems>\n"
    s += "\t<Attributes>\n" + "".join(a.xml(n) for n, a in enumerate(attrs, 1)) + "\t</Attributes>\n"
    if commands:
        s += "\t<Commands>\n" + "".join(c.xml(n) for n, c in enumerate(commands, 1)) + "\t</Commands>\n"
    if params:
        s += "\t<Parameters>\n"
        for name, tx in params:
            s += f'\t\t<Parameter name="{name}">\n\t\t\t<Type>\n' + _indent(tx, 4) + "\t\t\t</Type>\n\t\t</Parameter>\n"
        s += "\t</Parameters>\n"
    return s + "</Form>\n"


MDHEAD = ('<?xml version="1.0" encoding="UTF-8"?>\n<MetaDataObject xmlns="http://v8.1c.ru/8.3/MDClasses" '
          'xmlns:app="http://v8.1c.ru/8.2/managed-application/core" xmlns:cfg="http://v8.1c.ru/8.1/data/enterprise/current-config" '
          'xmlns:cmi="http://v8.1c.ru/8.2/managed-application/cmi" xmlns:ent="http://v8.1c.ru/8.1/data/enterprise" '
          'xmlns:lf="http://v8.1c.ru/8.2/managed-application/logform" xmlns:style="http://v8.1c.ru/8.1/data/ui/style" '
          'xmlns:sys="http://v8.1c.ru/8.1/data/ui/fonts/system" xmlns:v8="http://v8.1c.ru/8.1/data/core" '
          'xmlns:v8ui="http://v8.1c.ru/8.1/data/ui" xmlns:web="http://v8.1c.ru/8.1/data/ui/colors/web" '
          'xmlns:win="http://v8.1c.ru/8.1/data/ui/colors/windows" xmlns:xen="http://v8.1c.ru/8.3/xcf/enums" '
          'xmlns:xpr="http://v8.1c.ru/8.3/xcf/predef" xmlns:xr="http://v8.1c.ru/8.3/xcf/readable" '
          'xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="2.20">\n')


def form_md(owner_md, form_name, synonym):
    """Файл метаданных формы (…/Forms/<Имя>.xml). owner_md — «DataProcessor.X» / «Catalog.X»."""
    return MDHEAD + f'''	<Form uuid="{uid(owner_md, "Form", form_name)}">
		<Properties>
			<Name>{form_name}</Name>
			<Synonym>
{lstr(synonym, 4)}			</Synonym>
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


def data_processor_md(name, synonym, forms, default_form):
    md = f"DataProcessor.{name}"
    children = "".join(f"\t\t\t<Form>{f}</Form>\n" for f in forms)
    return MDHEAD + f'''	<DataProcessor uuid="{uid(md)}">
		<InternalInfo>
			<xr:GeneratedType name="DataProcessorObject.{name}" category="Object">
				<xr:TypeId>{uid(md, "Object", "type")}</xr:TypeId>
				<xr:ValueId>{uid(md, "Object", "value")}</xr:ValueId>
			</xr:GeneratedType>
			<xr:GeneratedType name="DataProcessorManager.{name}" category="Manager">
				<xr:TypeId>{uid(md, "Manager", "type")}</xr:TypeId>
				<xr:ValueId>{uid(md, "Manager", "value")}</xr:ValueId>
			</xr:GeneratedType>
		</InternalInfo>
		<Properties>
			<Name>{name}</Name>
			<Synonym>
{lstr(synonym, 4)}			</Synonym>
			<Comment/>
			<UseStandardCommands>true</UseStandardCommands>
			<DefaultForm>{md}.Form.{default_form}</DefaultForm>
			<AuxiliaryForm/>
			<IncludeHelpInContents>false</IncludeHelpInContents>
			<ExtendedPresentation/>
			<Explanation/>
		</Properties>
		<ChildObjects>
{children}		</ChildObjects>
	</DataProcessor>
</MetaDataObject>
'''


def write_module(rel, bsl_path):
    """Модуль берётся из исходника в tools/forms/bsl (UTF-8 без BOM, LF) и пишется в формате выгрузки."""
    write(rel, Path(bsl_path).read_text(encoding="utf-8"))
