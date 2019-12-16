#!/usr/bin/env python3.7


# +
# import(s)
# -
from astropy.io import fits
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# noinspection PyUnresolvedReferences,PyUnresolvedReferences,PyUnresolvedReferences,PyUnresolvedReferences
from src import ARTN_ENCODE_DICT, ARTN_DECODE_DICT, encode_verboten, decode_verboten
# noinspection PyUnresolvedReferences,PyUnresolvedReferences,PyUnresolvedReferences
from src.models.Models import ObsReq, obsreq_filters, User, user_filters

import argparse
import json
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
DNA_ARTN_TGZ_FILES = '/var/www/ARTN-ORP/instance/files'
DNA_COLOR_FORMAT = '%(log_color)s%(asctime)-20s %(levelname)-7s %(filename)-5s line:%(lineno)-5d Message: %(message)s'
DNA_CONSOLE_FORMAT = '%(asctime)-20s %(levelname)-5s %(filename)-7s line:%(lineno)-5d Message: %(message)s'
DNA_ISO_MATCH = re.compile(r'\d{8}')
DNA_LOGFILE_FORMAT = '%(asctime)-20s %(levelname)-5s %(filename)-7s line:%(lineno)-5d Message: %(message)s'
DNA_MAX_BYTES = 9223372036854775807
DNA_MONT4K_SIZES = [
    2880, 11520, 14400, 20480, 49152, 57600, 256000, 358400, 432128, 
    655360, 2206080, 3841920, 3856320, 3859200, 3862080, 3864960, 3867840, 
    7704000, 14904000, 14906880, 14921280
]
DNA_MONT4K_TYPES = ['fit', 'fits', 'FIT', 'FITS']
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
# class: DnaLogger()
# -
class DnaLogger(object):

    # +
    # method: __init__
    # -
    def __init__(self, name=''):

        # variable(s)
        self.name = name
        logname = '{}'.format(self.__name)

        # noinspection PyBroadException
        try:
            logfile = '/var/www/ARTN-DNA/logs/{}.log'.format(logname)
        except Exception:
            logfile = '{}/{}.log'.format(os.getcwd(), logname)
        logconsole = '/tmp/{}.log'.format(logname)

        utils_logger_dictionary = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'DnaColoredFormatter': {
                    '()': 'colorlog.ColoredFormatter',
                    'format': DNA_COLOR_FORMAT,
                    'log_colors': {
                        'DEBUG': 'cyan',
                        'INFO': 'green',
                        'WARNING': 'yellow',
                        'ERROR': 'red',
                        'CRITICAL': 'white,bg_red',
                    }
                },
                'DnaConsoleFormatter': {
                    'format': DNA_CONSOLE_FORMAT
                },
                'DnaFileFormatter': {
                    'format': DNA_LOGFILE_FORMAT
                }
            },

            'handlers': {
                'colored': {
                    'class': 'logging.StreamHandler',
                    'formatter': 'DnaColoredFormatter',
                    'level': 'DEBUG',
                },
                'console': {
                    'class': 'logging.StreamHandler',
                    'formatter': 'DnaConsoleFormatter',
                    'level': 'DEBUG',
                    'stream': 'ext://sys.stdout'
                },
                'file': {
                    'backupCount': 10,
                    'class': 'logging.handlers.RotatingFileHandler',
                    'formatter': 'DnaFileFormatter',
                    'filename': logfile,
                    'level': 'DEBUG',
                    'maxBytes': DNA_MAX_BYTES
                },
                'utils': {
                    'backupCount': 10,
                    'class': 'logging.handlers.RotatingFileHandler',
                    'formatter': 'DnaFileFormatter',
                    'filename': logconsole,
                    'level': 'DEBUG',
                    'maxBytes': DNA_MAX_BYTES
                }
            },

            'loggers': {
                logname: {
                    'handlers': ['colored', 'file', 'utils'],
                    'level': 'DEBUG',
                    'propagate': True
                }
            }
        }

        # configure and get logger
        logging.config.dictConfig(utils_logger_dictionary)
        self.logger = logging.getLogger(logname)

    # +
    # Decorator(s)
    # -
    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, name=''):
        self.__name = name if (isinstance(name, str) and name.strip() != '') else os.getenv('USER')


# +
# variable(s)
# -
dna_log = DnaLogger('ARTN-DNA').logger


# +
# default(s)
# -
def_dna_iso = datetime.now(tz=DNA_TIMEZONE).isoformat().split('T')[0].replace('-', '')
def_dna_fits = f'/data1/artn/rts2images/queue/{def_dna_iso}/C0'
def_dna_json = f'{def_dna_fits}/.dna.json'


# +
# function: dna_artn_ids()
# -
def dna_artn_ids(_fits=''):
    """ returns IDs from FITS headers or None """

    # check input(s)
    _gid, _oid, _tgt, _fits = '', '', '', os.path.abspath(os.path.expanduser(f'{_fits}'))
    if not isinstance(_fits, str) or _fits.strip() == '' or not os.path.exists(f'{_fits}'):
        dna_log.error(f'invalid input, _file={_fits}')
        return _gid, _oid, _tgt

    # noinspection PyBroadException
    try:
        _hdulist = fits.open(f'{_fits}')
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
def dna_connect_database():
    """ connect database """

    # noinspection PyBroadException
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
def dna_disconnect_database(_s=None):
    """ disconnect database """

    # noinspection PyBroadException
    try:
        if _s is not None:
            _s.close()
    except Exception as _e:
        dna_log.error(f'failed to disconnect database, error={_e}')


