"""v1.4 lifecycle accounting entry point; v1.3 accounting is preserved read-only."""
from account_lifecycle import calculate
import json
if __name__=="__main__":print(json.dumps(calculate(),indent=2))
