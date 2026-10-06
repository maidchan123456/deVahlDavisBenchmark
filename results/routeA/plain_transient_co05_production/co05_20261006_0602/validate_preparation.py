#!/usr/bin/env python3
"""Non-CFD tests: source arithmetic, offline log parsing, fail-closed preflight."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
from unittest.mock import patch
import numpy as np
import production_launcher as launcher

P=Path(__file__).resolve().parent
ROOT=P.parents[3]

def validate():
    plan=launcher.check();case=Path(plan['case']);tests=[]
    tests.append({'test':'complete_launch_preflight','result':'PASS','CFD_EXECUTED':'NO'})
    # A real input mutation in the newly prepared namespace must fail closed;
    # restore byte-for-byte even if the test itself fails.
    field=case/'0/U';original=field.read_bytes()
    try:
        field.write_bytes(original+b'\n// deliberate non-CFD tamper test\n')
        try: launcher.check()
        except RuntimeError as e:
            assert 'case changed: 0/U' in str(e);tests.append({'test':'actual_cold_field_tamper_rejected','result':'PASS'})
        else: raise AssertionError('tampered case accepted')
    finally: field.write_bytes(original)
    with patch.object(launcher.subprocess,'check_output',return_value='different_revision'):
        try: launcher.check()
        except RuntimeError as e:
            assert 'HEAD changed' in str(e);tests.append({'test':'HEAD_change_rejected','result':'PASS'})
        else:raise AssertionError('wrong HEAD accepted')
    runtime=Path(plan['runtime_output'])
    # Use a mocked namespace-existence result; never create an execution namespace.
    old_exists=Path.exists
    with patch.object(Path,'exists',lambda p: True if p==runtime else old_exists(p)):
        try: launcher.check()
        except RuntimeError as e:
            assert 'namespace already exists' in str(e);tests.append({'test':'existing_execution_namespace_rejected','result':'PASS'})
        else:raise AssertionError('reused execution accepted')
    with patch.object(launcher.sys,'argv',['production_launcher.py','--execute','--authorization-file',str(P/'production_authorization_draft.json')]), patch.object(launcher.subprocess,'Popen',side_effect=AssertionError('solver must never be invoked')) as popen,contextlib.redirect_stderr(io.StringIO()) as err:
        assert launcher.main()==2
        assert 'NOT_AUTHORIZED' in err.getvalue() and not popen.called
    assert not runtime.exists()
    tests.append({'test':'draft_NO_rejected_before_Popen_and_runtime_creation','result':'PASS'})
    log=ROOT/'results/routeA/transient_cfd_late_window_pilot/late_20261006_0531/log.foamRun'
    count=0;master=None;handler=False
    for line in log.read_text().splitlines():
        assert not launcher.fatal_line(line),line
        if line.startswith('Time = '):float(line.split('=',1)[1].strip().rstrip('s'));count+=1
        if line.startswith('PID    :'):master=int(line.split(':',1)[1])
        if 'sigWriteNow :' in line and 'Enabling' in line:handler=True
    assert count==598 and master and handler
    assert launcher.fatal_line('FOAM FATAL ERROR') and launcher.fatal_line('Final residual = nan')
    assert launcher.fatal_line('Floating point exception (core dumped)')
    assert not launcher.fatal_line('sigFpe : Enabling floating point exception trapping')
    tests.append({'test':'accepted_pilot_log_parser_and_fatal_detection','result':'PASS','steps_read_offline':count})
    rng=np.random.default_rng(415);d=rng.uniform(1e-6,.027734375,1000000)
    boundary=1420-.5*d
    for t in [boundary,np.nextafter(boundary,np.inf),boundary+.027734375]:
        stopped=~(t<(1420-.5*d));bins=((t+.5*d)/5).astype(int)
        assert np.all(bins[stopped]==284)
    before=np.nextafter(boundary,-np.inf)
    assert np.all(before<(1420-.5*d))
    finalproof={'result':'PASS','arithmetic_samples':3000000,'CFD_EXECUTED':'NO',
      'native_running_expression':'value < endTime - 0.5*deltaT',
      'native_write_bin_expression':'int(((value-beginTime)+0.5*deltaT)/writeInterval)',
      'beginTime':0,'endTime':1420,'writeInterval':5,'required_final_bin':284,
      'maxDeltaT':.027734375,'growth_limit':1.2,
      'final_time_lower_bound_s':1420-.5*.027734375,
      'final_time_upper_bound_s':1420+(1-1/(2*1.2))*.027734375,
      'exact_timestamp_forced':False,'output_changes_deltaT':False,
      'roundoff_test':'at termination boundary, next representable above, and one maxDeltaT beyond boundary; no missed final bin',
      'proof':'Since maxDeltaT < writeInterval, the first stopped step crosses bin284 without skipping any bin. Native driver writes before retesting running(). No adjustment for runTime IO.'}
    (P/'final_write_arithmetic_validation.json').write_text(json.dumps(finalproof,indent=2)+'\n')
    tests.append({'test':'native_final_write_boundary_arithmetic','result':'PASS','samples':3000000})
    # Initial analytic cold state and accepted late saved field calculations.
    import postprocess_production as post
    geo=np.load(P/'mesh_geometry.npz')
    f,t,index,native=post.reconstruct(case,'0');q,_=post.qoi(f,t,index,native,geo)
    assert q['Umax']==q['Wmax']==q['speed_max_m_s']==0
    assert abs(q['Nu_hot']-160)<1e-12 and abs(q['Nu_cold']-160)<1e-12
    with (P/'postprocess_validation_pass/transient_QoI.csv').open() as stream:
        import csv
        actual=next(csv.DictReader(stream))
    assert abs(float(actual['Nu_hot'])-6.2249983769413575)<1e-11
    assert abs(float(actual['speed_max_m_s'])-.03805799912427893)<1e-13
    with (P/'postprocess_validation_pass/native_step_diagnostics.csv').open() as stream:
        steps=list(csv.DictReader(stream))
    assert len(steps)==598 and all(int(r['pressure_solves'])==48 and int(r['energy_solves'])==24 for r in steps)
    tests.append({'test':'offline_QoI_analytic_cold_and_real_late_checkpoint_plus_native_598_steps','result':'PASS'})
    assert launcher.check()==plan
    (P/'production_launcher_dry_validation.json').write_text(json.dumps({'result':'PASS','tests':tests,'production_CFD_executed':'NO','runtime_namespace_created':False,'input_restored_and_reverified':True},indent=2)+'\n')
    print(json.dumps(tests,indent=2))

if __name__=='__main__':validate()
