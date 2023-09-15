#!/usr/bin/env python3


# +
# import(s)
# -
from astropy.io import fits
from datetime import datetime
from datetime import timedelta
from PsqlConnection import *
from typing import Any
from typing import Optional

import argparse
import logging
import logging.config
import os
import pytz
import re
import smtplib
import tarfile


# +
# doc string
# -
__doc__ = """python3 kuiper.py --help"""


# +
# constant(s)
# -
DNA_TGZ_DIR = '/var/www/ARTN-ORP/instance/files'
DNA_ISO_MATCH = re.compile(r'\d{8}')
DNA_LOG_CLR_FMT = \
    '%(log_color)s%(asctime)-20s %(levelname)-9s %(filename)-15s line:%(lineno)-5d %(message)s'
DNA_LOG_FIL_FMT = \
    '%(asctime)-20s %(levelname)-9s %(filename)-15s line:%(lineno)-5d %(message)s'
DNA_LOG_LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
DNA_LOG_WWW_DIR = '/var/www/ARTN-DNA/logs'
DNA_LOG_MAX_BYTES = 9223372036854775807
DNA_MONT4K_SIZES = [2880, 11520, 14400, 20480, 49152, 57600, 256000, 358400, 432128, 655360, 2206080, 3841920, 3856320, 3859200, 3862080, 3864960, 3867840, 7704000, 14904000, 14906880, 14921280]
DNA_MONT4K_TYPES = ['fit', 'fits', 'FIT', 'FITS']
DNA_TGZ_OWNER = {'www-data': 33}
DNA_TGZ_GROUP = {'www-data': 33}
DNA_TIMEZONE = pytz.timezone('America/Phoenix')


# +
# get credential(s)
# -
DNA_DB_HOST = os.getenv("DNA_DB_HOST", os.getenv("ARTN_DB_HOST", None))
DNA_DB_NAME = os.getenv("DNA_DB_NAME", os.getenv("ARTN_DB_NAME", None))
DNA_DB_PASS = os.getenv("DNA_DB_PASS", os.getenv("ARTN_DB_PASS", None))
DNA_DB_PORT = os.getenv("DNA_DB_PORT", os.getenv("ARTN_DB_PORT", None))
DNA_DB_USER = os.getenv("DNA_DB_USER", os.getenv("ARTN_DB_USER", None))

DNA_GMAIL_PASS = os.getenv("MAIL_PASSWORD", None)
DNA_GMAIL_PORT = os.getenv("MAIL_PORT", None)
DNA_GMAIL_HOST = os.getenv("MAIL_SERVER", None)
DNA_GMAIL_USER = os.getenv("MAIL_USERNAME", None)


# +
# class: DnaLogger() inherits from the object class
# -
# noinspection PyBroadException
class DnaLogger(object):

    # +
    # method: __init__
    # -
    def __init__(self, name: str = '', level: str = 'DEBUG'):

        # get arguments(s)
        self.name = name
        self.level = level

        # define some variables and initialize them
        self.__msg = None
        self.__logdir = os.getenv("DNA_LOGS", f"{DNA_LOG_WWW_DIR}")
        if not os.path.exists(self.__logdir) or not os.access(self.__logdir, os.W_OK):
            self.__logdir = os.getcwd()
        self.__logfile = f'{self.__logdir}/{self.__name}.log'

        # logger dictionary
        utils_logger_dictionary = {

            # logging version
            'version': 1,

            # do not disable any existing loggers
            'disable_existing_loggers': False,

            # use the same formatter for everything
            'formatters': {
                'DnaColoredFormatter': {
                    '()': 'colorlog.ColoredFormatter', 'format': DNA_LOG_CLR_FMT,
                    'log_colors': {'DEBUG': 'cyan', 'INFO': 'green', 'WARNING': 'yellow',
                        'ERROR': 'red', 'CRITICAL': 'white,bg_red'}},
                'DnaFileFormatter': {'format': DNA_LOG_FIL_FMT}
            },

            # define file and console handlers
            'handlers': {
                'colored': {'class': 'logging.StreamHandler', 'formatter': 'DnaColoredFormatter', 'level': self.__level},
                'file': {'backupCount': 10, 'class': 'logging.handlers.RotatingFileHandler',
                    'formatter': 'DnaFileFormatter', 'filename': self.__logfile, 'level': self.__level,
                    'maxBytes': DNA_LOG_MAX_BYTES},
            },

            # make this logger use file and console handlers
            'loggers': {
                self.__name: {'handlers': ['colored', 'file'], 'level': self.__level, 'propagate': True}}
        }

        # configure logger
        logging.config.dictConfig(utils_logger_dictionary)

        # get logger
        self.logger = logging.getLogger(self.__name)

    # +
    # Decorator(s)
    # -
    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, name: str = ''):
        self.__name = name if name.strip() != '' else os.getenv('USER')

    @property
    def level(self):
        return self.__level

    @level.setter
    def level(self, level: str = ''):
        self.__level = level.upper() if level.upper() in DNA_LOG_LEVELS else DNA_LOG_LEVELS[0]


