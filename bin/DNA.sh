#!/bin/bash


# +
#
# Name:        DNA.sh
# Description: DNA control
# Author:      Phil Daly (pndaly@email.arizona.edu)
# Date:        20190411
# Execute:     % bash DNA.sh --help
#
# -


# +
# default(s)
# -
today=$(date "+%Y%m%d")

def_dna_ins="Mont4k"
def_dna_iso=${today}
def_dna_json=".dna.json"
def_dna_tel="Kuiper"

def_dna_home="/var/www/ARTN-DNA"
def_orp_home="/var/www/ARTN-ORP"

dry_run=0
over_ride=0
send_gmail=0


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
  write_blue   ""                                                                                                                               2>&1
  write_blue   "DNA Control"                                                                                                                    2>&1
  write_blue   ""                                                                                                                               2>&1
  write_green  "Use:"                                                                                                                           2>&1
  write_green  "  %% bash $0 --ins=<str> --iso=<int> --json=<str> --tel=<str> --dna=<str> --orp=<str> [--dry-run] [--over-ride] [--send-gmail]" 2>&1
  write_green  ""                                                                                                                               2>&1
  write_yellow "Input(s):"                                                                                                                      2>&1
  write_yellow "  --ins=<str>,  where <str> is the instrument name,  default=${def_dna_ins}, (choices:${_all_ins})"                             2>&1
  write_yellow "  --iso=<int>,  where <int> is the date in YYYYMMDD, default=${def_dna_iso}"                                                    2>&1
  write_yellow "  --json=<str>, where <str> is the JSON log file,    default=${def_dna_json}"                                                   2>&1
  write_yellow "  --tel=<str>,  where <str> is the telescope name,   default=${def_dna_tel}, (choices:${_all_tel})"                             2>&1
  write_yellow "  --dna=<str>,  where <str> is DNA code directory,   default=${def_dna_home}"                                                   2>&1
  write_yellow "  --orp=<str>,  where <str> is ORP code directory,   default=${def_orp_home}"                                                   2>&1
  write_yellow ""                                                                                                                               2>&1
  write_cyan   "Flag(s):"                                                                                                                       2>&1
  write_cyan   "  --dry-run,    show (but do not execute) commands,  default=false"                                                             2>&1
  write_cyan   "  --over-ride,  replace existing json log file,      default=false"                                                             2>&1
  write_cyan   "  --send-gmail, send gmail to data owners,           default=false"                                                             2>&1
  write_cyan   ""                                                                                                                               2>&1
}


# +
# get command line argument(s) 
# -
while test $# -gt 0; do
  case "${1}" in
    --ins*)
      dna_ins=$(echo $1 | cut -d'=' -f2)
      shift
      ;;
    --iso*)
      dna_iso=$(echo $1 | cut -d'=' -f2)
      shift
      ;;
    --json*)
      dna_json=$(echo $1 | cut -d'=' -f2)
      shift
      ;;
    --tel*)
      dna_tel=$(echo $1 | cut -d'=' -f2)
      shift
      ;;
    --dna*)
      dna_home=$(echo $1 | cut -d'=' -f2)
      shift
      ;;
    --orp*)
      orp_home=$(echo $1 | cut -d'=' -f2)
      shift
      ;;
    --dry-run)
      dry_run=1
      shift
      ;;
    --gmail|--send-gmail)
      send_gmail=1
      shift
      ;;
    --over-ride)
      over_ride=1
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
[[ -z ${dna_ins} ]]  && dna_ins=${def_dna_ins}
[[ -z ${dna_iso} ]]  && dna_iso=${def_dna_iso}
[[ -z ${dna_json} ]] && dna_json=${def_dna_json}
[[ -z ${dna_tel} ]]  && dna_tel=${def_dna_tel}
[[ -z ${dna_home} ]] && dna_home=${def_dna_home}
[[ -z ${orp_home} ]] && orp_home=${def_orp_home}
[[ ! ${telescopes[${dna_tel}]} == *${dna_ins}* ]] && write_red "<ERROR> ${dna_ins} not supported!" && exit 0
[[ ! ${dna_iso} =~ ^[12][09][0-9]{6}$ ]] && write_red "<ERROR> ${dna_iso} is invalid!" && exit 0
[[ -z ${telescopes[${dna_tel}]} ]] && write_red "<ERROR> ${dna_tel} not supported!" && exit 0
[[ ! -d ${dna_home} ]] && write_red "<ERROR> directory (${dna_home}) is invalid!" && exit 0
[[ ! -d ${orp_home} ]] && write_red "<ERROR> directory (${orp_home}) is invalid!" && exit 0

