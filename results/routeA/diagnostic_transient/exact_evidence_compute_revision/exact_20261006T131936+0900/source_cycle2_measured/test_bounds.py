"""Conservative CPU bounds and post-revision framing validation."""
import sys,unittest
from common import REVISION_ROOT,atomic
from test_revision import Revision
from cpu_attribution import interval
from analysis import host_stability
class Bounds(unittest.TestCase):
 def test_late_discovery_does_not_credit_preboundary_ticks(self):
  p={'root_present':True,'root_identity':[1,2],'subtree_ticks':10,'observer_ticks':{},'identities':{},'boottime':2}
  q=dict(p,subtree_ticks=30,identities={'2:100':{'starttime_ticks':100,'own_ticks':20}},CLK_TCK=100,CPU_count=24)
  r=interval(p,q,100,30);self.assertEqual(r['own_ticks'],0);self.assertEqual(r['other_fraction_upper'],.30)
 def test_snapshot_race_uses_host_upper(self):
  p={'root_present':True,'root_identity':[1,2],'subtree_ticks':10,'subtree_ticks_upper':12,'observer_ticks':{'9':3},'observer_ticks_upper':{'9':4},'snapshot_certified':True}
  q=dict(p,subtree_ticks=25,subtree_ticks_upper=27,observer_ticks={'9':6});r=interval(p,q,100,30);self.assertEqual(r['own_ticks'],15);self.assertEqual(r['other_fraction_upper'],.15)
  q['snapshot_certified']=False;r=interval(p,q,100,30);self.assertEqual(r['other_fraction_upper'],.30);self.assertTrue(r['uncertainty'])
 def test_unknown_own_upper_can_certify_only_below10percent(self):
  def row(t,b):return {'timestamp_monotonic':t,'host':{'CPU_stat':f'cpu {b} 0 0 {1000-b} 0 0 0 0','MemAvailable':99,'loadavg':[0,0,0],'CPU_governor':'powersave','CPU_frequency':{'min':'800','max':'4500'},'CPU_count':24},'cpu_attribution':{'root_present':False,'root_identity':None,'subtree_ticks':0,'observer_ticks':{}},'disk_free':100,'file_count':1,'scratch_bytes':1}
  a=row(1,0);b=row(1.02,0);b['host']['CPU_stat']='cpu 5 0 0 1095 0 0 0 0';self.assertEqual(host_stability([a,b])['status'],'STABLE');b['host']['CPU_stat']='cpu 20 0 0 1080 0 0 0 0';self.assertEqual(host_stability([a,b])['status'],'UNRESOLVED')
suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(Bounds),Revision('test_framing_exact_equivalence'),Revision('test_CPU_late_child_and_reaped_short_lived'),Revision('test_CPU_controlled_tree'),Revision('test_new_watchdog_timeout_trace')]);r=unittest.TextTestRunner(verbosity=2).run(suite);atomic(REVISION_ROOT,'bounds_validation_cycle2.json',{'status':'PASS' if r.wasSuccessful() else 'FAIL','tests':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),'rule_changed':False});sys.exit(not r.wasSuccessful())
