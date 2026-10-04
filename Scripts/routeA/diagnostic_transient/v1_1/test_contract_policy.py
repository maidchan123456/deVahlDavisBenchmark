"""Synthetic policy and evidence unit tests, no CFD/real-case I/O."""
import math
import unittest
import contract_policy as p


class PolicyTests(unittest.TestCase):
    def test_first_native_step_growth(self):
        self.assertAlmostEqual(p.controller_step(p.CONTROL_DICT_DT,0,0.5),p.FIRST_PHYSICAL_DT)
        self.assertAlmostEqual(p.FIRST_PHYSICAL_DT/p.CELL_THERMAL_TIME,0.001)

    def test_controller_targets_and_growth_cap(self):
        self.assertEqual(p.controller_step(.01,1,.25),.0025)
        self.assertEqual(p.controller_step(.01,.1,.5),.012)
        self.assertEqual(p.controller_step(.1,0,.125),p.MAX_DT)
        self.assertAlmostEqual(p.controller_step(1e-17,5e-16,.125),1.2e-17)
        for h,co,target in ((-.1,0,.5),(.1,-1,.5),(.1,0,.75),(.1,math.nan,.5)):
            with self.assertRaises(ValueError): p.controller_step(h,co,target)

    def test_representable_minimum_step(self):
        self.assertGreater(p.minimum_dt(1420),math.ulp(1420))
        self.assertGreater(1420+p.minimum_dt(1420),1420)

    def test_conditional_iterative_budget(self):
        names={"U","T","p_rgh","rho_s","rho_T","Nu_bar_cavity","Umax","Wmax"}
        changes={k:[1e-7,5e-8,2.5e-8,1.25e-8] for k in names}
        floors={k:1e-12 for k in names}
        estimates=p.certify_outer(changes,floors)
        self.assertLess(max(estimates.values()),p.ITERATIVE_BUDGET)
        changes["T"]=[1e-7]*4
        with self.assertRaises(ValueError):p.certify_outer(changes,floors)
        changes["T"]=[1e-13]*4
        self.assertLess(p.certify_outer(changes,floors)["T"],p.ITERATIVE_BUDGET)

    def test_inner_missing_or_large_floor_rejected(self):
        with self.assertRaises(ValueError):p.certify_outer({}, {})
        names={"U","T","p_rgh","rho_s","rho_T","Nu_bar_cavity","Umax","Wmax"}
        with self.assertRaises(ValueError):p.certify_outer({k:[0]*4 for k in names},{k:1e-3 for k in names})

    def test_linear_policy_failure_and_completeness(self):
        good=[(k,1e-2,1e-14,0 if k=="rho" else 5) for k in ("Ux","Uy","e","p_rgh","rho")]
        p.validate_linear(good)
        with self.assertRaises(ValueError):p.validate_linear(good[:-1])
        with self.assertRaises(ValueError):p.validate_linear(good+[("p_rgh",1,1e-3,4000)])

    def test_nonuniform_time_weighted_mean(self):
        stats=p.window_stats([0,.01,.08,.1],[0,.01,.08,.1],.1)
        self.assertAlmostEqual(stats["mean"],.05)
        self.assertAlmostEqual(stats["slope"],1)
        self.assertAlmostEqual(stats["half_mean_drift"],.05)
        self.assertAlmostEqual(stats["normalized_slope_span"],.1)

    def test_no_extrapolation_duplicate_nonfinite(self):
        for times,vals,x in (([0,1],[0,1],2),([0,0],[0,1],0),([0,1],[0,math.nan],.5)):
            with self.assertRaises(ValueError):p.interpolate(times,vals,x)

    def histories(self,drift=0):
        times=[0,.07,.2,.23,.29,.4,.47,.5,.51,.7]
        h={k:[(8 if k=="Nu_bar_cavity" else 200 if k=="Wmax" else 65)+drift*t for t in times]
           for k in ("Nu_bar_cavity","Umax","Wmax")}
        scales={"rho_min":.001,"rho_max":.001,"rho_mean":.001,"total_mass":1e-8,"energy_storage":.01}
        for k in scales: h[k]=[.0185 if k=="energy_storage" else 1e-5 if k=="total_mass" else 1.0 for _ in times]
        return times,h,scales

    def test_three_physical_windows_and_final_value(self):
        times,h,scales=self.histories()
        ok,windows=p.arrival_candidate(times,h,.5,scales,True)
        self.assertTrue(ok);self.assertEqual(len(windows),3)
        self.assertAlmostEqual(windows[-1]["Nu_bar_cavity"]["mean"],8)
        self.assertAlmostEqual(windows[-1]["Nu_bar_cavity"]["left"],.4)
        self.assertAlmostEqual(windows[-1]["Nu_bar_cavity"]["right"],.5)

    def test_early_invalid_drifting_or_mass_runaway_not_arrival(self):
        times,h,scales=self.histories(drift=1)
        self.assertFalse(p.arrival_candidate(times,h,.5,scales,True)[0])
        times,h,scales=self.histories()
        self.assertFalse(p.arrival_candidate(times,h,.4,scales,True)[0])
        self.assertFalse(p.arrival_candidate(times,h,.51,scales,True)[0])
        self.assertFalse(p.arrival_candidate(times,h,.5,scales,False)[0])
        h["total_mass"]=[1e-5+1e-8*t for t in times]
        self.assertFalse(p.arrival_candidate(times,h,.5,scales,True)[0])

    def test_stage_duplicates_missing_reordered(self):
        packet=dict(time_index=1,time=.1,outer=1,pressure=0,energy_solve=1,
                    stage="energy_assembly",oldTime_ids=["rho:old0:sha"],dt=.1,dt_previous=.2)
        ledger=p.StageLedger();ledger.accept(packet)
        ledger.expect([(1,1,0,1,"energy_assembly")])
        with self.assertRaises(ValueError):ledger.accept(packet)
        with self.assertRaises(ValueError):ledger.expect([])
        packet["oldTime_ids"]=[]
        with self.assertRaises(ValueError):p.StageLedger().accept(packet)
        packet["oldTime_ids"]=[""]
        with self.assertRaises(ValueError):p.StageLedger().accept(packet)
        packet["oldTime_ids"]=["rho:old0:sha"]
        packet["outer"]=-1
        with self.assertRaises(ValueError):p.StageLedger().accept(packet)

    def test_independence_of_conservation_accuracy_threshold(self):
        # A synthetic *state* plateau can satisfy arrival even if its constant
        # conservation defect is large: such a defect is a mandatory diagnostic
        # concern, never conservation PASS. The evaluator-valid input must first
        # cover native stage identities, which this synthetic fixture does not.
        times,h,scales=self.histories()
        self.assertTrue(p.arrival_candidate(times,h,.5,scales,True)[0])


if __name__=="__main__":
    unittest.main(verbosity=2)
