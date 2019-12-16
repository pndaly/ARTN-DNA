#!/bin/sh


# +
#
# Name:        DNA.sh
# Description: DNA environment set up
# Author:      Phil Daly (pndaly@email.arizona.edu)
# Date:        20190411
# Execute:     % bash DNA.sh [DNA_directory]
#
# -


# +
# edit default(s) as required
# -
export DNA_HOME=${1:-/var/www/ARTN-DNA}

export DNA_BIN=${DNA_HOME}/bin
export DNA_CRON=${DNA_HOME}/cron
export DNA_ETC=${DNA_HOME}/etc
export DNA_LOGS=${DNA_HOME}/logs
export DNA_SRC=${DNA_HOME}/src


# +
# PYTHONPATH
# -
pythonpath=$(env | grep PYTHONPATH)
if [[ -z ${pythonpath} ]]; then
  export PYTHONPATH=${DNA_HOME}:${DNA_SRC}:$(pwd)
else
  export PYTHONPATH=${DNA_HOME}:${DNA_SRC}:${PYTHONPATH}
fi
