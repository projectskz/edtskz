import xml.etree.ElementTree as ET, glob, collections, sys, os
def tag(e): return e.tag.split('}')[1]
before=collections.defaultdict(set)  # (parent tag) -> set of (a,b) where a seen before b
seen=collections.defaultdict(set)
files=glob.glob(os.environ.get('SSL','ssl')+'/src/cf/**/Ext/Form.xml',recursive=True)
for f in files:
    try: r=ET.parse(f).getroot()
    except Exception: continue
    for el in r.iter():
        kids=[tag(k) for k in el]
        p=tag(el)
        for i,a in enumerate(kids):
            seen[p].add(a)
            for b in kids[i+1:]:
                if a!=b: before[p].add((a,b))
print('forms:',len(files))
r=ET.parse(sys.argv[1]).getroot(); bad=0
for el in r.iter():
    kids=[tag(k) for k in el]; p=tag(el)
    for k in kids:
        if k not in seen[p]: print('НЕ ВСТРЕЧАЛОСЬ:',p,'>',k); bad+=1
    for i,a in enumerate(kids):
        for b in kids[i+1:]:
            if (b,a) in before[p] and (a,b) not in before[p]: print('ПОРЯДОК:',p,':',a,'должен идти после',b); bad+=1
print('bad',bad)
