"""Trusted sandbox entry: bound the plugin before executing reviewed Python."""
import os
import resource
import sys

resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024,) * 2)
resource.setrlimit(resource.RLIMIT_CPU, (3, 3))
resource.setrlimit(resource.RLIMIT_FSIZE, (8 * 1024 * 1024,) * 2)
resource.setrlimit(resource.RLIMIT_NPROC, (16, 16))
resource.setrlimit(resource.RLIMIT_NOFILE, (32, 32))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
os.execv('/usr/bin/python3', ['/usr/bin/python3', '-I', '-B', sys.argv[1]])
