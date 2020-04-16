#!/bin/bash


# +
#
# Name:        TGZ.sh
# Description: TGZ cron control
# Author:      Phil Daly (pndaly@email.arizona.edu)
# Date:        20190411
# Execute:     % bash TGZ.sh --help
#
# -


# +
# default(s)
# -
today=$(date "+%Y%m%d")

def_tgz_ins="Mont4k"
def_tgz_iso=${today}
def_tgz_tel="Kuiper"

dry_run=0


# +
# supported telescope(s) and instrument(s)
# -
declare -A telescopes
telescopes[Bok]="90Prime BCSpec"
telescopes[Kuiper]="Mont4k"
telescopes[MMT]=BinoSpec
telescopes[Vatt]=Vatt4k

_all_tel=${!telescopes[@]}
_all_ins=${telescopes[@]}


# +
# utility functions
# -
write_blue () {
  printf "\033[0;34m${1}\033[0m\n"
}

write_red () {
  printf "\033[0;31m${1}\033[0m\n"
}

write_yellow () {
  printf "\033[0;33m${1}\033[0m\n"
}

write_green () {
  printf "\033[0;32m${1}\033[0m\n"
}

write_cyan () {
  printf "\033[0;36m${1}\033[0m\n"
}

write_magenta () {
  printf "\033[0;35m${1}\033[0m\n"
}

usage () {
  write_blue   ""                                                                                                   2>&1
  write_blue   "TGZ Cron Control"                                                                                   2>&1
  write_blue   ""                                                                                                   2>&1
  write_green  "Use:"                                                                                               2>&1
  write_green  "  %% bash $0 --ins=<str> --iso=<int> --tel=<str> [--dry-run]"                                       2>&1
  write_green  ""                                                                                                   2>&1
  write_yellow "Input(s):"                                                                                          2>&1
  write_yellow "  --ins=<str>,  where <str> is the instrument name,  default=${def_tgz_ins}, (choices:${_all_ins})" 2>&1
  write_yellow "  --iso=<int>,  where <int> is the date in YYYYMMDD, default=${def_tgz_iso}"                        2>&1
  write_yellow "  --tel=<str>,  where <str> is the telescope name,   default=${def_tgz_tel}, (choices:${_all_tel})" 2>&1
  write_yellow ""                                                                                                   2>&1
  write_cyan   "Flag(s):"                                                                                           2>&1
  write_cyan   "  --dry-run,    show (but do not execute) commands,  default=false"                                 2>&1
  write_cyan   ""                                                                                                   2>&1
}


# +
# get command line argument(s) 
# -
while test $# -gt 0; do
  case "${1}" in
    --ins*)
      tgz_ins=$(echo $1 | cut -d'=' -f2)
      shift
      ;;
    --iso*)
      tgz_iso=$(echo $1 | cut -d'=' -f2)
      shift
      ;;
    --tel*)
      tgz_tel=$(echo $1 | cut -d'=' -f2)
      shift
      ;;
    --dry-run)
      dry_run=1
      shift
      ;;
    --help*|*)
      usage
      exit 0
      ;;
  esac
done


# +
# check and (re)set variable(s)
# -
[[ -z ${tgz_ins} ]] && tgz_ins=${def_tgz_ins}
[[ -z ${tgz_iso} ]] && tgz_iso=${def_tgz_iso}
[[ -z ${tgz_tel} ]] && tgz_tel=${def_tgz_tel}

[[ ! ${telescopes[${tgz_tel}]} == *${tgz_ins}* ]] && write_red "<ERROR> ${tgz_ins} not supported!" && exit 0
[[ ! ${tgz_iso} =~ ^[12][09][0-9]{6}$ ]]          && write_red "<ERROR> ${tgz_iso} is invalid!"    && exit 0
[[ -z ${telescopes[${tgz_tel}]} ]]                && write_red "<ERROR> ${tgz_tel} not supported!" && exit 0


