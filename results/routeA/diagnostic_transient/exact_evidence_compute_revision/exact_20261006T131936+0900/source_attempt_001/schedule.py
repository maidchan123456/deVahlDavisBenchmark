"""Explicit resource campaign checkpoint around the unmodified production Schedule."""
from persistence import Schedule,AUDIT_CAP,BUNDLE_CAP,FIELD_CAP
from common import need

def context(kind):
 need(kind in ('STARTUP_ONE_TIME','RECURRING_STEP_EQUIVALENT'),'STOP_SCHEDULE_CONTEXT')
 s=Schedule()
 if kind=='RECURRING_STEP_EQUIVALENT':
  # Reconstruct a resource-only checkpoint after the three registered startup
  # slots. No Writer policy is edited; begin() itself consumes each slot.
  for time in (.1,.2,.3):s.begin(time)
  need(s.step==3 and s.full_count==3,'STOP_STARTUP_CHECKPOINT')
 return s

def recurring_time():return Schedule().bundle_targets[0]*710

def accounting(cfg):
 # One full startup write sample, multiplicity 3 retained as an explicit cost
 # projection. Recurring repeats use the same immutable resource checkpoint,
 # so selected and final bundle contents have a single retained CAS identity.
 # Every selected/final write is still performed before representation migration.
 trace=384*2**20;receipts=64*2**20;primary=16*2**20;stop=16*2**20
 retained=AUDIT_CAP+BUNDLE_CAP+7*(receipts+primary+2*FIELD_CAP)+trace
 temporary=2*BUNDLE_CAP+2*FIELD_CAP+receipts+primary
 # Startup and recurring temporaries have distinct lifetimes. Startup audit is
 # adopted without copying; recurring workspace is bounded and content-shared.
 total=retained+temporary+64*2**20+stop
 return {'startup_audit_sample_count':1,'production_startup_full_audit_slots':3,'startup_projection_multiplicity':3,'startup_cost_not_hidden':True,'recurring_repeat_context':'AFTER_THREE_STARTUP_SLOTS_FIRST_SELECTED_TARGET','maximum_retained_bytes':retained,'maximum_temporary_bytes':temporary,'archive_copy_buffer_bound':64*2**20,'manifest_trace_reserve_bytes':trace,'partial_stop_reserve_bytes':stop,'maximum_simultaneous_bytes':total,'registered_scratch_bytes':cfg['stages']['Q1']['budgets']['scratch_bytes'],'within_budget':total<=cfg['stages']['Q1']['budgets']['scratch_bytes'],'sharing_required':'EXACT_SELECTED_BUNDLE_CONTENT_IDENTITY_VERIFIED_AT_EACH_COMMIT','production_policy_changed':False}
