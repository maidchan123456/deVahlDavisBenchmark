"""Explicit user-operated verify/dry-run/purge; never invoked by capacity preflight."""
import argparse,json
from lifecycle import Series
p=argparse.ArgumentParser();p.add_argument('action',choices=('verify','dry-run','purge'));p.add_argument('root');p.add_argument('--seal-id',required=True);p.add_argument('--dry-run-id');p.add_argument('--authorization-id');p.add_argument('--explicit-user-authorization',action='store_true');a=p.parse_args();s=Series(a.root)
if a.action=='verify':out=s.verify(a.seal_id)
elif a.action=='dry-run':out=s.dry_run(a.seal_id)
else:out=s.purge(a.seal_id,a.dry_run_id,a.authorization_id,a.explicit_user_authorization)
print(json.dumps(out,indent=2))
