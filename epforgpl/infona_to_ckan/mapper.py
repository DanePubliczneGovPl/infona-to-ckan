# encoding: utf-8
'''
Mapping functions
'''
import re

def org_image(name):    
    urls = {
        'Ministerstwo Administracji i Cyfryzacji': 'https://mac.gov.pl/sites/all/themes/global/images/logo.jpg?2',
    }
    url = urls.get(name)

    if not url:
        # Fail softly
        print("Warning: No image url for: '" + name + "'")
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

def package_license(license_text):
    license_text = license_text.strip()
    if license_text == u'bez ogranicze\u0144' or license_text == u'bezogranicze\u0144' or license_text == '':
        return None
    return license_text

# CKAN accepts lowercase alphanumeric+_ characters as some inputs
def alphaname(name):
    pl_map = {
        "ę": "e",
        "ś": "s",
        "ą": 'a',
        "ż": 'z',
        'ź': 'z',
        'ó': 'o',
        'ć': 'c',
        'ń': 'n',
        'ł': 'l'
    }
    name = re.sub('^\s+|[\s\.]+$', '', name.lower()) # Trim
    for pl, plm in pl_map.iteritems():
        name = re.sub(pl, plm, name)

    name = re.sub('\\W', '_', name) # Clear other chars
    return name