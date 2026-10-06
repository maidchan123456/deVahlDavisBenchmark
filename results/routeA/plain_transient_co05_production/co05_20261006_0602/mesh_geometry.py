"""Read fixed ASCII mesh geometry for preparation and offline saved-field analysis."""
from pathlib import Path
import re
import numpy as np
def body(path):
 s=Path(path).read_text();m=re.search(r'\n(\d+)\s*\n\(\s*\n',s)
 if not m:raise ValueError('Missing ASCII list: '+str(path))
 return int(m[1]),s[m.end():s.rfind(')')]
def labels(path):
 n,s=body(path);a=np.fromstring(s,sep=' ',dtype=np.int64)
 if len(a)!=n:raise ValueError('Bad label count: '+str(path))
 return a
def geometry(mesh):
 n,s=body(mesh/'points');points=np.array([[float(v) for v in row.split()] for row in re.findall(r'\(([^()]*)\)',s)]);assert points.shape==(n,3)
 n,s=body(mesh/'faces');faces=np.array([[int(v) for v in row.split()] for row in re.findall(r'\d+\(([^()]*)\)',s)]);assert faces.shape==(n,4)
 owner=labels(mesh/'owner');neighbour=labels(mesh/'neighbour');assert len(owner)==n;cells=int(owner.max())+1
 vertices=points[faces];face_lo=vertices.min(axis=1);face_hi=vertices.max(axis=1);lo=np.full((cells,3),np.inf);hi=np.full((cells,3),-np.inf)
 np.minimum.at(lo,owner,face_lo);np.maximum.at(hi,owner,face_hi);np.minimum.at(lo,neighbour,face_lo[:len(neighbour)]);np.maximum.at(hi,neighbour,face_hi[:len(neighbour)])
 return {'lo':lo,'hi':hi,'centres':(lo+hi)/2,'volumes':np.prod(hi-lo,axis=1),'owner':owner,'neighbour':neighbour,'face_count':n}
def patch_cells(mesh,name,owner):
 text=(mesh/'boundary').read_text();m=re.search(r'\b'+re.escape(name)+r'\s*\{([^}]*)\}',text,re.S)
 if not m:raise ValueError(name)
 start=int(re.search(r'startFace\s+(\d+)',m[1])[1]);count=int(re.search(r'nFaces\s+(\d+)',m[1])[1]);return owner[start:start+count]