data_dir=$(echo "/rts2data/${dna_tel}/${dna_ins}/${dna_iso}")
[[ ! -d ${data_dir} ]] && write_red "<ERROR> directory (${data_dir}) is invalid!" && exit 0


# set up
export PYTHONPATH=`pwd`
source ${orp_home}/etc/ARTN.sh ${orp_home}
source ${orp_home}/etc/ORP.sh  ${orp_home}
source ${dna_home}/etc/DNA.sh  ${dna_home}
export PYTHONPATH=${dna_home}/src:${dna_home}:${PYTHONPATH}


# +
# execute
# -
write_blue "%% bash $0 --ins=${dna_ins} --iso=${dna_iso} --json=${dna_json} --tel=${dna_tel} --dna=${dna_home} --orp=${orp_home} --dry-run=${dry_run} --over-ride=${over_ride} --send-gmail=${send_gmail}"

cli_args="--data=${data_dir} --json=${data_dir}/${dna_json} --iso=${dna_iso} --telescope=${dna_tel} --instrument=${dna_ins}"
if [[ ${send_gmail} -eq 1 ]]; then
  cli_args="${cli_args} --gmail"
fi

if [[ ${dry_run} -eq 1 ]]; then
  write_yellow "Dry-Run> touch ${data_dir}/${dna_json}"
  write_yellow "Dry-Run> chown artn-eng:users ${data_dir}/${dna_json}"
else
  write_green "`date`> touch ${data_dir}/${dna_json}"
  touch ${data_dir}/${dna_json}
  write_green "`date`> chown artn-eng:users ${data_dir}/${dna_json}"
  chown artn-eng:users ${data_dir}/${dna_json}
fi

if [[ ${dry_run} -eq 1 ]]; then
  if [[ ${over_ride} -eq 1 ]]; then
    write_yellow "Dry-Run> mv ${data_dir}/${dna_json} ${data_dir}/${dna_json}.${today}"
  fi
else
  if [[ ${over_ride} -eq 1 ]]; then
    write_green "`date`> mv ${data_dir}/${dna_json} ${data_dir}/${dna_json}.${today}"
    mv ${data_dir}/${dna_json} ${data_dir}/${dna_json}.${today}
  fi
fi

if [[ ${dry_run} -eq 1 ]]; then
  write_yellow "Dry-Run> nohup python3.7 ${dna_home}/src/dna.py ${cli_args} >> ${dna_home}/logs/dna.${dna_iso}.log 2>&1 &"
else
  write_green "`date`> nohup python3.7 ${dna_home}/src/dna.py ${cli_args} >> ${dna_home}/logs/dna.${dna_iso}.log 2>&1 &"
  nohup python3.7 ${dna_home}/src/dna.py ${cli_args} >> ${dna_home}/logs/dna.${dna_iso}.log 2>&1 &
fi

if [[ ${dry_run} -eq 1 ]]; then
  write_yellow "Dry-Run> touch -t ${dna_iso}0000 ${data_dir}/${dna_json}"
  write_yellow "Dry-Run> chown -R www-data:www-data ${dna_home}"
else
  write_green "`date`> touch -t ${dna_iso}0000 ${data_dir}/${dna_json}"
  touch -t ${dna_iso}0000 ${data_dir}/${dna_json}
  write_green "`date`> chown -R www-data:www-data ${dna_home}"
  chown -R www-data:www-data ${dna_home}
fi

# +
# exit
# -
exit 0
