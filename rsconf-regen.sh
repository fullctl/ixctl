#!/bin/bash
. /home/dev/.local/share/virtualenvs/ixctl-6nKie3nS/bin/activate
cd /home/dev/ixctl/src

export PATH=$HOME/opt/sqlite/bin:$PATH
export LD_LIBRARY_PATH=$HOME/opt/sqlite/lib
export LD_RUN_PATH=$HOME/opt/sqlite/lib

python manage.py ixctl_rsconf_generate
