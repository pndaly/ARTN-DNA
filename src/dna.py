#!/usr/bin/env python3.7


# +
# import(s)
# -
from astropy.io import fits
from datetime import datetime
from datetime import timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# noinspection PyUnresolvedReferences,PyUnresolvedReferences,PyUnresolvedReferences,PyUnresolvedReferences
from src import ARTN_ZERO_ISO, ARTN_ZERO_MJD, ARTN_ENCODE_DICT, ARTN_DECODE_DICT
# noinspection PyUnresolvedReferences,PyUnresolvedReferences,PyUnresolvedReferences,PyUnresolvedReferences
from src import encode_verboten, decode_verboten, get_iso
# noinspection PyUnresolvedReferences,PyUnresolvedReferences,PyUnresolvedReferences
from src.models.Models import ObsReq, obsreq_filters, User, user_filters

import argparse
import json
import itertools
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
__doc__ = """
    % python3.7 dna.py --help
"""


# +
# constant(s)
# -
DNA_TGZ_DIR = '/var/www/ARTN-ORP/instance/files'
DNA_ISO_MATCH = re.compile(r'\d{8}')
DNA_LOG_CLR_FMT = \
    '%(log_color)s%(asctime)-20s %(levelname)-9s %(filename)-15s %(funcName)-15s line:%(lineno)-5d Message: %(message)s'
DNA_LOG_CSL_FMT = \
    '%(asctime)-20s %(levelname)-9s %(filename)-15s %(funcName)-15s line:%(lineno)-5d Message: %(message)s'
DNA_LOG_FIL_FMT = \
    '%(asctime)-20s %(levelname)-9s %(filename)-15s %(funcName)-15s line:%(lineno)-5d Message: %(message)s'
DNA_LOG_LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
DNA_LOG_WWW_DIR = '/var/www/ARTN-DNA/logs'
DNA_LOG_MAX_BYTES = 9223372036854775807
DNA_MONT4K_SIZES = [
    2880, 11520, 14400, 20480, 49152, 57600, 256000, 358400, 432128, 
    655360, 2206080, 3841920, 3856320, 3859200, 3862080, 3864960, 3867840, 
    7704000, 14904000, 14906880, 14921280
]
DNA_MONT4K_TYPES = ['fit', 'fits', 'FIT', 'FITS']
DNA_TGZ_OWNER = {'www-data': 33}
DNA_TGZ_GROUP = {'www-data': 33}
DNA_TIMEZONE = pytz.timezone('America/Phoenix')


# +
# dictionary(s)
# -
SUPPORTED = {
    'Bok': ['90Prime', 'BCSpec'],
    'Kuiper': ['Mont4k'],
    'MMT': ['BinoSpec'],
    'Vatt': ['Vatt4k']
}
TELESCOPES = [_k for _k in SUPPORTED]
INSTRUMENTS = list(itertools.chain.from_iterable([_v for _k, _v in SUPPORTED.items()]))


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
    def __init__(self, name='', level='DEBUG'):

        # get arguments(s)
        self.name = name
        self.level = level

        # define some variables and initialize them
        self.__msg = None
        self.__logconsole = f'/tmp/console-{self.__name}.log'
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
                    '()': 'colorlog.ColoredFormatter',
                    'format': DNA_LOG_CLR_FMT,
                    'log_colors': {
                        'DEBUG': 'cyan',
                        'INFO': 'green',
                        'WARNING': 'yellow',
                        'ERROR': 'red',
                        'CRITICAL': 'white,bg_red',
                    }
                },
                'DnaConsoleFormatter': {
                    'format': DNA_LOG_CSL_FMT
                },
                'DnaFileFormatter': {
                    'format': DNA_LOG_FIL_FMT
                }
            },

            # define file and console handlers
            'handlers': {
                'colored': {
                    'class': 'logging.StreamHandler',
                    'formatter': 'DnaColoredFormatter',
                    'level': self.__level,
                },
                'console': {
                    'class': 'logging.StreamHandler',
                    'formatter': 'DnaConsoleFormatter',
                    'level': self.__level,
                    'stream': 'ext://sys.stdout'
                },
                'file': {
                    'backupCount': 10,
                    'class': 'logging.handlers.RotatingFileHandler',
                    'formatter': 'DnaFileFormatter',
                    'filename': self.__logfile,
                    'level': self.__level,
                    'maxBytes': DNA_LOG_MAX_BYTES
                },
                'utils': {
                    'backupCount': 10,
                    'class': 'logging.handlers.RotatingFileHandler',
                    'formatter': 'DnaFileFormatter',
                    'filename': self.__logconsole,
                    'level': self.__level,
                    'maxBytes': DNA_LOG_MAX_BYTES
                }
            },

            # make this logger use file and console handlers
            'loggers': {
                self.__name: {
                    'handlers': ['colored', 'file', 'utils'],
                    'level': self.__level,
                    'propagate': True
                }
            }
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
    def name(self, name=''):
        self.__name = name if (isinstance(name, str) and name.strip() != '') else os.getenv('USER')

    @property
    def level(self):
        return self.__level

    @level.setter
    def level(self, level=''):
        self.__level = level.upper() if \
            (isinstance(level, str) and level.strip() != '' and level.upper() in DNA_LOG_LEVELS) else DNA_LOG_LEVELS[0]

