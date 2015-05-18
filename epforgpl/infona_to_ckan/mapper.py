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

def package_license(p, license_text):
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

    if license_text == u'Ponowne wykorzystywanie udost\u0119pnionej lub przekazanej informacji publicznej wymaga zachowania nast\u0119puj\u0105cych warunk\xf3w:\r\n\u2022informacja publiczna musi zawiera\u0107 wzmiank\u0119 o \u017ar\xf3dle jej pozyskania poprzez podanie pe\u0142nej nazwy Urz\u0119du Komunikacji Elektronicznej lub nazwy skr\xf3conej - UKE;\r\n\u2022nale\u017cy poda\u0107 dat\u0119 wytworzenia oraz pozyskania informacji publicznej;\r\n\u2022pozyskana tre\u015b\u0107 informacji publicznej nie mo\u017ce by\u0107 modyfikowana;\r\n\u2022je\u017celi tre\u015b\u0107 pozyskanej informacji publicznej lub jej fragment, ma stanowi\u0107 cz\u0119\u015b\u0107 ca\u0142o\u015bci, nale\u017cy j\u0105 zamie\u015bci\u0107 w tek\u015bcie w formie cytatu wraz z przypisem informuj\u0105cym o \u017ar\xf3dle pochodzenia lub odpowiedniego dla formy wykorzystania \u2013 oznaczenia podobnego.\r\n\r\nUrz\u0105d Komunikacji Elektronicznej odpowiada za przekazywane informacje publiczne, je\u017celi ich ponowne wykorzystywanie spe\u0142nia wy\u017cej okre\u015blone warunki.':
        pass # TODO

    if license_text == u'Ponowne wykorzystywanie udost\u0119pnionej lub przekazanej informacji publicznej wymaga zachowania nast\u0119puj\u0105cych warunk\xf3w:\r\n\u2022informacja publiczna musi zawiera\u0107 wzmiank\u0119 o \u017ar\xf3dle jej pozyskania poprzez podanie pe\u0142nej nazwy Urz\u0119du Komunikacji Elektronicznej lub nazwy skr\xf3conej - UKE;\r\n\u2022nale\u017cy poda\u0107 dat\u0119 wytworzenia oraz pozyskania informacji publicznej;\r\n\u2022pozyskana tre\u015b\u0107 informacji publicznej nie mo\u017ce by\u0107 modyfikowana;\r\n\u2022je\u017celi tre\u015b\u0107 pozyskanej informacji publicznej lub jej fragment, ma stanowi\u0107 cz\u0119\u015b\u0107 ca\u0142o\u015bci, nale\u017cy j\u0105 zamie\u015bci\u0107 w tek\u015bcie w formie cytatu wraz z przypisem informuj\u0105cym o \u017ar\xf3dle pochodzenia lub odpowiedniego dla formy wykorzystania \u2013 oznaczenia podobnego.\r\n\r\nUrz\u0105d Komunikacji Elektronicznej odpowiada za przekazywane informacje publiczne, je\u017celi ich ponowne wykorzystywanie spe\u0142nia wy\u017cej okre\u015blone warunki.':
        pass # TODO

    if license_text == u'Ponowne wykorzystywanie udost\u0119pnionej lub przekazanej informacji publicznej wymaga zachowania nast\u0119puj\u0105cych warunk\xf3w: \u2022informacja publiczna musi zawiera\u0107 wzmiank\u0119 o \u017ar\xf3dle jej pozyskania poprzez podanie pe\u0142nej nazwy Urz\u0119du Komunikacji Elektronicznej lub nazwy skr\xf3conej - UKE; \u2022nale\u017cy poda\u0107 dat\u0119 wytworzenia oraz pozyskania informacji publicznej; \u2022pozyskana tre\u015b\u0107 informacji publicznej nie mo\u017ce by\u0107 modyfikowana; \u2022je\u017celi tre\u015b\u0107 pozyskanej informacji publicznej lub jej fragment, ma stanowi\u0107 cz\u0119\u015b\u0107 ca\u0142o\u015bci, nale\u017cy j\u0105 zamie\u015bci\u0107 w tek\u015bcie w formie cytatu wraz z przypisem informuj\u0105cym o \u017ar\xf3dle pochodzenia lub odpowiedniego dla formy wykorzystania \u2013 oznaczenia podobnego. Urz\u0105d Komunikacji Elektronicznej odpowiada za przekazywane informacje publiczne, je\u017celi ich ponowne wykorzystywanie spe\u0142nia wy\u017cej okre\u015blone warunki.':
        pass # TODO

    if license_text == u'Podmioty pobieraj\u0105ce t\u0119 informacj\u0119 w celu jej ponownego wykorzystywania s\u0105 zobowi\u0105zane do:\r\n1.\tpoinformowania o \u017ar\xf3dle, czasie wytworzenia i pozyskania informacji publicznej, poprzez podanie pe\u0142nej nazwy Ministerstwa Finans\xf3w lub nazwy skr\xf3conej \u2013 MF;\r\n2.\tniemodyfikowania pozyskanej tre\u015bci informacji publicznej;\r\n3.\tzamieszczenia jej w tre\u015bci w formie cytatu wraz z przypisem informuj\u0105cym o \u017ar\xf3dle pochodzenia (Ministerstwo Finans\xf3w, MF) lub z innym, odpowiednim dla formy wykorzystania oznaczeniem w przypadku przetwarzania pozyskanej informacji publicznej.':
        pass # TODO

    if license_text == u'http://www.uke.gov.pl/ponowne-wykorzystywanie-informacji-publicznej-13718':
        pass # TODO

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
    name = replacepl(name)

    name = re.sub('\\W', '_', name) # Clear other chars
    return name

def replacepl(name):
    pl_map = {
        u"ę": "e",
        u"ś": "s",
        u"ą": 'a',
        u"ż": 'z',
        u'ź': 'z',
        u'ó': 'o',
        u'ć': 'c',
        u'ń': 'n',
        u'ł': 'l',
        u"Ę": "E",
        u"Ś": "S",
        u"Ą": 'A',
        u"Ż": 'Z',
        u'Ź': 'Z',
        u'Ó': 'O',
        u'Ć': 'C',
        u'Ń': 'N',
        u'Ł': 'L',
    }
    for pl, plm in pl_map.iteritems():
        name = re.sub(pl, plm, name)

    return name

def alphanamepl(name):
    name = re.sub('^\s+|[\s\.]+$', '', name.lower()) # Trim
    name = re.sub('/\\W/u', '_', name) # Clear other chars
    
    return name
