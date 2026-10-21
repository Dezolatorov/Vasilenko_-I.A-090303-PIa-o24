import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRV = os.path.join(ROOT, "loans-service")
for p in (ROOT, SRV):
    if p not in sys.path:
        sys.path.insert(0, p)