# +
# variable(s)
# -
dna_log = DnaLogger('ARTN-DNA').logger


# +
# default(s)
# -
def_dna_iso = datetime.now(tz=DNA_TIMEZONE).isoformat().split('T')[0].replace('-', '')
def_dna_ins = f'Mont4k'
def_dna_dir = f'/rts2data/Kuiper/Mont4k/{def_dna_iso}/object'
def_dna_json = f'/rts2data/Kuiper/Mont4k/{def_dna_iso}/.dna.json'
def_dna_obj = f''
def_dna_tel = f'Kuiper'
def_dna_user = f''


# +
# function: dna_artn_ids()
# -
# noinspection PyBroadException
def dna_artn_ids(_file=''):
    """ returns IDs from FITS headers """
    # check input(s)
    _gid, _oid, _tgt, _file = '', '', '', os.path.abspath(os.path.expanduser(f'{_file}'))
    if not isinstance(_file, str) or _file.strip() == '' or not os.path.exists(f'{_file}'):
        dna_log.error(f'invalid input, _file={_file}')
        return _gid, _oid, _tgt
    # get header(s)
    try:
        _hdulist = fits.open(f'{_file}')
        _gid = f"{_hdulist[0].header['ARTNGID']}"
        _oid = f"{_hdulist[0].header['ARTNOID']}"
        _tgt = f"{_hdulist[0].header['TARGET']}"
        _hdulist.close()
    except Exception as _e:
        dna_log.error(f'failed to get fits header(s), error={_e}')
    # return
    return _gid, _oid, _tgt


# +
# function: dna_connect_database()
# -
# noinspection PyBroadException
def dna_connect_database():
    """ return database session """
    try:
        engine = create_engine(
            f'postgresql+psycopg2://{DNA_DB_USER}:{DNA_DB_PASS}@{DNA_DB_HOST}:{DNA_DB_PORT}/{DNA_DB_NAME}')
        get_session = sessionmaker(bind=engine)
        return get_session()
    except Exception as _e:
        dna_log.error('failed to connect database, error={_e}')
        return None


# +
# function: dna_disconnect_database()
# -
# noinspection PyBroadException
def dna_disconnect_database(_s=None):
    """ disconnect database session """
    try:
        if _s is not None:
            _s.close()
    except Exception as _e:
        dna_log.error(f'failed to disconnect database, error={_e}')


# +
# function: dna_gmail_close()
# -
# noinspection PyBroadException
def dna_gmail_close(_s=None):
    """ close gmail """
    try:
        if _s is not None:
            _s.quit()
    except Exception as _e:
        dna_log.error(f'failed to disconnect from gmail, error={_e}')


# +
# function: dna_gmail_open()
# -
# noinspection PyBroadException
def dna_gmail_open():
    """ open gmail """
    try:
        _s = smtplib.SMTP(DNA_GMAIL_HOST, DNA_GMAIL_PORT)
        _s.ehlo()
        _s.starttls()
        _s.login(DNA_GMAIL_USER, DNA_GMAIL_PASS)
        return _s
    except Exception as _e:
        dna_log.error(f'failed to open gmail, error={_e}')
        return None