# +
# variable(s)
# -
dna_log = DnaLogger(name='DNA-Kuiper', level='DEBUG').logger


# +
# default(s)
# -
DEF_DNA_ISO = int(datetime.now(tz=DNA_TIMEZONE).isoformat().split('T')[0].replace('-', ''))
DEF_DNA_PATH = f'/rts2data/Kuiper/Mont4k/{DEF_DNA_ISO}'
DEF_AUTHORIZATION = "artn:********"

# +
# function: dna_gmail_close()
# -
# noinspection PyBroadException
def dna_gmail_close(_s: smtplib.SMTP = None) -> None:
    try:
        _s.quit()
    except Exception as _:
        dna_log.error(f"failed to disconnect from gmail, error='{_}'")


# +
# function: dna_gmail_open()
# -
# noinspection PyBroadException
def dna_gmail_open() -> Optional[smtplib.SMTP]:
    try:
        _s = smtplib.SMTP(DNA_GMAIL_HOST, DNA_GMAIL_PORT)
        _s.ehlo()
        _s.starttls()
        _s.login(DNA_GMAIL_USER, DNA_GMAIL_PASS)
        return _s
    except Exception as _:
        dna_log.error(f"failed to open gmail, error='{_}'")


# +
# function: dna_gmail_send()
# -
# noinspection PyBroadException
def dna_gmail_send(_s: smtplib.SMTP = None, _to: list = None, _from: str = '', _subject: str = '', _text: str = '') -> bool:
    if _s is None or _to is None or _to is [] or _from.strip() == '' or _subject.strip() == '' or _text.strip() == '':
        dna_log.error(f"invalid input(s), _s={_s}, _to={_to}, _from='{_from}', _subject='{_subject}', _text='{_text}'")
        return
    try:
        _tos = ', '.join([_n for _n in _to])
        _body = '\r\n'.join([f'To: {_tos}', f'From: {DNA_GMAIL_USER}', f'Subject: {_subject}', '',  f'{_text}'])
        _s.sendmail(DNA_GMAIL_USER, _to, _body)
        return True
    except Exception as _:
        dna_log.error(f"failed to send gmail, error='{_}'")
        return False


# +
# function: dna_seek()
# -
# noinspection PyBroadException
def dna_seek(_path: str = '', _type: str = '') -> dict:
    # check input(s)
    _path = os.path.abspath(os.path.expanduser(f'{_path}'))
    if not os.path.isdir(f'{_path}') or _type not in DNA_MONT4K_TYPES:
        dna_log.error(f"invalid input(s), _path={_path}, _type='{_type}'")
        return {}
    # generator code (does nothing until called)
    _fw = (
        os.path.join(_root, _file)
        for _root, _dirs, _files in os.walk(os.path.abspath(os.path.expanduser(_path)))
        for _file in _files
    )
    # return results
    try:
        return {f'{_k}': os.stat(f'{_k}').st_size for _k in _fw if not os.path.islink(f'{_k}') and
                'stitched' not in _k and os.path.exists(f'{_k}') and _k.endswith(f'{_type}')}
    except Exception as _:
        dna_log.error(f"dna_seek() failed, error='{_}'")
        return {}


