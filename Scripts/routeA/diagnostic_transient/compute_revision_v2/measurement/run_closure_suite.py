"""Run the original regression suite and B1-B4 tiny correctness tests only."""
import json,sys,unittest
from pathlib import Path
from common import atomic,sha,plan,HERE
import test_closure,test_preparation

class Result(unittest.TextTestResult):
 def __init__(self,*args,**kwargs):super().__init__(*args,**kwargs);self.records=[]
 def addSuccess(self,test):super().addSuccess(test);self.records.append({'test':test.id(),'status':'PASS'})
 def addFailure(self,test,err):super().addFailure(test,err);self.records.append({'test':test.id(),'status':'FAIL'})
 def addError(self,test,err):super().addError(test,err);self.records.append({'test':test.id(),'status':'ERROR'})

if __name__=='__main__':
 out=Path(sys.argv[1]);source_before={str(p):sha(p) for p in HERE.iterdir() if p.is_file()};suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromModule(test_closure),unittest.defaultTestLoader.loadTestsFromModule(test_preparation)])
 result=unittest.TextTestRunner(verbosity=2,resultclass=Result).run(suite)
 source_after={str(p):sha(p) for p in HERE.iterdir() if p.is_file()};unchanged=source_before==source_after
 atomic(out.parent,out.name,{'schema':'timing_preparation_closure_tests/2','status':'PASS' if result.wasSuccessful() and unchanged else 'FAIL','source_unchanged_during_tests':unchanged,'source_SHA256':source_after,'tests_run':result.testsRun,'tests':result.records,'tiny_stage_evidence':test_closure.RESULTS,'classification':'TINY_CORRECTNESS_PROCESS_LAYOUT_ONLY','Q1_Q2_actual_target_measurements_executed':False,'actual_authorization_created':False})
 sys.exit(0 if result.wasSuccessful() and unchanged else 1)
