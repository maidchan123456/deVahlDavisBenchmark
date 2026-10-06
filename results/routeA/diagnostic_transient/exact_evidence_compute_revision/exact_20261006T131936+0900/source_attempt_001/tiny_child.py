"""Safe watchdog test child; never used by measurement campaigns."""
import os,signal,subprocess,sys,time
from pathlib import Path
mode=sys.argv[1];out=Path(sys.argv[2]);(out/'tiny_pid').write_text(str(os.getpid()))
if mode=='normal':(out/'tiny_payload').write_text('UNCHANGED_BY_WATCHDOG');time.sleep(.1)
elif mode=='files':
 for i in range(16):(out/('tiny_file_'+str(i))).write_text('tiny')
 time.sleep(2)
elif mode=='memory':
 data=bytearray(16*2**20);time.sleep(2)
elif mode=='tree':
 child=subprocess.Popen([sys.executable,'-c','import signal,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);time.sleep(5)']);(out/'grandchild_pid').write_text(str(child.pid));signal.signal(signal.SIGTERM,signal.SIG_IGN);time.sleep(5)
elif mode=='escape':
 child=subprocess.Popen([sys.executable,'-c','import os,time;os.setsid();time.sleep(5)']);(out/'grandchild_pid').write_text(str(child.pid));time.sleep(5)
else:time.sleep(5)
