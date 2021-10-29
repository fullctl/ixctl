IXCTL_HOME=/srv/service

. $IXCTL_HOME/venv/bin/activate
cd $IXCTL_HOME/main

./manage.py $@