# +
# function: dna_gmail_close()
# -
def dna_gmail_close(_s=None):
    """ close gmail """

    # noinspection PyBroadException
    try:
        if _s is not None:
            _s.quit()
    except Exception as _e:
        dna_log.error(f'failed to disconnect from gmail, error={_e}')


# +
# function: dna_gmail_open()
# -
def dna_gmail_open():
    """ open gmail """

    # noinspection PyBroadException
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

    # noinspection PyBroadException
    try:
        _tos = ', '.join([_n for _n in _to])
        _body = '\r\n'.join([f'To: {_tos}', f'From: {DNA_GMAIL_USER}', f'Subject: {_subject}', '',  f'{_text}'])
        _s.sendmail(DNA_GMAIL_USER, _to, _body)
    except Exception as _e:
        dna_log.error(f'failed to send gmail, error={_e}')


# +
# function: dna_seek()
# -
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

    # noinspection PyBroadException
    try:
        return {f'{_k}': os.stat(f'{_k}').st_size for _k in _fw if not os.path.islink(f'{_k}') and
                os.path.exists(f'{_k}') and _k.endswith(f'{_type}')}
    except Exception:
        return {}


# +
# function: dna()
# -
def dna(_dna_fits=def_dna_fits, _dna_json=def_dna_json, _dna_iso=def_dna_iso, _gmail=False):
    """ finds data, tarballs it up and send the user a notification on location """

    # entry message
    dna_log.info(f'dna(fits={_dna_fits}, json={_dna_json}, iso={_dna_iso}, gmail={_gmail}) ... entry')

    # check input(s)
    _dna_fits = os.path.abspath(os.path.expanduser(f'{_dna_fits}'))
    if not isinstance(_dna_fits, str) or _dna_fits.strip() == '' or not os.path.isdir(f'{_dna_fits}'):
        dna_log.error(f'invalid input, _dna_fits={_dna_fits}')
        return

    _dna_json = os.path.abspath(os.path.expanduser(f'{_dna_json}'))
    if not isinstance(_dna_json, str) or _dna_json.strip() == '' or not os.path.isfile(f'{_dna_json}'):
        dna_log.error(f'invalid input, _dna_json={_dna_json}')
        return

    if not isinstance(_dna_iso, str) or len(_dna_iso) != 8 or re.match(DNA_ISO_MATCH, _dna_iso) is None:
        dna_log.error(f'invalid input, _dna_iso={_dna_iso}')
        return

    if not isinstance(_gmail, bool):
        _gmail = False

    # +
    # set up
    # -
    dna_log.info(f'finding dark(s) tarballs')
    _dgz = os.path.abspath(os.path.expanduser(f"{os.path.join(DNA_ARTN_TGZ_FILES, f'darks.{_dna_iso}.tgz')}"))
    if os.path.exists(f'{_dgz}'):
        dna_log.info(f'found {_dgz}')

    dna_log.info(f'finding skyflat(s) tarballs')
    _sfgz = os.path.abspath(os.path.expanduser(f"{os.path.join(DNA_ARTN_TGZ_FILES, f'skyflats.{_dna_iso}.tgz')}"))
    if os.path.exists(f'{_sfgz}'):
        dna_log.info(f'found {_sfgz}')

    dna_log.info(f'connecting gmail')
    dna_gs = dna_gmail_open() if _gmail else None

    dna_log.info(f'connecting database')
    dna_db = dna_connect_database()

    # noinspection PyBroadException
    try:
        dna_log.info(f'reading JSON')
        with open(f'{_dna_json}', 'r') as _fr:
            dna_json = list(json.load(_fr))
    except Exception:
        dna_json = []

    # get previously seen _gids
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
    _fits_dictionary = dna_seek(_dna_fits, 'fits')
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

            # if group_id, observation_id or _size is invalid, continue
            _gid, _oid, _tgt = dna_artn_ids(f'{_file}')
            if (isinstance(_gid, str) and _gid.strip() == '') or \
               (isinstance(_oid, str) and _oid.strip() == '') or \
               _size not in DNA_MONT4K_SIZES:
                dna_log.warning(
                    f'invalid headers or size, _file={_file}, _gid={_gid}, _oid={_oid}, _tgt={_tgt}, _size={_size}')
                continue

            # populate dictionary with this file
            if f'{_gid}' not in _gid_dict:
                _gid_dict[f'{_gid}'] = [f'{_file}']
            else:
                _gid_dict[f'{_gid}'].append(f'{_file}')
            dna_log.debug(f'_gid_dict={_gid_dict}')

            # create new entry
            _element = {
                'file': f'{_file}',
                'user': f'',
                'email': f'',
                'gid': f'{_gid}',
                'oid': f'{_oid}',
                'tgt': f'{_tgt}',
                'size': int(_size),
                'timestamp': f"{datetime.fromtimestamp(os.path.getmtime(_file)).isoformat()}"
            }
            dna_log.debug(f'_element={_element}')

            # query obsreq database(s)
            _obsreq = None

            # noinspection PyBroadException
            try:
                _obsreq = dna_db.query(ObsReq)
                _obsreq = obsreq_filters(_obsreq, {'group_id': f'{_gid}', 'observation_id': f'{_oid}'})
            except Exception as _e:
                dna_log.warning(f'failed to query obsreq table, error={_e}')
                continue

            # update record(s)
            for _q in _obsreq.all():

                dna_log.info(f"query obsreq table, _q.username={_q.username},_q.user_id={_q.user_id}")

                # get user/owner
                _element['user'] = _q.username

                # tell user (if desired)
                if len(_gid_dict[f'{_gid}']) == _q.num_exp:

                    # increment counter and save if complete
                    _q.completed = True
                    try:
                        dna_db.commit()
                    except Exception as _e:
                        dna_db.rollback()
                        dna_log.warning(f'failed to commit to obsreq table, error=_{_e}')
                        continue

                    # get user/owner
                    _user = None

                    # noinspection PyBroadException
                    try:
                        _user = dna_db.query(User)
                        _user = user_filters(_user, {'user_id': f'{_q.user_id}', 'username': f'{_q.username}'})
                    except Exception as e:
                        dna_log.warning(f'failed to execute user query, error={e}')
                        continue

                    # gmail user
                    for _u in _user.all():

                        _element['email'] = _u.email

                        # zip all files in this dataset
                        _tgz = os.path.join(f'{DNA_ARTN_TGZ_FILES}', f'{_u.username}.{_dna_iso}.{_q.rts2_id}.tgz')
                        if _gid_dict[f'{_gid}'] is not []:
                            dna_log.info(f'creating archive {_tgz}')
                            with tarfile.open(f'{_tgz}', mode='w:gz') as _wf:
                                for _fz in _gid_dict[f'{_gid}']:
                                    dna_log.info(f'adding {_fz} to {_tgz}')
                                    _wf.add(f'{_fz}')

                        if _gmail:
                            _object_name = decode_verboten(_q.object_name, ARTN_DECODE_DICT)
                            _text = f'Object: {_object_name}\n' \
                                f'Telescope: {_q.telescope}\n' \
                                f'Instrument: {_q.instrument}\n' \
                                f'RA: {_q.ra_hms}\n' \
                                f'Dec: {_q.dec_dms}\n' \
                                f'Filter: {_q.filter_name}\n' \
                                f'ExposureTime: {_q.exp_time}\n' \
                                f'NumberOfExposures: {_q.num_exp}\n' \
                                f'Airmass: {_q.airmass}\n' \
                                f'LunarPhase: {_q.lunarphase}\n' \
                                f'DatabaseID: {_q.id}\n' \
                                f'FITS Data Location:     ' \
                                f'https://scopenet.as.arizona.edu/orp/files/{os.path.basename(_tgz)}\n' \
                                f'FITS Darks Location:    ' \
                                f'https://scopenet.as.arizona.edu/orp/files/{os.path.basename(_dgz)}\n' \
                                f'FITS SkyFlats Location: ' \
                                f'https://scopenet.as.arizona.edu/orp/files/{os.path.basename(_sfgz)}\n' \
                                f'NB: Calibration data may not be available until 08:00 the following day'

                            # noinspection PyBroadException
                            try:
                                dna_log.info(f"sending gmail to {_u.email}, num_exp={_q.num_exp}, "
                                             f"num_taken={len(_gid_dict[f'{_gid}'])}, _text=\n{_text}")
                                dna_gmail_send(dna_gs, [f'{_u.email}', DNA_GMAIL_USER], DNA_GMAIL_USER,
                                               f'ARTN ORP Completed {_object_name}', _text)
                            except Exception as e:
                                dna_log.error(f'failed to send gmail, error={e}')

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
    dna_log.info(f'dna(fits={_dna_fits}, json={_dna_json}, iso={_dna_iso}, gmail={_gmail}) ... exit')


# +
# main()
# -
if __name__ == '__main__':

    # get command line argument(s)
    _p = argparse.ArgumentParser(description=f'ARTN Data Notification Agent',
                                 formatter_class=argparse.RawTextHelpFormatter)
    _p.add_argument(f'--fits', default=f'{def_dna_fits}',
                    help=f"""Data directory <str>, defaults to %(default)s""")
    _p.add_argument(f'--gmail', default=False, action='store_true', help=f'if present, gmail owner')
    _p.add_argument(f'--iso', default=f'{def_dna_iso}',
                    help=f"""ISO date <yyyymmdd>, defaults to %(default)s""")
    _p.add_argument(f'--json', default=f'{def_dna_json}',
                    help=f"""DNA json file <str>, defaults to %(default)s""")
    args = _p.parse_args()

    # execute
    dna(args.fits, args.json, args.iso, bool(args.gmail))