# +
# function: dna_kuiper()
# -
# noinspection PyBroadException
def dna_kuiper(_path: str = DEF_DNA_PATH, _iso: int = DEF_DNA_ISO, _authorization: str = DEF_AUTHORIZATION, _gmail: bool = False) -> None:

    # entry message
    dna_log.info(f"dna(_path='{_path}', _iso={_iso}, _authorization='{_authorization}', _gmail={_gmail})")

    # check input(s)
    _path = os.path.abspath(os.path.expanduser(f'{_path}'))
    if not os.path.isdir(f'{_path}') or _iso < 0:
        dna_log.error(f"invalid input(s), _path={_path}, _iso={_iso}, _authorization='{_authorization}'`")
        return

    # search path
    _data = dna_seek(_path, 'fits')
    if _data is None or _data is {}:
        dna_log.info(f'no files found for processing')
        return

    # create calibration tarball(s)
    darks = [_ for _ in _data if 'dark' in _]
    darks_tgz = os.path.abspath(os.path.expanduser(os.path.join(DNA_TGZ_DIR, f"Kuiper.Mont4k.{_iso}.darks.tgz")))
    if not os.path.isfile(darks_tgz):
        dna_log.info(f'creating {darks_tgz}')
        with tarfile.open(f'{darks_tgz}', mode='w:gz') as _wf:
            for _e in darks:
                dna_log.info(f'adding {_e} to {darks_tgz}')
                _wf.add(f'{_e}')
    os.chown(f'{darks_tgz}', DNA_TGZ_OWNER['www-data'], DNA_TGZ_GROUP['www-data'])

    flats = [_ for _ in _data if 'flat' in _]
    flats_tgz = os.path.abspath(os.path.expanduser(os.path.join(DNA_TGZ_DIR, f"Kuiper.Mont4k.{_iso}.flats.tgz")))
    if not os.path.isfile(flats_tgz):
        dna_log.info(f'creating {flats_tgz}')
        with tarfile.open(f'{flats_tgz}', mode='w:gz') as _wf:
            for _e in flats:
                dna_log.info(f'adding {_e} to {flats_tgz}')
                _wf.add(f'{_e}')
    os.chown(f'{flats_tgz}', DNA_TGZ_OWNER['www-data'], DNA_TGZ_GROUP['www-data'])

    foci = [_ for _ in _data if 'focus' in _]
    foci_tgz = os.path.abspath(os.path.expanduser(os.path.join(DNA_TGZ_DIR, f"Kuiper.Mont4k.{_iso}.foci.tgz")))
    if not os.path.isfile(foci_tgz):
        dna_log.info(f'creating {foci_tgz}')
        with tarfile.open(f'{foci_tgz}', mode='w:gz') as _wf:
            for _e in foci:
                dna_log.info(f'adding {_e} to {foci_tgz}')
                _wf.add(f'{_e}')
    os.chown(f'{foci_tgz}', DNA_TGZ_OWNER['www-data'], DNA_TGZ_GROUP['www-data'])

    # get ARTNOID and OBJECT from fits files
    emails, oids, names, usernames = {}, {}, {}, {}
    objects = [_ for _ in _data if 'object' in _]
    for _i, _e in enumerate(objects):
        dna_log.info(f"processing '{_e}', _i={_i}")
        try:
            _hdulist = fits.open(f'{_e}')
            _oid = f"{_hdulist[0].header['ARTNOID']}"
            _nam = f"{_hdulist[0].header['OBJECT']}"
        except Exception as _e1:
            dna_log.error(f"failed to get fits header, error='{_e1}'")
            continue
        else:
            _hdulist.close()
            dna_log.info(f"processing '{_e}', _i={_i}, _oid='{_oid[:8]}', _nam='{_nam}'")
            if _oid not in oids:
                oids[_oid] = [_e]
            else:
                oids[_oid].append(_e)
            if _oid not in names:
                names[_oid] = _nam

    # connect to database
    _db = None
    try:
        _db = PsqlConnection(database='artn', authorization=_authorization, server='localhost', port=5432)
        _db.connect()
    except Exception as _e2:
        dna_log.error(f"failed to connect to database, error-'{_e2}'")
        return
    else:
        dna_log.debug(f"connected to database OK")

    # from oid, get username of owner
    for _k, _v in oids.items():
        _ans = _db.fetchone(f"SELECT * FROM ObsReq2 WHERE observation_id LIKE '%{_k}%';")
        _username = _ans[0][1]
        if _k not in usernames and _username.strip() != '':
            usernames[_k] = _username.strip()

    # from username get email address
    for _k, _v in usernames.items():
        _ans = _db.fetchone(f"SELECT * FROM Users WHERE username LIKE '%{_v}%';")
        _email = _ans[0][6]
        if _k not in emails and _email.strip() != '':
            emails[_k] = _email.strip()
    _db.disconnect()

    # create observation tarball(s)
    gmails = {}
    for _k, _v in oids.items():
        oid_tgz = os.path.abspath(os.path.expanduser(os.path.join(DNA_TGZ_DIR, f"Kuiper.Mont4k.{_iso}.{usernames[_k]}.{_k[:8]}.tgz")))
        if not os.path.isfile(oid_tgz):
            dna_log.info(f'creating {oid_tgz}')
            with tarfile.open(f'{oid_tgz}', mode='w:gz') as _wf:
                for _e in _v:
                    dna_log.info(f'adding {_e} to {oid_tgz}')
                    _wf.add(f'{_e}')
        gmails = {**gmails, **{_k: {'user': usernames[_k], 'gmail': emails[_k], 'tgz': oid_tgz, 'object': names[_k]}}}
        try:
            os.chown(f'{oid_tgz}', DNA_TGZ_OWNER['www-data'], DNA_TGZ_GROUP['www-data'])
        except Exception as _e3:
            dna_log.error(f"failed to chown {oid_tgz}, error='{_e3}'")

    # send out gmail(s)
    if _gmail:
        for _k, _v in gmails.items():
            _user = f"{_v['user']}"
            _mail = f"{_v['gmail']}"
            _name = f"{_v['object']}"
            _subj = f"{_v['object']}"
            _tgzf = f"{_v['tgz']}"
            _body = f"{_name} observed using the Kuiper telescope on {_iso}.\n" \
                    f"Data link: https://scopenet.as.arizona.edu/orp/files/{os.path.basename(_tgzf)}\n" \
                    f"Dark link: https://scopenet.as.arizona.edu/orp/files/{os.path.basename(darks_tgz)}\n" \
                    f"Flat link: https://scopenet.as.arizona.edu/orp/files/{os.path.basename(flats_tgz)}\n" \
                    f"Foci link: https://scopenet.as.arizona.edu/orp/files/{os.path.basename(foci_tgz)}"
            _text = _body.replace('\n', '')
            try:
                dna_gs = dna_gmail_open()
                dna_log.info(f"sending gmail to {_user} via {_mail} for '{_subj}', text={_text}")
                dna_gmail_send(dna_gs, [_mail, DNA_GMAIL_USER], DNA_GMAIL_USER, f"ARTN ORP Completed {_subj}", _body)
                dna_gmail_close(dna_gs)
            except Exception as _e4:
                dna_log.error(f"failed to send gmail _k={_k}, _v={_v}, error='{_e4}'")
                continue

# +
# main()
# -
if __name__ == '__main__':

    # get command line argument(s)
    _p = argparse.ArgumentParser(description=f'ARTN Data Notification Agent', formatter_class=argparse.RawTextHelpFormatter)
    _p.add_argument(f'-a', f'--authorization', default=DEF_AUTHORIZATION, help=f"""database authorization=<str>:<str>, defaults to '%(default)s'""")
    _p.add_argument(f'--path', default=DEF_DNA_PATH, help=f"""Data path, defaults to '%(default)s'""")
    _p.add_argument(f'--iso', default=DEF_DNA_ISO, help=f"""ISO date, defaults to %(default)s""")
    _p.add_argument(f'--gmail', default=False, action='store_true', help=f'if present, gmail owner')
    _a = _p.parse_args()

    # execute
    try:
        dna_kuiper(_path=_a.path, _iso=_a.iso, _authorization=_a.authorization, _gmail=bool(_a.gmail))
    except Exception as _:
        print(f"{_}\n{__doc__}")
