"""Fixed native startup verifier. No measurement dispatch or authorization creation."""
import sys
from runner import verify_stage_execution
if __name__=='__main__':
 if len(sys.argv)!=3:raise ValueError('STOP_NATIVE_PERMISSION_ARGUMENTS')
 verify_stage_execution(sys.argv[1],sys.argv[2])
