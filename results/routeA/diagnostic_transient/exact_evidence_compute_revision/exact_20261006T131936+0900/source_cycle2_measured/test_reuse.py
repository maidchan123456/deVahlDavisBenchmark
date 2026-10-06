import copy,importlib.util,math,random,unittest
from common import ROOT
import online_evaluator as oe
import persistence as persist
from reuse import Reuse,install

META={k:0 for k in ('time_index','outer','pressure','nonOrthogonal','energy_solve','rho_solve')}
class Tests(unittest.TestCase):
 def test_content_epoch_mutation_eviction(self):
  c=Reuse(4096);calls=[]
  def f(x):calls.append(1);return bytes(str(x),'utf8')
  c.begin(META,1);v=list(range(100));a=c.apply('x',v,f);self.assertEqual(a,c.apply('x',list(v),f));self.assertEqual(len(calls),1)
  v[0]=999;self.assertNotEqual(a,c.apply('x',v,f));self.assertEqual(len(calls),2)
  c.begin(dict(META,pressure=1),2);c.apply('x',v,f);self.assertEqual(len(calls),3)
  for i in range(50):c.apply('x',list(range(i,i+100)),f)
  self.assertLessEqual(c.bytes,c.limit);self.assertGreater(c.stats['evictions'],0)
 def test_unknown_epoch_and_mutable_result(self):
  c=Reuse();calls=[]
  def f(x):calls.append(1);return [x]
  c.apply('x',1,f);c.apply('x',1,f);self.assertEqual(len(calls),2)
  c.begin(META,1);r=c.apply('x',1,f,True);r[0]=2;self.assertEqual(c.apply('x',1,f,True),[1])
 def test_exact_canonical_packing_errors(self):
  oldc=oe.canonical;oldr=oe.replay_matrix;olde=persist.encode;c=install(oe,persist);c.begin(META,1);rng=random.Random(20261006)
  try:
   fixtures=[{'array':[rng.uniform(-1e100,1e100) for _ in range(100)]},[float.fromhex('0x0.0000000000001p-1022'),-0.,0,1,1.]*20,{'vector':[[rng.random(),rng.random(),rng.random()] for _ in range(100)]}]
   for x in fixtures:
    self.assertEqual(oldc(x),oe.canonical(x));self.assertEqual(olde(x),persist.encode(x));self.assertEqual(oldc(x),oe.canonical(copy.deepcopy(x)));self.assertEqual(olde(x),persist.encode(copy.deepcopy(x)))
   for x in ([math.nan],[math.inf],{'owner':[1.,2.]}):
    funcs=(oldc,oe.canonical) if not isinstance(x,dict) else (olde,persist.encode);errors=[]
    for fn in funcs:
     try:fn(x)
     except Exception as e:errors.append((type(e).__name__,str(e)))
    self.assertEqual(len(errors),2);self.assertEqual(errors[0],errors[1])
   self.assertGreater(c.stats['hits'],0)
  finally:oe.canonical=oldc;oe.replay_matrix=oldr;persist.encode=olde;persist.canonical=oldc
if __name__=='__main__':unittest.main()