# +
# function: dna_gmail_send()
# -
# noinspection PyBroadException
def dna_gmail_send(_s=None, _to=None, _from='', _subject='', _text=''):
    """ send gmail """
    # check input(s)
    if _s is None:
        dna_log.error(f'invalid input, _s={_s}')
        return
    if not isinstance(_to, list) or _to is None or _to is []:
        dna_log.error(f'invalid input, _to={_to}')
        return
    if not isinstance(_from, str) or _from.strip() == '':
        dna_log.error(f'invalid input, _from={_from}')
        return
    if not isinstance(_subject, str) or _from.strip() == '':
        dna_log.error(f'invalid input, _subject={_subject}')
        return
    if not isinstance(_text, str) or _text.strip() == '':
        dna_log.error(f'invalid input, _text={_text}')
        return
    # send gmail
    try:
        _tos = ', '.join([_n for _n in _to])
        _body = '\r\n'.join([f'To: {_tos}', f'From: {DNA_GMAIL_USER}', f'Subject: {_subject}', '',  f'{_text}'])
        _s.sendmail(DNA_GMAIL_USER, _to, _body)
    except Exception as _e:
        dna_log.error(f'failed to send gmail, error={_e}')


# +
# function: dna_seek()
# -
# noinspection PyBroadException
def dna_seek(_path='', _type=''):
    """ returns dictionary of {filename: size} for given type in path or {} """
    # check input(s)
    _path = os.path.abspath(os.path.expanduser(f'{_path}'))
    if not isinstance(_path, str) or _path.strip() == '' or not os.path.isdir(f'{_path}'):
        dna_log.error(f'invalid input, _path={_path}')
        return {}
    if not isinstance(_type, str) or _type.strip() == '' or _type not in DNA_MONT4K_TYPES:
        dna_log.error(f'invalid input, _type={_type}')
        return {}
    # (clever) generator code (does nothing until called)
    _fw = (
        os.path.join(_root, _file)
        for _root, _dirs, _files in os.walk(os.path.abspath(os.path.expanduser(_path)))
        for _file in _files
    )
    # return dictionary of results
    try:
        return {f'{_k}': os.stat(f'{_k}').st_size for _k in _fw if not os.path.islink(f'{_k}') and
                os.path.exists(f'{_k}') and _k.endswith(f'{_type}')}
    except Exception:
        return {}