# +
# work function(s)
# -
_tar_files () {
  # $1 = dry run, $2 = directory, $3 = type
  _tel=$(echo ${2} | cut -d'/' -f3)
  _ins=$(echo ${2} | cut -d'/' -f4)
  _iso=$(echo ${2} | cut -d'/' -f5)
  _typ=$(echo ${2} | cut -d'/' -f6)
  if [[ ${1} -eq 1 ]]; then
    if [[ -d ${2} ]]; then
      _f=$(find ${2} -name "*.fits" -print)
      if [[ ! -z ${_f} ]]; then
        write_yellow "Dry-Run> rm -f /var/www/ARTN-ORP/instance/files/${_tel}.${_ins}.${_iso}.${_typ}.tgz >> /dev/null 2>&1"
        write_yellow "Dry-Run> tar -czpvf /var/www/ARTN-ORP/instance/files/${_tel}.${_ins}.${_iso}.${_typ}.tgz ${2}/*.fits >> /dev/null 2>&1"
        write_yellow "Dry-Run> chown www-data:www-data /var/www/ARTN-ORP/instance/files/${_tel}.${_ins}.${_iso}.${_typ}.tgz"
        write_yellow "Dry-Run> chmod 775 /var/www/ARTN-ORP/instance/files/${_tel}.${_ins}.${_iso}.${_typ}.tgz"
      fi
    fi
  else
    if [[ -d ${2} ]]; then
      _f=$(find ${2} -name "*.fits" -print)
      if [[ ! -z ${_f} ]]; then
        write_green "`date`> rm -f /var/www/ARTN-ORP/instance/files/${_tel}.${_ins}.${_iso}.${_typ}.tgz >> /dev/null 2>&1"
        rm -f /var/www/ARTN-ORP/instance/files/${_tel}.${_ins}.${_iso}.${_typ}.tgz >> /dev/null 2>&1
        write_green "`date`> tar -czpvf /var/www/ARTN-ORP/instance/files/${_tel}.${_ins}.${_iso}.${_typ}.tgz ${2}/*.fits >> /dev/null 2>&1"
        tar -czpvf /var/www/ARTN-ORP/instance/files/${_tel}.${_ins}.${_iso}.${_typ}.tgz ${2}/*.fits >> /dev/null 2>&1
        write_green "`date`> chown www-data:www-data /var/www/ARTN-ORP/instance/files/${_tel}.${_ins}.${_iso}.${_typ}.tgz"
        chown www-data:www-data /var/www/ARTN-ORP/instance/files/${_tel}.${_ins}.${_iso}.${_typ}.tgz
        write_green "`date`> chmod 775 /var/www/ARTN-ORP/instance/files/${_tel}.${_ins}.${_iso}.${_typ}.tgz"
        chmod 775 /var/www/ARTN-ORP/instance/files/${_tel}.${_ins}.${_iso}.${_typ}.tgz
      fi
    fi
  fi
}


# +
# execute
# -
write_blue "%% bash $0 --ins=${tgz_ins} --iso=${tgz_iso} --tel=${tgz_tel} --dry-run=${dry_run}"

# create data directory(s)
_tar_files ${dry_run} /rts2data/${tgz_tel}/${tgz_ins}/${tgz_iso}/bias
_tar_files ${dry_run} /rts2data/${tgz_tel}/${tgz_ins}/${tgz_iso}/calibration
_tar_files ${dry_run} /rts2data/${tgz_tel}/${tgz_ins}/${tgz_iso}/dark
_tar_files ${dry_run} /rts2data/${tgz_tel}/${tgz_ins}/${tgz_iso}/flat
_tar_files ${dry_run} /rts2data/${tgz_tel}/${tgz_ins}/${tgz_iso}/focus
_tar_files ${dry_run} /rts2data/${tgz_tel}/${tgz_ins}/${tgz_iso}/skyflat
_tar_files ${dry_run} /rts2data/${tgz_tel}/${tgz_ins}/${tgz_iso}/standard

# fix code-base
chown -R www-data:www-data /var/www/ARTN-DNA


# +
# exit
# -
exit 0
