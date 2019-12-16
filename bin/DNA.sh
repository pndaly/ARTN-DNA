#!/bin/sh


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
def_dna_code="/var/www/ARTN-DNA"
def_dna_iso=$(date +%Y%m%d)
def_dna_json=".dna.json"
def_fits_root="/data1/artn/rts2images/queue"
def_orp_code="/var/www/ARTN-ORP"

dry_run=0
over_ride=0
send_gmail=0


# +
# variable(s)
# -
dna_code="${def_dna_code}"
dna_iso="${def_dna_iso}"
dna_json="${def_dna_json}"
fits_root="${def_fits_root}"
orp_code="${def_orp_code}"


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
    -d*|-D*|--dna*|--DNA*)
      dna_code=$(echo $1 | cut -d'=' -f2)
      shift
      ;;
    -f*|-F*|--fits*|--FITS*)
      fits_root=$(echo $1 | cut -d'=' -f2)
      shift
      ;;
    -g|-G|--gmail|--GMAIL|--send-gmail|--SEND-GMAIL)
      send_gmail=1
      shift
      ;;
    -i*|-I*|--iso*|--ISO*)
      dna_iso=$(echo $1 | cut -d'=' -f2)
      shift
      ;;
    -j*|-J*|--json*|--JSON*)
      dna_json=$(echo $1 | cut -d'=' -f2)
      shift
      ;;
    -n|-N|--dry-run|--DRY-RUN)
      dry_run=1
      shift
      ;;
    -o*|-O*|--orp*|--ORP*)
      orp_code=$(echo $1 | cut -d'=' -f2)
      shift
      ;;
    -x|-X|--over-ride|--OVER-RIDE)
      over_ride=1
      shift
      ;;
    -h*|-H*|--help*|--HELP*|*)
      write_blue "\nDNA Control\n" 2>&1
      write_green "Use:\n %% bash $0 --dna=<str> --fits=<str> --iso=<int> --json=<str> --orp=<str> [--dry-run] [--over-ride] [--send-gmail]\n" 2>&1
      write_yellow "Input(s):" 2>&1
      write_yellow "  --dna=<str>,       -d=<str>  where <str> is DNA code directory,       default=${def_dna_code}" 2>&1
      write_yellow "  --fits=<str>,      -f=<str>  where <str> is data root directory,      default=${def_fits_root}" 2>&1
      write_yellow "  --iso=<int>,       -i=<int>  where <int> is the date in YYYYMMDD,     default=${def_dna_iso}" 2>&1
      write_yellow "  --json=<str>,      -j=<str>  where <str> is the JSON log file,        default=${def_dna_json}" 2>&1
      write_yellow "  --orp=<str>,       -o=<str>  where <str> is ORP code directory,       default=${def_orp_code}" 2>&1
      write_cyan "Flag(s):" 2>&1
      write_cyan "    --dry-run,         -n        show (but do not execute) commands,      default=false" 2>&1
      write_cyan "    --over-ride,       -x        replace existing json log file,          default=false" 2>&1
      write_cyan "    --send-gmail,      -g        send gmail to data owners,               default=false" 2>&1
      exit 0
      ;;
  esac
done


# +
# check and (re)set variable(s)
# -
if [[ ! -d ${dna_code} ]]; then
  write_red "<ERROR> code directory (${dna_code}) is unknown ... exiting"
  exit 0 
fi

case ${dna_iso} in
  [0-9]*)
    ;;
  *)
    dna_iso=${def_dna_iso}
    ;;
esac

if [[ ! -d ${fits_root} ]]; then
  write_red "<ERROR> data directory (${fits_root}) is unknown ... exiting"
  exit 0 
fi

_json_dir=`dirname ${fits_root}/${dna_iso}/C0/${dna_json}`
if [[ ! -e ${_json_dir} ]]; then
  write_red "<ERROR> json directory (${_json_dir}) is unknown ... exiting"
  exit 0 
else
  touch ${_json_dir}/${dna_json}
  chown artn-eng:artn-eng ${_json_dir}/${dna_json}
fi

if [[ ! -d ${orp_code} ]]; then
  write_red "<ERROR> code directory (${orp_code}) is unknown ... exiting"
  exit 0 
fi

# set up
export PYTHONPATH=`pwd`
source ${orp_code}/etc/ARTN.sh ${orp_code}
source ${orp_code}/etc/ORP.sh  ${orp_code}
source ${dna_code}/etc/DNA.sh  ${dna_code}
export PYTHONPATH=${dna_code}/src:${dna_code}:${PYTHONPATH}


# +
# execute
# -
write_blue "%% bash $0 --dna=${dna_code} --fits=${fits_root} --iso=${dna_iso} --json=${dna_json} --orp=${orp_code} --dry-run=${dry_run} --over-ride=${over_ride} --send-gmail=${send_gmail}"

cli_args="--fits=${fits_root}/${dna_iso}/C0 --json=${_json_dir}/${dna_json} --iso=${dna_iso}"
if [[ ${send_gmail} -eq 1 ]]; then
  cli_args="${cli_args} --gmail"
fi

if [[ ${dry_run} -eq 1 ]]; then
  if [[ ${over_ride} -eq 1 ]]; then
    write_yellow "Dry-Run> mv ${_json_dir}/${dna_json} ${_json_dir}/${dna_json}.${today}"
  fi
  write_yellow "Dry-Run> nohup python3.7 ${dna_code}/src/dna.py ${cli_args} >> ${dna_code}/logs/dna.${dna_iso}.log 2>&1 &"
  write_yellow "Dry-Run> touch -t ${dna_iso}0000 ${_json_dir}/${dna_json}"
  write_yellow "Dry-Run> chown -R www-data:www-data ${dna_code}"

else
  if [[ ${over_ride} -eq 1 ]]; then
    write_green "`date`> mv ${_json_dir}/${dna_json} ${_json_dir}/${dna_json}.${today}"
    mv ${_json_dir}/${dna_json} ${_json_dir}/${dna_json}.${today}
  fi
  write_green "`date`> nohup python3.7 ${dna_code}/src/dna.py ${cli_args} >> ${dna_code}/logs/dna.${dna_iso}.log 2>&1 &"
  nohup python3.7 ${dna_code}/src/dna.py ${cli_args} >> ${dna_code}/logs/dna.${dna_iso}.log 2>&1 &
  write_green "`date`> touch -t ${dna_iso}0000 ${_json_dir}/${dna_json}"
  touch -t ${dna_iso}0000 ${_json_dir}/${dna_json}
  write_green "`date`> chown -R www-data:www-data ${dna_code}"
  chown -R www-data:www-data ${dna_code}
fi

# +
# exit
# -
exit 0
