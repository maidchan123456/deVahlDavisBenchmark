"""All-or-nothing preparedness, independent of measurement/run permission."""
def derive(blockers):
 return {'Q1':all(blockers[k]['status']=='PASS' for k in ('B1','B4')),'Q2':all(blockers[k]['status']=='PASS' for k in ('B2','B3','B4'))}
