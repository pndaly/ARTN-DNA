#!/bin/sh


# +
#
# Name:        TGZ.sh
# Description: TGZ control
# Author:      Phil Daly (pndaly@email.arizona.edu)
# Date:        20190411
# Execute:     % bash TGZ.sh [yyyymmdd] --help
#
# -


# +
# default(s)
# -
def_darks_root="/data1/artn/rts2images"
def_tgz_iso=$(date +%Y%m%d)
def_skyflats_root="/data1/artn/rts2images"
dna_dir="/var/www/ARTN-DNA"
dry_run=0
over_ride=0
www_own="www-data:www-data"
www_dir="/var/www/ARTN-ORP/instance/files"


# +
# variable(s)
# -
darks_root="${def_darks_root}"
skyflats_root="${def_skyflats_root}"
tgz_iso="${def_tgz_iso}"


# +
# utility functions
# -
write_blue () {
  BLUE='\033[0;34m'
  NCOL='\033[0m'
  printf "${BLUE}${1}${NCOL}\n"
}
write_red () {
  RED='\033[0;31m'
  NCOL='\033[0m'
  printf "${RED}${1}${NCOL}\n"
}
write_yellow () {
  YELLOW='\033[0;33m'
  NCOL='\033[0m'
  printf "${YELLOW}${1}${NCOL}\n"
}
write_green () {
  GREEN='\033[0;32m'
  NCOL='\033[0m'
  printf "${GREEN}${1}${NCOL}\n"
}
write_cyan () {
  CYAN='\033[0;36m'
  NCOL='\033[0m'
  printf "${CYAN}${1}${NCOL}\n"
}


# +
# check command line argument(s) 
# -
while test $# -gt 0; do
  case "${1}" in
    -d*|-D*|--darks*|--DARKS*)
      darks_root=$(echo $1 | cut -d'=' -f2)
      shift
      ;;
    -i*|-I*|--iso*|--ISO*)
      tgz_iso=$(echo $1 | cut -d'=' -f2)
      shift
      ;;
    -n|-N|--dry-run|--DRY-RUN)
      dry_run=1
      shift
      ;;
    -x|-X|--over-ride|--OVER-RIDE)
      over_ride=1
      shift
      ;;
    -s*|-S*|--skyflats*|--SKYFLATS*)
      skyflats_root=$(echo $1 | cut -d'=' -f2)
      shift
      ;;
    -h*|-H*|--help*|--HELP*|*)
      write_blue "\nTGZ Control\n"                                                                                         2>&1
      write_green "Use:\n %% bash $0 --darks=<str> --iso=<int> --skyflats=<str> [--dry-run] [--over-ride]\n"               2>&1
      write_yellow "Input(s):"                                                                                             2>&1
      write_yellow "  --darks=<str>      -r=<str>  where <str> is darks root directory,     default=${def_darks_root}"     2>&1
      write_yellow "  --iso=<int>,       -i=<int>  where <int> is the date in YYYYMMDD,     default=${def_tgz_iso}"        2>&1
      write_yellow "  --skyflats=<str>,  -s=<str>  where <str> is skyflats root directory,  default=${def_skyflats_root}"  2>&1
      write_cyan "Flag(s):"                                                                                                2>&1
      write_cyan "    --dry-run,         -n        show (but do not execute) commands,      default=false"                 2>&1
      write_cyan "    --over-ride,       -x        replace existing tarball(s),             default=false"                 2>&1
      exit 0
      ;;
  esac
done


# +
# check and (re)set variable(s)
# -
if [[ ! -d ${darks_root} ]]; then
  write_red "<ERROR> darks root directory (${darks_root}) is unknown ... exiting"
  exit 0 
fi

if [[ ! -d ${skyflats_root} ]]; then
  write_red "<ERROR> skyflats root directory (${skyflats_root}) is unknown ... exiting"
  exit 0 
fi

case ${tgz_iso} in
  [0-9]*)
    ;;
  *)
    tgz_iso=${def_tgz_iso}
    ;;
esac

_darks_dir="${darks_root}/${tgz_iso}/darks"
if [[ ! -d ${_darks_dir} ]]; then
  write_red "<ERROR> darks directory (${_darks_dir}) is unknown ... exiting"
  exit 0 
