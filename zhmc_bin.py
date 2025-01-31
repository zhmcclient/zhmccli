#!/usr/bin/env python
"""
Wrapper script used to create binary executable for zhmccli.
"""

import re
import sys
from zhmccli.zhmccli import cli

if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw|\.exe)?$', '', sys.argv[0])
    sys.exit(cli())
