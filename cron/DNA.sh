#!/bin/sh


# +
#
# Name:        DNA.sh
# Description: DNA cron control
# Author:      Phil Daly (pndaly@email.arizona.edu)
# Date:        20190411
# Execute:     % bash DNA.sh
#
# % crontab -l
#   # +
#   # at noon every day, set up new directory
#   # -
#   0 12 * * * bash /var/www/ARTN-DNA/cron/DNA.sh >> /var/www/ARTN-DNA/logs/DNA.log 2>&1
# -


# +
# edit default(s) as required
# -
DATA_DIR="/data1/artn/rts2images/queue"
DARK_DIR="/data1/artn/rts2images"
DNA_DIR="/var/www/ARTN-DNA"
FLAT_DIR="/data1/artn/rts2images"
ARTN_OWNER="artn-eng:artn-eng"
WWW_OWNER="www-data:www-data"


# +
# set defaults
# -
TODAY=$(date +%Y%m%d)


# +
# create new data directory
# -
if [[ ! -d ${DATA_DIR}/${TODAY}/C0 ]]; then
  mkdir -p ${DATA_DIR}/${TODAY}/C0
fi


# +
# create new dark directory
# -
if [[ ! -d ${DARK_DIR}/${TODAY}/darks ]]; then
  mkdir -p ${DARK_DIR}/${TODAY}/darks
fi


# +
# create new flat directory
# -
if [[ ! -d ${FLAT_DIR}/${TODAY}/skyflats ]]; then
  mkdir -p ${FLAT_DIR}/${TODAY}/skyflats
fi


# +
# renew permissions
# -
touch ${DATA_DIR}/${TODAY}/C0/.dna.json
chmod 775 ${DATA_DIR}/${TODAY}/C0/.dna.json
chown -R ${ARTN_OWNER} ${DATA_DIR}
chown -R ${ARTN_OWNER} ${DARK_DIR}/${TODAY}
chown -R ${ARTN_OWNER} ${FLAT_DIR}/${TODAY}
chown -R ${ARTN_OWNER} ${DARK_DIR}/${TODAY}/darks
chown -R ${ARTN_OWNER} ${FLAT_DIR}/${TODAY}/skyflats
chown -R ${WWW_OWNER} ${DNA_DIR}


# +
# exit
# -
exit
