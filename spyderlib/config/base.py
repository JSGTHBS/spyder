# -*- coding: utf-8 -*-
#
# Copyright © 2009- The Spyder development Team
# Licensed under the terms of the MIT License
# (see spyderlib/__init__.py for details)

"""
Spyder base configuration management

This file only deals with non-GUI configuration features
(in other words, we won't import any PyQt object here, avoiding any
sip API incompatibility issue in spyderlib's non-gui modules)
"""

from __future__ import print_function

import codecs
import locale
import os.path as osp
import os
import sys

# Local imports
from spyderlib.utils import encoding
from spyderlib.py3compat import (is_unicode, TEXT_TYPES, INT_TYPES, PY3,
                                 to_text_string, is_text_string)


#==============================================================================
# Only for development
#==============================================================================
# To activate/deactivate certain things for development
# SPYDER_DEV is (and *only* has to be) set in bootstrap.py
DEV = os.environ.get('SPYDER_DEV')

# For testing purposes
# SPYDER_TEST can be set using the --test option of bootstrap.py
TEST = os.environ.get('SPYDER_TEST')


#==============================================================================
# Debug helpers
#==============================================================================
# This is needed after restarting and using debug_print
STDOUT = sys.stdout if PY3 else codecs.getwriter('utf-8')(sys.stdout)
STDERR = sys.stderr
def _get_debug_env():
    debug_env = os.environ.get('SPYDER_DEBUG', '')
    if not debug_env.isdigit():
        debug_env = bool(debug_env)
    return int(debug_env)    
DEBUG = _get_debug_env()

def debug_print(*message):
    """Output debug messages to stdout"""
    if DEBUG:
        ss = STDOUT
        if PY3:
            # This is needed after restarting and using debug_print
            for m in message:
                ss.buffer.write(str(m).encode('utf-8'))
            print('', file=ss)
        else:
            print(*message, file=ss)

#==============================================================================
# Configuration paths
#==============================================================================
# Spyder settings dir
# NOTE: During the 2.x.x series this dir was named .spyder2, but
# since 3.0+ we've reverted back to use .spyder to simplify major
# updates in version (required when we change APIs by Linux
# packagers)
if TEST is None:
    SUBFOLDER = '.spyder'
else:
    SUBFOLDER = 'spyder_test'


# We can't have PY2 and PY3 settings in the same dir because:
# 1. This leads to ugly crashes and freezes (e.g. by trying to
#    embed a PY2 interpreter in PY3)
# 2. We need to save the list of installed modules (for code
#    completion) separately for each version
if PY3:
    SUBFOLDER = SUBFOLDER + '-py3'


def get_home_dir():
    """
    Return user home directory
    """
    try:
        # expanduser() returns a raw byte string which needs to be
        # decoded with the codec that the OS is using to represent file paths.
        path = encoding.to_unicode_from_fs(osp.expanduser('~'))
    except:
        path = ''
    for env_var in ('HOME', 'USERPROFILE', 'TMP'):
        if osp.isdir(path):
            break
        # os.environ.get() returns a raw byte string which needs to be
        # decoded with the codec that the OS is using to represent environment
        # variables.
        path = encoding.to_unicode_from_fs(os.environ.get(env_var, ''))
    if path:
        return path
    else:
        raise RuntimeError('Please define environment variable $HOME')


def get_conf_path(filename=None):
    """Return absolute path for configuration file with specified filename"""
    if TEST is None:
        conf_dir = osp.join(get_home_dir(), SUBFOLDER)
    else:
         import tempfile
         conf_dir = osp.join(tempfile.gettempdir(), SUBFOLDER)
    if not osp.isdir(conf_dir):
        os.mkdir(conf_dir)
    if filename is None:
        return conf_dir
    else:
        return osp.join(conf_dir, filename)
        

def get_module_path(modname):
    """Return module *modname* base path"""
    return osp.abspath(osp.dirname(sys.modules[modname].__file__))


