#!/usr/bin/env python3
import re, sys, zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

CHORD_RE = re.compile(r'^(?:[A-G](?:#|b)?)(?:(?:m|maj|min|M|dim|aug|sus|add)?(?:2|4|5|6|7|9|11|13)?(?:b5|#5)?|m7b5)?(?:/[A-G](?:#|b)?)?$')
ROOT_PC={'C':0,'D':2,'E':4,'F':5,'G':7,'A':9,'B':11}

def parse_chord(s):
    s=s.strip().replace('♯','#').replace('♭','b').replace('Δ','maj')
    if not CHORD_RE.match(s): return None
    m=re.match(r'^([A-G])([#b]?)(.*?)(?:/([A-G])([#b]?))?$',s)
    if not m:return None
    return s,m.groups()

def harmony(chord):
    text,(step,acc,suf,bstep,bacc)=parse_chord(chord)
    h=ET.Element('harmony')
    r=ET.SubElement(h,'root'); ET.SubElement(r,'root-step').text=step
    if acc: ET.SubElement(r,'root-alter').text='1' if acc=='#' else '-1'
    sl=suf.lower()
    kinds={'':'major','m':'minor','min':'minor','7':'dominant','maj7':'major-seventh','m7':'minor-seventh','dim':'diminished','dim7':'diminished-seventh','aug':'augmented','sus2':'suspended-second','sus4':'suspended-fourth','6':'major-sixth','9':'dominant-ninth','m7b5':'half-diminished'}
    k=ET.SubElement(h,'kind'); k.text=kinds.get(sl,'major'); k.set('text',suf)
    if bstep:
        b=ET.SubElement(h,'bass'); ET.SubElement(b,'bass-step').text=bstep
        if bacc: ET.SubElement(b,'bass-alter').text='1' if bacc=='#' else '-1'
    return h

def read_xml(path):
    p=Path(path)
    if p.suffix.lower()=='.mxl':
        with zipfile.ZipFile(p) as z:
            names=[n for n in z.namelist() if n.lower().endswith(('.xml','.musicxml')) and 'container.xml' not in n.lower()]
            name=max(names,key=lambda n:z.getinfo(n).file_size)
            return ET.fromstring(z.read(name)),p,name
    return ET.parse(p).getroot(),p,None

def main():
    if len(sys.argv)<3: raise SystemExit('usage: merge_chords.py MUSICXML TSV')
    root,p,inner=read_xml(sys.argv[1])
    if root.findall('.//harmony'):
        print('MusicXML already contains harmony; leaving it unchanged'); return
    rows=[]
    for line in Path(sys.argv[2]).read_text(errors='ignore').splitlines():
        a=line.split('\t')
        if len(a)<4: continue
        try: x,y,w=float(a[6]),float(a[7]),float(a[8])
        except: continue
        c=parse_chord(a[11])
        if c: rows.append((x+w/2,y,c[0]))
    if not rows: print('No chord symbols detected'); return
    measures=root.findall('.//part[1]/measure')
    if not measures:return
    # OCR x coordinates are mapped monotonically across measures. This is a fallback
    # for cases where Audiveris omits harmony; repeated systems are distributed by y.
    ys=sorted(set(round(r[1]/120)*120 for r in rows))
    systems={y:i for i,y in enumerate(ys)}
    per=max(1,(len(measures)+len(ys)-1)//max(1,len(ys)))
    for x,y,c in rows:
        sy=min(ys,key=lambda q:abs(q-y)); candidates=measures[systems[sy]*per:min((systems[sy]+1)*per,len(measures))]
        if not candidates: continue
        xs=sorted(r[0] for r in rows if abs(r[1]-y)<120)
        rank=sum(v<x for v in xs)/max(1,len(xs))
        mi=min(len(candidates)-1,int(rank*len(candidates)))
        candidates[mi].insert(0,harmony(c))
    out=Path(sys.argv[1]).with_suffix('.musicxml')
    ET.ElementTree(root).write(out,encoding='utf-8',xml_declaration=True)
    print(f'Merged {len(rows)} OCR chord symbols -> {out}')
if __name__=='__main__': main()