# +
# function: dna()
# -
# noinspection PyBroadException
def dna(_dna_dir=def_dna_dir, _dna_ins=def_dna_ins, _dna_iso=def_dna_iso, _dna_json=def_dna_json, 
        _dna_obj=def_dna_obj, _dna_tel=def_dna_tel, _dna_user=def_dna_user, _gmail=False):
    """ finds data, tarballs it up and send the user a notification on location """

    # entry message
    dna_log.info(f'dna(data={_dna_dir}, json={_dna_json}, instrument={_dna_ins}, iso={_dna_iso}, '
                 f'object={_dna_obj}, telescope={_dna_tel}, user={_dna_user}, gmail={_gmail}) ... entry')

    # check input(s)
    _dna_dir = os.path.abspath(os.path.expanduser(f'{_dna_dir}'))
    if not isinstance(_dna_dir, str) or _dna_dir.strip() == '' or not os.path.isdir(f'{_dna_dir}'):
        dna_log.error(f'invalid input, _dna_dir={_dna_dir}')
        return
    else:
        dna_log.info(f'valid input, _dna_dir={_dna_dir}')

    if not isinstance(_dna_ins, str) or _dna_ins.strip() == '' or _dna_ins not in INSTRUMENTS:
        dna_log.error(f'invalid input, _dna_ins={_dna_ins}')
        return
    else:
        dna_log.info(f'valid input, _dna_ins={_dna_ins}')

    if not isinstance(_dna_iso, str) or len(_dna_iso) != 8 or re.match(DNA_ISO_MATCH, _dna_iso) is None:
        dna_log.error(f'invalid input, _dna_iso={_dna_iso}')
        return
    else:
        dna_log.info(f'valid input, _dna_iso={_dna_iso}')

    _dna_json = os.path.abspath(os.path.expanduser(f'{_dna_json}'))
    if not isinstance(_dna_json, str) or _dna_json.strip() == '' or not os.path.isfile(f'{_dna_json}'):
        dna_log.error(f'invalid input, _dna_json={_dna_json}')
        return
    else:
        dna_log.info(f'valid input, _dna_json={_dna_json}')

    if not isinstance(_dna_obj, str):
        dna_log.error(f'invalid input, _dna_obj={_dna_obj}')
        return
    else:
        dna_log.info(f'valid input, _dna_obj={_dna_obj}')

    if not isinstance(_dna_tel, str) or _dna_tel.strip() == '' or _dna_tel not in TELESCOPES:
        dna_log.error(f'invalid input, _dna_tel={_dna_tel}')
        return
    else:
        dna_log.info(f'valid input, _dna_tel={_dna_tel}')

    if not isinstance(_dna_user, str):
        dna_log.error(f'invalid input, _dna_user={_dna_user}')
        return
    else:
        dna_log.info(f'valid input, _dna_user={_dna_user}')

    if f'{_dna_ins}' not in SUPPORTED[f'{_dna_tel}']:
        dna_log.error(f'invalid combination, _dna_ins={_dna_ins}, _dna_tel={_dna_tel}')
        return
    else:
        dna_log.info(f'valid combination, _dna_ins={_dna_ins}, _dna_tel={_dna_tel}')

    if not isinstance(_gmail, bool):
        _gmail = False

    # +
    # set up
    # -
    _tgzs = {
        # new
        'bias': os.path.abspath(
            os.path.expanduser(os.path.join(DNA_TGZ_DIR, f'{_dna_tel}.{_dna_ins}.{_dna_iso}.bias.tgz'))),
        'calibration': os.path.abspath(
            os.path.expanduser(os.path.join(DNA_TGZ_DIR, f'{_dna_tel}.{_dna_ins}.{_dna_iso}.calibration.tgz'))),
        'dark': os.path.abspath(
            os.path.expanduser(os.path.join(DNA_TGZ_DIR, f'{_dna_tel}.{_dna_ins}.{_dna_iso}.dark.tgz'))),
        'flat': os.path.abspath(
            os.path.expanduser(os.path.join(DNA_TGZ_DIR, f'{_dna_tel}.{_dna_ins}.{_dna_iso}.flat.tgz'))),
        'focus': os.path.abspath(
            os.path.expanduser(os.path.join(DNA_TGZ_DIR, f'{_dna_tel}.{_dna_ins}.{_dna_iso}.focus.tgz'))),
        'skyflat': os.path.abspath(
            os.path.expanduser(os.path.join(DNA_TGZ_DIR, f'{_dna_tel}.{_dna_ins}.{_dna_iso}.skyflat.tgz'))),
        'standard': os.path.abspath(
            os.path.expanduser(os.path.join(DNA_TGZ_DIR, f'{_dna_tel}.{_dna_ins}.{_dna_iso}.standard.tgz'))),
        # legacy
        'darks': os.path.abspath(os.path.expanduser(os.path.join(DNA_TGZ_DIR, f'darks.{_dna_iso}.tgz'))),
        'skyflats': os.path.abspath(os.path.expanduser(os.path.join(DNA_TGZ_DIR, f'skyflats.{_dna_iso}.tgz')))
    }
    dna_log.info(f'_tgzs={_tgzs}')
    
    dna_log.info(f'connecting gmail')
    dna_gs = dna_gmail_open() if _gmail else None

    dna_log.info(f'connecting database')
    dna_db = dna_connect_database()

    try:
        dna_log.info(f'reading JSON')
        with open(f'{_dna_json}', 'r') as _fr:
            dna_json = list(json.load(_fr))
    except Exception:
        dna_json = []

    dna_log.info(f'loading previous GIDs and OIDs')
    _gid_dict = {}
    for _e in dna_json:
        if 'gid' in _e:
            if _e['gid'] not in _gid_dict:
                _gid_dict[_e['gid']] = [f"{_e['file']}"]
            else:
                _gid_dict[_e['gid']].append(f"{_e['file']}")

    # +
    # process
    # -
    _fits_dictionary = dna_seek(_dna_dir, 'fits')
    if _fits_dictionary is None or _fits_dictionary is {}:
        dna_log.info(f'no files found for processing')

    else:
        dna_log.info(f'found {len(_fits_dictionary)} files for processing')

        # process keyword-value pair(s)
        for _file, _size in _fits_dictionary.items():

            # if we have already processed this file, continue
            _already_processed = True if [_f for _f in dna_json if _file in _f['file']] != [] else False
            if _already_processed:
                dna_log.warning(f'already processed {_file}')
                continue
            else:
                dna_log.info(f'processing {_file}')

            # find observation type from directory structure
            _obstype = os.path.basename(os.path.dirname(_file)).lower()
            _user = ''
            _email = ''

            # if group_id, observation_id or _size is invalid, continue
            if _obstype == 'object':
                _gid, _oid, _tgt = dna_artn_ids(f'{_file}')
                if (isinstance(_gid, str) and _gid.strip() == '') or \
                   (isinstance(_oid, str) and _oid.strip() == '') or \
                   _size not in DNA_MONT4K_SIZES:
                    dna_log.error(f'invalid headers or size, _file={_file}, _gid={_gid}, '
                                  f'_oid={_oid}, _tgt={_tgt}, _size={_size}')
                    continue
            else:
                _gid = f"{os.path.basename(_file).replace('-', '').replace('.', '').lower()}gid"
                _oid = f"{os.path.basename(_file).replace('-', '').replace('.', '').lower()}oid"
                _tgt = _obstype
                _user = 'rts2'
                _email = 'rts2.operator@gmail.com'

            # populate dictionary with this file
            if f'{_gid}' not in _gid_dict:
                _gid_dict[f'{_gid}'] = [f'{_file}']
            else:
                _gid_dict[f'{_gid}'].append(f'{_file}')
            dna_log.debug(f'_gid_dict={_gid_dict}')

            # create new entry
            _element = {
                'file': f'{_file}',
                'user': f'{_user}',
                'email': f'{_email}',
                'gid': f'{_gid}',
                'oid': f'{_oid}',
                'tgt': f'{_tgt}',
                'size': int(_size),
                'timestamp': f"{datetime.fromtimestamp(os.path.getmtime(_file)).isoformat()}"
            }
            dna_log.debug(f'_element={_element}')

            # query obsreq database(s)
            _obsreq = None
            try:
                _obsreq = dna_db.query(ObsReq)
                _obsreq = obsreq_filters(_obsreq, {'group_id': f'{_gid}', 'observation_id': f'{_oid}'})
            except Exception as _e:
                dna_log.warning(f'failed to query obsreq table, error={_e}')
            else:
                # update record(s)
                for _q in _obsreq.all():

                    dna_log.info(f"query obsreq table, _q.username={_q.username},_q.user_id={_q.user_id}")

                    # get user/owner
                    _element['user'] = _q.username

                    # tell user (if desired)
                    if len(_gid_dict[f'{_gid}']) == _q.num_exp:

                        # increment counter and save if complete
                        _q.completed = True
                        _iso = get_iso()
                        _q.completed_iso = _iso
                        _q.completed_mjd = mjd_to_iso(_iso)
                        try:
                            dna_db.commit()
                        except Exception as _e:
                            dna_db.rollback()
                            dna_log.error(f'failed to commit to obsreq table, error=_{_e}')
                            continue

                        # get user/owner
                        _user = None
                        try:
                            _user = dna_db.query(User)
                            _user = user_filters(_user, {'user_id': f'{_q.user_id}', 'username': f'{_q.username}'})
                        except Exception as e:
                            dna_log.error(f'failed to execute user query, error={e}')
                            continue

                        # gmail user
                        for _u in _user.all():

                            _element['email'] = _u.email

                            # gzip all files in this dataset
                            _tgz = os.path.abspath(
                                os.path.expanduser(
                                    os.path.join(DNA_TGZ_DIR,
                                                 f'{_dna_tel}.{_dna_ins}.{_dna_iso}.{_u.username}.{_q.rts2_id}.tgz')))
                            if _gid_dict[f'{_gid}'] is not []:
                                dna_log.info(f'creating archive {_tgz}')
                                with tarfile.open(f'{_tgz}', mode='w:gz') as _wf:
                                    for _fz in _gid_dict[f'{_gid}']:
                                        dna_log.info(f'adding {_fz} to {_tgz}')
                                        _wf.add(f'{_fz}')

                            # change ownership
                            if os.path.exists(_tgz):
                                try:
                                    os.chown(f'{_tgz}', DNA_TGZ_OWNER['www-data'], DNA_TGZ_GROUP['www-data'])
                                except Exception as _f:
                                    dna_log.error(f'failed to chown {_tgz}')

                            if _gmail:
                                _object_name = decode_verboten(_q.object_name, ARTN_DECODE_DICT)
                                _txt = f'{_object_name} observed using the {_q.telescope} telescope with ' \
                                       f'{_q.instrument}\nRA: {_q.ra_hms}  Dec: {_q.dec_dms}  Epoch: J2000\n' \
                                       f'{_q.num_exp} x {_q.exp_time}s exposures, in the {_q.filter_name} filter, ' \
                                       f'at airmass {_q.airmass}\nData archive: ' \
                                       f'https://scopenet.as.arizona.edu/orp/files/{os.path.basename(_tgz)}\n' \
                                       f'NB: Calibration data may not be available until 08:00 ' \
                                       f'the following day (or at all!)\n'
                                for _k, _v in _tgzs.items():
                                    if os.path.exists(f'{_v}'):
                                        _txt += f'{_k[0].upper()}{_k[1:]} archive: ' \
                                                f'https://scopenet.as.arizona.edu/orp/files/{os.path.basename(_v)}\n'
                                _txt = _txt[:-1]

                                try:
                                    dna_log.info(f"sending gmail to {_q.username} ({_u.email}), "
                                                 f"object='{_object_name}', _txt='{_txt}'")
                                    # notify specific user of all object(s) observed
                                    if _dna_user != '' and _dna_obj == '':
                                        if _dna_user.lower() in _u.email.lower():
                                            dna_gmail_send(dna_gs, [f'{_u.email}', DNA_GMAIL_USER], DNA_GMAIL_USER,
                                                           f'ARTN ORP Completed {_object_name}', _txt)
                                    # notify all user(s) of specific object(s) observed
                                    elif _dna_user == '' and _dna_obj != '':
                                        if _dna_obj.lower() in _object_name.lower():
                                            dna_gmail_send(dna_gs, [f'{_u.email}', DNA_GMAIL_USER], DNA_GMAIL_USER,
                                                           f'ARTN ORP Completed {_object_name}', _txt)
                                    # notify specific user of specific object(s) observed
                                    elif _dna_user != '' and _dna_obj != '':
                                        if _dna_user.lower() in _u.email.lower() and \
                                                _dna_obj.lower() in _object_name.lower():
                                            dna_gmail_send(dna_gs, [f'{_u.email}', DNA_GMAIL_USER], DNA_GMAIL_USER,
                                                           f'ARTN ORP Completed {_object_name}', _txt)
                                    # notify all user(s) of all object(s) observed
                                    else:
                                        dna_gmail_send(dna_gs, [f'{_u.email}', DNA_GMAIL_USER], DNA_GMAIL_USER,
                                                       f'ARTN ORP Completed {_object_name}', _txt)
                                except Exception as e:
                                    dna_log.error(f'failed to send gmail, error={e}')
            finally:
                # add it to the json data structure
                if all(_k in _element for _k in ('file', 'size', 'gid', 'oid', 'tgt', 'email', 'user', 'timestamp')):
                    dna_log.info(f'processed {_element}')
                    dna_json.append(_element)
                else:
                    dna_log.warning(f'missing keys in dna json, keys={_element.keys()}')

    # +
    # shut down
    # -
    dna_log.info(f'writing JSON')
    with open(f'{_dna_json}', 'w') as _fw:
        json.dump(dna_json, _fw)

    dna_log.info(f'disconnect database')
    if dna_db:
        dna_disconnect_database(dna_db)

    dna_log.info(f'disconnect gmail')
    if _gmail and dna_gs:
        dna_gmail_close(dna_gs)

    # exit message
    dna_log.info(f'dna(data={_dna_dir}, json={_dna_json}, instrument={_dna_ins}, iso={_dna_iso}, '
                 f'object={_dna_obj}, telescope={_dna_tel}, user={_dna_user}, gmail={_gmail}) ... exit')


