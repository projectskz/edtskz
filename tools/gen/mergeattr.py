#!/usr/bin/env python3
# Вставляет блоки <Attribute>/<Resource>/<Dimension> с заданными именами из build/cfe в src/cfe
# после блока-соседа. usage: mergeattr.py <rel.xml> <ИмяНового> <ИмяПосле>
import sys,re
rel,name,after=sys.argv[1:4]
b=open("build/cfe/"+rel,encoding="utf-8-sig").read().replace("\r\n","\n")
sp="src/cfe/"+rel
raw=open(sp,"rb").read()
bom=raw.startswith(b"\xef\xbb\xbf")
s=raw.decode("utf-8-sig")
crlf="\r\n" in s
s=s.replace("\r\n","\n")
def block(t,n):
    m=re.search(r'(\n(\t+)<(Attribute|Resource|Dimension|TabularSection)\b[^>]*>\n\2\t<Properties>\n\2\t\t<Name>'+re.escape(n)+r'</Name>.*?\n\2</\3>)',t,re.S)
    return m
if block(s,name): print("уже есть",name); sys.exit()
nb=block(b,name); assert nb,name
ab=block(s,after); assert ab,after
s=s[:ab.end()]+nb.group(1)+s[ab.end():]
if crlf: s=s.replace("\n","\r\n")
open(sp,"wb").write((b"\xef\xbb\xbf" if bom else b"")+s.encode("utf-8"))
print("ok",name)