fi

_skyflats_dir="${skyflats_root}/${tgz_iso}/skyflats"
if [[ ! -d ${_skyflats_dir} ]]; then
  write_red "<ERROR> skyflats directory (${_skyflats_dir}) is unknown ... exiting"
  exit 0 
fi


# +
# execute
# -
write_blue "%% bash $0 --darks=${darks_root} --iso=${tgz_iso} --skyflats=${skyflats_root} --dry-run=${dry_run} --over=ride=${over_ride}"

# dry-run
if [[ ${dry_run} -eq 1 ]]; then
  # write_yellow "Dry-Run> find ${www_dir} -name '*.tgz' -mtime +28 -print -exec rm -f {} \; 2>&1"
  if [[ ${over_ride} -eq 1 ]]; then
    write_yellow "Dry-Run> rm -f ${www_dir}/darks.${tgz_iso}.tgz"
    write_yellow "Dry-Run> rm -f ${www_dir}/skyflats.${tgz_iso}.tgz"
  fi
  write_yellow "Dry-Run> tar -czpvf ${www_dir}/darks.${tgz_iso}.tgz ${_darks_dir}/*.fits >> /dev/null 2>&1"
  write_yellow "Dry-Run> chown ${www_own} ${www_dir}/darks.${tgz_iso}.tgz >> /dev/null 2>&1"
  write_yellow "Dry-Run> tar -czpvf ${www_dir}/skyflats.${tgz_iso}.tgz ${_skyflats_dir}/*.fits >> /dev/null 2>&1"
  write_yellow "Dry-Run> chown ${www_own} ${www_dir}/skyflats.${tgz_iso}.tgz >> /dev/null 2>&1"
  write_yellow "Dry-Run> chown -R ${www_own} ${dna_dir} >> /dev/null 2>&1"

# for-real
else

  # write_green "`date`> find ${www_dir} -name '*.tgz' -mtime +28 -print -exec rm -f {} \; 2>&1"
  # find ${www_dir} -name '*.tgz' -mtime +28 -print -exec rm -f {} \; 2>&1
  if [[ ${over_ride} -eq 1 ]]; then
    write_green "`date`> rm -f ${www_dir}/darks.${tgz_iso}.tgz"
    rm -f ${www_dir}/darks.${tgz_iso}.tgz
    write_green "`date`> rm -f ${www_dir}/skyflats.${tgz_iso}.tgz"
    rm -f ${www_dir}/skyflats.${tgz_iso}.tgz
  fi
  if [[ ! -f ${www_dir}/darks.${tgz_iso}.tgz ]]; then
    write_green "`date`> tar -czpvf ${www_dir}/darks.${tgz_iso}.tgz ${_darks_dir}/*.fits >> /dev/null 2>&1"
    tar -czpvf ${www_dir}/darks.${tgz_iso}.tgz ${_darks_dir}/*.fits >> /dev/null 2>&1
    write_green "`date`> chown ${www_own} ${www_dir}/darks.${tgz_iso}.tgz >> /dev/null 2>&1"
    chown ${www_own} ${www_dir}/darks.${tgz_iso}.tgz >> /dev/null 2>&1
  fi
  if [[ ! -f ${www_dir}/skyflats.${tgz_iso}.tgz ]]; then
    write_green "`date`> tar -czpvf ${www_dir}/skyflats.${tgz_iso}.tgz ${_skyflats_dir}/*.fits >> /dev/null 2>&1"
    tar -czpvf ${www_dir}/skyflats.${tgz_iso}.tgz ${_skyflats_dir}/*.fits >> /dev/null 2>&1
    write_green "`date`> chown ${www_own} ${www_dir}/skyflats.${tgz_iso}.tgz >> /dev/null 2>&1"
    chown ${www_own} ${www_dir}/skyflats.${tgz_iso}.tgz >> /dev/null 2>&1
    write_green "`date`> chown -R ${www_own} ${dna_dir} >> /dev/null 2>&1"
    chown -R ${www_own} ${dna_dir} >> /dev/null 2>&1
  fi
fi


# +
# exit
# -
exit 0