# +
# main()
# -
if __name__ == '__main__':

    # get command line argument(s)
    # noinspection PyTypeChecker
    _p = argparse.ArgumentParser(description=f'ARTN Data Notification Agent',
                                 formatter_class=argparse.RawTextHelpFormatter)
    _p.add_argument(f'--data', default=f'{def_dna_dir}',
                    help=f"""Data directory <str>, defaults to %(default)s""")
    _p.add_argument(f'--instrument', default=f'{def_dna_ins}',
                    help=f"""Instrument <str>, defaults to '%(default)s', choices: {INSTRUMENTS}""")
    _p.add_argument(f'--iso', default=f'{def_dna_iso}',
                    help=f"""ISO date <yyyymmdd>, defaults to %(default)s""")
    _p.add_argument(f'--json', default=f'{def_dna_json}',
                    help=f"""DNA json file <str>, defaults to %(default)s""")
    _p.add_argument(f'--object', default=f'{def_dna_obj}',
                    help=f"""Object name <str>, defaults to '%(default)s'""")
    _p.add_argument(f'--telescope', default=f'{def_dna_tel}',
                    help=f"""Telescope <str>, defaults to '%(default)s', choices: {TELESCOPES}""")
    _p.add_argument(f'--user', default=f'{def_dna_user}',
                    help=f"""User <str>, defaults to '%(default)s'""")
    _p.add_argument(f'--gmail', default=False, action='store_true', help=f'if present, gmail owner')
    args = _p.parse_args()

    # execute
    dna(args.data, args.instrument, args.iso, args.json, args.object, args.telescope, args.user, bool(args.gmail))
