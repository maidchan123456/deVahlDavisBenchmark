import pilot
for rank in [2,4,6,8,12]:
 if not pilot.run(rank):
  import json
  t=json.loads((pilot.OUT/f'rank_{rank:02d}'/'timing.json').read_text())
  if t['status'] not in ['WALL_LIMIT']:raise SystemExit('STOP: generic contract/solver failure; preserve evidence')