def get_module_data_path(modname, relpath=None, attr_name='DATAPATH'):
    """Return module *modname* data path
    Note: relpath is ignored if module has an attribute named *attr_name*
    
    Handles py2exe/cx_Freeze distributions"""
    datapath = getattr(sys.modules[modname], attr_name, '')
    if datapath:
        return datapath
    else:
        datapath = get_module_path(modname)
        parentdir = osp.join(datapath, osp.pardir)
        if osp.isfile(parentdir):
            # Parent directory is not a directory but the 'library.zip' file:
            # this is either a py2exe or a cx_Freeze distribution
            datapath = osp.abspath(osp.join(osp.join(parentdir, osp.pardir),
                                            modname))
        if relpath is not None:
            datapath = osp.abspath(osp.join(datapath, relpath))
        return datapath


def get_module_source_path(modname, basename=None):
    """Return module *modname* source path
    If *basename* is specified, return *modname.basename* path where 
    *modname* is a package containing the module *basename*
    
    *basename* is a filename (not a module name), so it must include the
    file extension: .py or .pyw
    
    Handles py2exe/cx_Freeze distributions"""
    srcpath = get_module_path(modname)
    parentdir = osp.join(srcpath, osp.pardir)
    if osp.isfile(parentdir):
        # Parent directory is not a directory but the 'library.zip' file:
        # this is either a py2exe or a cx_Freeze distribution
        srcpath = osp.abspath(osp.join(osp.join(parentdir, osp.pardir),
                                       modname))
    if basename is not None:
        srcpath = osp.abspath(osp.join(srcpath, basename))
    return srcpath


def is_py2exe_or_cx_Freeze():
    """Return True if this is a py2exe/cx_Freeze distribution of Spyder"""
    return osp.isfile(osp.join(get_module_path('spyderlib'), osp.pardir))


SCIENTIFIC_STARTUP = get_module_source_path('spyderlib',
                                            'scientific_startup.py')


#==============================================================================
# Image path list
#==============================================================================

IMG_PATH = []
def add_image_path(path):
    if not osp.isdir(path):
        return
    global IMG_PATH
    IMG_PATH.append(path)
    for dirpath, dirnames, _filenames in os.walk(path):
        for dirname in dirnames:
            IMG_PATH.append(osp.join(dirpath, dirname))

add_image_path(get_module_data_path('spyderlib', relpath='images'))

from spyderlib.otherplugins import PLUGIN_PATH
if PLUGIN_PATH is not None:
    add_image_path(osp.join(PLUGIN_PATH, 'images'))

def get_image_path(name, default="not_found.png"):
    """Return image absolute path"""
    for img_path in IMG_PATH:
        full_path = osp.join(img_path, name)
        if osp.isfile(full_path):
            return osp.abspath(full_path)
    if default is not None:
        return osp.abspath(osp.join(img_path, default))


#==============================================================================
# Translations
#==============================================================================
LANG_FILE = get_conf_path('langconfig')
DEFAULT_LANGUAGE = 'en'

# This needs to be updated every time a new language is added to spyder, and is
# used by the Preferences configuration to populate the Language QComboBox
LANGUAGE_CODES = {'en': u'English',
                  'fr': u'Français',
                  'es': u'Español',
                  'pt_BR': u'Português'
                  }


def get_available_translations():
    """
    List available translations for spyder based on the folders found in the
    locale folder. This function checks if LANGUAGE_CODES contain the same
    information that is found in the 'locale' folder to ensure that when a new
    language is added, LANGUAGE_CODES is updated.
    """
    locale_path = get_module_data_path("spyderlib", relpath="locale",
                                       attr_name='LOCALEPATH')
    listdir = os.listdir(locale_path)
    langs = [d for d in listdir if osp.isdir(osp.join(locale_path, d))]
    langs = [DEFAULT_LANGUAGE] + langs

    # Check that there is a language code available in case a new translation
    # is added, to ensure LANGUAGE_CODES is updated.
    for lang in langs:
        if lang not in LANGUAGE_CODES:
            error = _('Update LANGUAGE_CODES (inside config/base.py) if a new '
                      'translation has been added to Spyder')
            raise Exception(error)
    return langs


def get_interface_language():
    """
    If Spyder has a translation available for the locale language, it will
    return the version provided by Spyder adjusted for language subdifferences,
    otherwise it will return DEFAULT_LANGUAGE.

    Example:
    1.) Spyder provides ('en',  'fr', 'es' and 'pt_BR'), if the locale is
    either 'en_US' or 'en' or 'en_UK', this function will return 'en'

    2.) Spyder provides ('en',  'fr', 'es' and 'pt_BR'), if the locale is
    either 'pt' or 'pt_BR', this function will return 'pt_BR'
    """
    locale_language = locale.getdefaultlocale()[0]

    language = DEFAULT_LANGUAGE

    if locale_language is not None:
        spyder_languages = get_available_translations()
        for lang in spyder_languages:
            if locale_language == lang:
                language = locale_language
                break
            elif locale_language.startswith(lang) or \
              lang.startswith(locale_language):
                language = lang
                break

    return language


