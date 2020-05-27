#!/bin/bash


# +
#
# Name:        DNA.sh
# Description: DNA cron control
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
  write_blue   "DNA Cron Control"                                                                                   2>&1
  write_blue   ""                                                                                                   2>&1
  write_green  "Use:"                                                                                               2>&1
  write_green  "  %% bash $0 --ins=<str> --iso=<int> --json=<str> --tel=<str> [--dry-run]"                          2>&1
  write_green  ""                                                                                                   2>&1
  write_yellow "Input(s):"                                                                                          2>&1
  write_yellow "  --ins=<str>,  where <str> is the instrument name,  default=${def_dna_ins}, (choices:${_all_ins})" 2>&1
  write_yellow "  --iso=<int>,  where <int> is the date in YYYYMMDD, default=${def_dna_iso}"                        2>&1
  write_yellow "  --json=<str>, where <str> is the JSON log file,    default=${def_dna_json}"                       2>&1
  write_yellow "  --tel=<str>,  where <str> is the telescope name,   default=${def_dna_tel}, (choices:${_all_tel})" 2>&1
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
[[ -z ${dna_ins} ]]  && dna_ins=${def_dna_ins}
[[ -z ${dna_iso} ]]  && dna_iso=${def_dna_iso}
[[ -z ${dna_json} ]] && dna_json=${def_dna_json}
[[ -z ${dna_tel} ]]  && dna_tel=${def_dna_tel}

[[ ! ${telescopes[${dna_tel}]} == *${dna_ins}* ]] && write_red "<ERROR> ${dna_ins} not supported!" && exit 0
[[ ! ${dna_iso} =~ ^[12][09][0-9]{6}$ ]]          && write_red "<ERROR> ${dna_iso} is invalid!"    && exit 0
[[ -z ${telescopes[${dna_tel}]} ]]                && write_red "<ERROR> ${dna_tel} not supported!" && exit 0


# +
# work function(s)
# -
_fix_ownership () {
  if [[ ${1} -eq 1 ]]; then
    write_yellow "Dry-Run> chown -R artn-eng:users ${2}"
    write_yellow "Dry-Run> chmod -R 775 ${2}"
  else
    write_green "Executing> chown -R artn-eng:users ${2}"
    chown -R artn-eng:users ${2}
    write_green "Executing> chmod -R 775 ${2}"
    chmod -R 775 ${2}
  fi
}

_create_directories () {
  if [[ ${1} -eq 1 ]]; then
    write_yellow "Dry-Run> mkdir -p ${2} ${2}/acquisition ${2}/archive ${2}/bias ${2}/calibration ${2}/dark ${2}/flat ${2}/focus ${2}/object ${2}/queue ${2}/standard ${2}/skyflat ${2}/test ${2}/trash >> /dev/null 2>&1"
  else
    write_green "Executing> mkdir -p ${2} ${2}/acquisition ${2}/archive ${2}/bias ${2}/calibration ${2}/dark ${2}/flat ${2}/focus ${2}/object ${2}/queue ${2}/standard ${2}/skyflat ${2}/test ${2}/trash >> /dev/null 2>&1"
    mkdir -p ${2} ${2}/acquisition ${2}/archive ${2}/bias ${2}/calibration ${2}/dark ${2}/flat ${2}/focus ${2}/object ${2}/queue ${2}/standard ${2}/skyflat ${2}/test ${2}/trash >> /dev/null 2>&1
  fi
}

_create_json () {
  if [[ ${1} -eq 1 ]]; then
    write_yellow "Dry-Run> touch ${2}"
  else
    write_green "Executing> touch ${2}"
    touch ${2}
  fi
}

# +
# execute
# -
write_blue "%% bash $0 --ins=${dna_ins} --iso=${dna_iso} --json=${dna_json} --tel=${dna_tel} --dry-run=${dry_run}"

# create data directory(s)
_create_directories ${dry_run} /rts2data/${dna_tel}/${dna_ins}/${dna_iso}
_create_json        ${dry_run} /rts2data/${dna_tel}/${dna_ins}/${dna_iso}/${dna_json}
_fix_ownership      ${dry_run} /rts2data/${dna_tel}/${dna_ins}/${dna_iso}

# fix code-base
chown -R www-data:www-data /var/www/ARTN-DNA


# +
# exit
# -
exit 0
