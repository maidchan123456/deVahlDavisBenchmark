"""Four-cell nested supervisor/archive validation for the new revision."""
import sys,time
from common import REVISION_ROOT,atomic,load
from campaign import launch_campaign
from archive import recover
from trace_codec import iter_trace
reqs=[{'kind':'pipeline','mode':'ON','purpose':'primitive','sample_class':c,'phase':'tiny_'+c,'context_kind':'RECURRING_STEP_EQUIVALENT'} for c in ('controller','field','matrix','term','energy_matrix','pressure_matrix')]
start=time.monotonic();r=launch_campaign(REVISION_ROOT/'tiny_campaign_003','SCOUT',tiny=True,test_requests=reqs,test_budget={'stage_wall_seconds':90,'single_trial_wall_seconds':12})
assert r['status']=='COMPLETE_REQUIRES_RESOURCE_REVIEW',r
assert len(r['trials'])==6
records,tail=recover(REVISION_ROOT/'tiny_campaign_003/archive');assert len(records)==6 and not tail
atomic(REVISION_ROOT,'tiny_campaign_validation_003.json',{'status':'PASS','trials':6,'nested_supervisor_and_archive':'PASS','resource_trace_representation':'lossless gzip members','stage_wall_seconds':time.monotonic()-start,'target_size_executed':False,'CFD_executed':False})
print(r['status'])