def save_lang_conf(value):
    """Save language setting to language config file"""
    with open(LANG_FILE, 'w') as f:
        f.write(value)


def load_lang_conf():
    """
    Load language setting from language config file if it exists, otherwise
    try to use the local settings if Spyder provides a translation, or
    return the default if no translation provided.
    """
    if osp.isfile(LANG_FILE):
        with open(LANG_FILE, 'r') as f:
            lang = f.read()
    else:
        lang = get_interface_language()
        save_lang_conf(lang)
    return lang


def get_translation(modname, dirname=None):
    """Return translation callback for module *modname*"""
    if dirname is None:
        dirname = modname
    locale_path = get_module_data_path(dirname, relpath="locale",
                                       attr_name='LOCALEPATH')

    # If LANG is defined in ubuntu, a warning message is displayed, so in unix
    # systems we define the LANGUAGE variable.
    language = load_lang_conf()
    if os.name == 'nt':
        os.environ["LANG"] = language      # Works on Windows
    else:
        os.environ["LANGUAGE"] = language  # Works on Linux
 
    import gettext
    try:
        _trans = gettext.translation(modname, locale_path, codeset="utf-8")
        lgettext = _trans.lgettext
        def translate_gettext(x):
            if not PY3 and is_unicode(x):
                x = x.encode("utf-8")
            y = lgettext(x)
            if is_text_string(y) and PY3:
                return y
            else:
                return to_text_string(y, "utf-8")
        return translate_gettext
    except IOError as _e:  # analysis:ignore
        #print "Not using translations (%s)" % _e
        def translate_dumb(x):
            if not is_unicode(x):
                return to_text_string(x, "utf-8")
            return x
        return translate_dumb

# Translation callback
_ = get_translation("spyderlib")


#==============================================================================
# Namespace Browser (Variable Explorer) configuration management
#==============================================================================

def get_supported_types():
    """
    Return a dictionnary containing types lists supported by the 
    namespace browser:
    dict(picklable=picklable_types, editable=editables_types)
         
    See:
    get_remote_data function in spyderlib/widgets/externalshell/monitor.py
    get_internal_shell_filter method in namespacebrowser.py
    
    Note:
    If you update this list, don't forget to update doc/variablexplorer.rst
    """
    from datetime import date
    editable_types = [int, float, complex, list, dict, tuple, date
                      ] + list(TEXT_TYPES) + list(INT_TYPES)
    try:
        from numpy import ndarray, matrix, generic
        editable_types += [ndarray, matrix, generic]
    except ImportError:
        pass
    try:
        from pandas import DataFrame, Series
        editable_types += [DataFrame, Series]
    except ImportError:
        pass
    picklable_types = editable_types[:]
    try:
        from spyderlib.pil_patch import Image
        editable_types.append(Image.Image)
    except ImportError:
        pass
    return dict(picklable=picklable_types, editable=editable_types)

# Variable explorer display / check all elements data types for sequences:
# (when saving the variable explorer contents, check_all is True,
#  see widgets/varexp/namespacebrowser.py:NamespaceBrowser.save_data)
CHECK_ALL = False #XXX: If True, this should take too much to compute...

EXCLUDED_NAMES = ['nan', 'inf', 'infty', 'little_endian', 'colorbar_doc',
                  'typecodes', '__builtins__', '__main__', '__doc__', 'NaN',
                  'Inf', 'Infinity', 'sctypes', 'rcParams', 'rcParamsDefault',
                  'sctypeNA', 'typeNA', 'False_', 'True_',]

#==============================================================================
# Mac application utilities
#==============================================================================

if PY3:
    MAC_APP_NAME = 'Spyder.app'
else:
    MAC_APP_NAME = 'Spyder-Py2.app'

def running_in_mac_app():
    if sys.platform == "darwin" and MAC_APP_NAME in __file__:
        return True
    else:
        return False