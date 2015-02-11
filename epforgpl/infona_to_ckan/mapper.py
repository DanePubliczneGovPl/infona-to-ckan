# encoding: utf-8
'''
Mapping functions
'''
import re

class MappingException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

def mimetype(ext):
    mimes = {
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'xls':'application/vnd.ms-excel',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'doc':'application/msword',
        'zip': 'application/zip',        
        'ods':'application/vnd.oasis.opendocument.spreadsheet',
        'html':'text/html',
        'pdf':'application/pdf',
        '7z': 'application/x-7z-compressed',
        "rtf": 'application/rtf',
        "txt": 'text/plain',
        "csv": 'text/csv',
        "jpg": 'image/jpeg',
        'jpeg': 'image/jpeg'
    }
    mime = mimes.get(ext)
    
    if not mime:
        # Fail softly 
        raise MappingException("No mimetype defined for: " + ext)
    return mime

def org_image(name):    
    urls = {
        'Ministerstwo Administracji i Cyfryzacji': 'https://mac.gov.pl/sites/all/themes/global/images/logo.jpg?2',
    }
    url = urls.get(name)

    if not url:
        # Fail softly
        raise MappingException("Warning: No image url for: '" + name + "'")
    return url

def user_state(infona):
    if infona == 'ACTIVE':
        return 'active'
    elif infona == 'INACTIVE':
        return 'deleted'
    else:
        raise ("Unknown user/org status: " + infona)
org_state = user_state

def state_ru(status):
    statuses = {
        'PUBLISHED': 'active',
        'DRAFT': 'active',
        'DELETED': 'deleted'
    }
    state = statuses.get(status)

    if not state:
        raise "Unknown ru/ir status: '" + status + "'"
    return state
ir_state = state_ru

def private_status(status):
    statuses = {
        'PUBLISHED': False,
        'DRAFT': True,
        'DELETED': False
    }
    priv = statuses.get(status)

    if priv == None:
        raise "Unknown status: " + status
    return priv

# translate timestamp
def ts(ts):
    # TODO check timezone
    if type(ts) == str:
        return re.sub('\s+', 'T', ts)
    return ts.strftime('%Y-%m-%dT%H:%M:%S')

def _(text):
    text = text.strip()
    if text == '':
        return None 
    return text

def package_license(p, license_text, errors):
    license_text = license_text.strip()
    if license_text in [u"Bez ograniczeń", u"bez ograniczeń ", u"bez ograniczeń", u"bezograniczeń"] or not license_text:
        return

    if license_text in [u"Dane mogą być wykorzystane z powołaniem się na źródło",
        u"Dane można wykorzystać z podaniem źródła.",
        u"Dane są możliwe do wykorzystania z powołaniem się na źródło.",
        u"Dane są możliwe do wykorzystania z powołaniem się na źródło",
        u"Dane możliwe do wykorzystania z powołaniem się na źródło",
        u"Dane można wykorzystać powołując się na źródło.",
        u"Dane mogą być wykorzystane z podaniem źródła.",
        u"Dane mogą być wykorzystane z podaniem źródła.",
        u"Dane mogą być wykorzystane z podaniem źródła",
        u"Bez ograniczeń, pod warunkiem podania źródła informacji",
        u"Bez ograniczeń pod warunkiem podania źródła informacji"]:
        p['license_condition_source'] = True
        return

    raise MappingException("Untranslated reuse restrictions: " + license_text)

# CKAN accepts lowercase alphanumeric+_ characters as some inputs
def alphaname(name):
    pl_map = {
        u"ę": "e",
        u"ś": "s",
        u"ą": 'a',
        u"ż": 'z',
        u'ź': 'z',
        u'ó': 'o',
        u'ć': 'c',
        u'ń': 'n',
        u'ł': 'l'
    }
    name = re.sub('^\s+|[\s\.]+$', '', name.lower()) # Trim
    for pl, plm in pl_map.iteritems():
        name = re.sub(pl, plm, name)

    name = re.sub('\\W', '_', name) # Clear other chars
    return name

def alphanamepl(name):
    name = re.sub('^\s+|[\s\.]+$', '', name.lower()) # Trim
    name = re.sub('\\W', '_', name) # Clear other chars
    
    return name
