"""Read a user-supplied GameData dump to reproduce the access-condition report.

Only strings and typed metadata are inspected. This script never changes game
or save files and is not used by the editor at runtime.
"""
from pathlib import Path
import struct,json,re
BASE = None  # Supplied by the command line; no game data is bundled.
TYPES={'string','string[]','string[,]','u8','s8','u16','s16','u32','s32','u64','s64','int','uint','float','f32','b8','b16','b32','data','data[]','data[,]','ref','ref[]','u8[]','s16[]','s32[]','float[]','int[]'}
class Data:
 def __init__(self,file):
  self.b=(BASE/file).read_bytes();self.schemas=[]
  def field(at):
   if at+32>len(self.b):return None
   n,t,x,z,o=struct.unpack_from('<QQQII',self.b,at)
   name,typ=self.string(n),self.string(t)
   return (name,typ,z,o) if name and typ in TYPES and z in range(1,33) and 32<=o<=4096 else None
  at=32
  while at<len(self.b)-32:
   f=field(at)
   if f:
    start=at; fields=[]
    while f:
     fields.append(f);at+=32;f=field(at)
    self.schemas.append({'at':start,'end':at,'stride':(max(x[2]+x[3] for x in fields)+7)//8*8,'fields':fields})
   else:at+=8
 def q(self,p):return struct.unpack_from('<Q',self.b,p)[0]
 def string(self,p):
  if not p or not 32<=p+32<len(self.b):return ''
  try:
   end=self.b.index(0,p+32);s=self.b[p+32:end].decode('utf8')
   return s if s.isprintable() or '\n' in s else ''
  except (ValueError,UnicodeDecodeError):return ''
 def values(self,p,schema):
  result=[]
  for n,t,z,o in schema['fields']:
   if t=='string':v=self.string(self.q(p+o))
   elif t=='string[]':
    packed=self.q(p+o);count=packed&65535;step=(packed>>16)&65535;ptr=self.q(p+o+8)+32
    v=[self.string(self.q(ptr+i*step)) for i in range(count)] if count<100 and (count==0 or step==8 and ptr+count*step<=len(self.b)) else 'invalid array'
   elif t in ('f32','float'):v=struct.unpack_from('<f',self.b,p+o)[0]
   elif t in ('u8','s8','u16','s16','u32','s32','int','uint','b8','b16','b32'):v=int.from_bytes(self.b[p+o:p+o+z],'little',signed=t.startswith('s') or t=='int')
   else:v=self.b[p+o:p+o+z].hex()
   result.append((n,t,o,v))
  return result
 def refs_to_string(self,s):
  target=self.b.find(s.encode()+b'\0')-32
  if target<0:return []
  needle=struct.pack('<Q',target)
  return [m.start() for m in re.finditer(re.escape(needle),self.b) if m.start()%8==0]

if __name__ == '__main__':
 import argparse,hashlib
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('gamedata',type=Path)
 args=parser.parse_args();BASE=args.gamedata
 d=Data('HubDispos/Hub_000.bin');rows=[]
 targets=['ファストトラベル_アウロラの私室','ファストトラベル_アウロラの庭園',
          'ファストトラベル_サラミス迎賓館','ファストトラベル_ユ・ファス神殿',
          'ユ・ファス神殿侵入禁止','A9へ','A141へ','アウロラの私室へ',
          'アウロラの庭園へ','アウロラの私室赤ライン','アウロラの庭園赤ライン',
          'アウロラの庭園赤ライン（名前隠ぺい）']
 for target in targets:
  found=[]
  for at in d.refs_to_string(target):
   schema=max((s for s in d.schemas if s['at']<at),key=lambda s:s['at'])
   p=at-32;group=d.string(d.q(p+8))
   if not group.startswith(('ロケータ_','イベント_')):continue
   fields=d.values(p,schema)
   if not any(n=='配置ラベル' and o==32 and v==target for n,t,o,v in fields):continue
   found.append({'offset':hex(p),'group':group,'fields':[{'name':n,'offset':o,'value':v} for n,t,o,v in fields if t in ('string','string[]') and v]})
  if not found:raise ValueError('No supported row for '+target)
  rows.append({'label':target,'rows':found})
 print(json.dumps({'source':'HubDispos/Hub_000.bin','sha256':hashlib.sha256(d.b).hexdigest(),'entries':rows},ensure_ascii=False,indent=2))
