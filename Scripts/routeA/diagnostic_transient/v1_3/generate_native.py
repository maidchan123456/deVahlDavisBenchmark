"""Only replace observer persistence; graph/operator hooks are inherited verbatim."""
from pathlib import Path
import hashlib
H=Path(__file__).resolve().parent;P=H.parent/'v1_2'
s=(P/'NativeStageObserver.C').read_text()
assert hashlib.sha256(s.encode()).hexdigest()=='d745d08364c1aeb71d7536fd53aa68d810335a17c0cf700b4682a152028291ba'
s=s.replace('#include <algorithm>','#include <algorithm>\n#include "PersistenceBridge.H"')
a=s.index(' const std::string bytes=record.dump()');b=s.index('\n}',a)
s=s[:a]+' persistence::send(record.dump()+"\\n");'+s[b:]
a=s.index('void Observer::finish()');b=s.index('\nObserver* current()',a)
s=s[:a]+'''void Observer::finish(){if(phase!="time_end")fail("INCOMPLETE_STAGE_SEQUENCE");if(completed)fail("DUPLICATE_FINISH");persistence::send("FINISH\\n");persistence::close();completed=true;}'''+s[b:]
s=s.replace('if(::mkdir(root.c_str(),0700)!=0)fail("EXPORT_ROOT_MUST_BE_NEW");','if(::mkdir(root.c_str(),0700)!=0)fail("EXPORT_ROOT_MUST_BE_NEW");\n persistence::start(root,guard,src,inst);')
(H/'NativeStageObserver.C').write_text(s)
(H/'NativeStageObserver.H').write_text((P/'NativeStageObserver.H').read_text())
(H/'DiagnosticJson.H').write_text((P/'DiagnosticJson.H').read_text())
