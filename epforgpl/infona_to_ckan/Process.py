# coding: utf-8
import config
import mapper as tr

from pymongo import MongoClient
import gridfs
import ckanapi

import uuid, json, re
import io, os, errno


class Bunch(dict):
    def __getattr__(self,name):
        v = self.get(name)
        if type(v) == dict:
            return Bunch(v)
        return v
    __setattr__ = dict.__setitem__
    

class MockEncoder(json.JSONEncoder):
    def default(self, o):
        if type(o) == file:
            return o.name
        
        return json.JSONEncoder.default(self, o)

class ActionMock(object):
    def __getattr__(self, name):       
        def action(**kwargs):
            print name + ': ' + json.dumps(kwargs, cls=MockEncoder) 
        return action

class ActionWrapperDev(object):
    def __init__(self, process):
        self._ckan = process.ckan
        self._process = process
        
    def __getattr__(self, name):
        if name == '_ckan':
            return self._ckan
        if name == '_process':
            return self._process
            
        caction = getattr(self._ckan.action, name)
               
        def action(**kwargs):
            debug_action = name + ': ' + json.dumps(kwargs, cls=MockEncoder) + ' ' + self._ckan.apikey
            print debug_action

            try:
                if config.perform_update and name.endswith('_create') and kwargs.get('id', None) and name != 'organization_member_create' and name != 'member_create':
                    show = getattr(self._ckan.action, name.replace('_create', '_show'))
                    update = getattr(self, name.replace('_create', '_update'))
                    try:
                        show(id=kwargs['id'])
                        if config.update_existing:
                            return update(**kwargs)
                        return None

                    except ckanapi.errors.NotFound:
                        return caction(**kwargs)

                return caction(**kwargs)
            except ckanapi.errors.ValidationError as e:
                if name == 'vocabulary_create' and u'That vocabulary name is already in use.' in e.error_dict.get('name',[]):
                    self._process.warnings.append('Skipping ' + unicode(e))
                elif name == 'package_create' and u'That URL is already in use.' in e.error_dict.get('name',[]):
                    self._process.errors.append(debug_action
                                                + "\n\tURL in use: " + kwargs['url']
                                                + "\n\tdb.informationResource.find({'metadata.webPageUrl': '"+ kwargs['url'] +"'})" )
                else:
                    self._process.errors.append(debug_action + "\n\t" + str(e))

                print str(e)

            except ckanapi.errors.NotFound as e:
                self._process.errors.append(debug_action + "\n\t" + str(e))

                print str(e)

            except ckanapi.errors.CKANAPIError as e:
                print str(e.extra_msg)
                self._process.errors.append(debug_action + "\n\t" + str(e.extra_msg))

        return action
    
class ActionWrapperProduction(object):
    def __init__(self, process):
        self._ckan = process.ckan
        self._process = process
        
    def __getattr__(self, name):
        if name == '_ckan':
            return self._ckan
        if name == '_process':
            return self._process
            
        caction = getattr(self._ckan.action, name)
               
        def action(**kwargs):
            debug_action = name + ': ' + json.dumps(kwargs, cls=MockEncoder) 
            print debug_action
            
            try:
                return caction(**kwargs)
            except (ckanapi.errors.ValidationError, ckanapi.errors.NotFound) as e:
                self._process.errors.append(debug_action + "\n\t" + str(e))

        return action 
 

class Process(object):
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.user_count = 0
        self.organization_count = 0
        self.package_count = 0
        self.resource_count = 0
        self.unprocessed_keys = {} # key -> set(values)
        self.known_keys = set()         
        self.user_names = {}
        self.user_keys = {}
        self.package_id_map = {}
    
    def process(self):
        # connect to Mongo
        client = MongoClient(config.mongo['connection'])
        self.db = client[config.mongo['database']]
        self.grid = gridfs.GridFS(self.db)
        
        # Connect to CKAN
        self.ckan = ckanapi.RemoteCKAN(config.ckan['host'],
            apikey=config.ckan['apikey'],
            user_agent=config.ckan['user_agent'])
        
        self.action = ActionWrapperDev(self)

        self._category()
        self._other_vocabularies()
        self._organization()

        self._user()
        #self._pullUsers()

        self._package()
        self._resource()
        
        print '\nClosing connection to mongo..'
        client.close()
        
        self.summary()
        
    def summary(self):
        if self.warnings:
            print '\n ======== WARNINGS ======='
            for w in set(self.warnings):
                print unicode(w)
        
        if self.unprocessed_keys:
            print '\n ======== UNPROCESSED KEYS ======='
            for key, values in self.unprocessed_keys.iteritems():
                print key
                for v in values:
                    print '\t', v
        
            self.errors.append('Found unprocessed keys')
            
        if self.errors:
            print '\n ======== ERRORS ======='
            for w in self.errors:
                print unicode(w)
                
            print '\nFound ' + str(len(self.errors)) +  ' errors!'        
        else:
            print '\nProcessing was successful!'
            
        print "\n\nPodsumowanie"
        print "Przeniesiono kont użytkowników: ", self.user_count
        print "Przeniesiono profili dostawców: ", self.organization_count
        print "Przeniesiono zbiorów IP: ", self.package_count
        print "Przeniesiono jednostek IP: ", self.resource_count    

    def _category(self):
        print 'Processing categories..'
        # http://docs.ckan.org/en/latest/api/index.html#ckan.logic.action.create.vocabulary_create

        categories = list(self.db.category.find())
        self.categories = map(lambda c: c['_id'], categories)

        category_map = {
            "administracja_publiczna": {
                'title_i18n-pl': u'Administracja Publiczna',
                'title_i18n-en': 'Public Administration',
                'color': '#4b77be',
            },
            "biznes_gospodarka": {
                'title_i18n-pl': u'Biznes i Gospodarka',
                'title_i18n-en': 'Business and Economy',
                'color': '#24485f',
            },
            "budzet_finanse_publiczne": {
                'title_i18n-pl': u'Budżet i Finanse Publiczne',
                'title_i18n-en': 'Budget and Public Finance',
                'color': '#6c7a89',
            },
            "nauka_oswiata": {
                'title_i18n-pl': u'Nauka i Oświata',
                'title_i18n-en': 'Education',
                'color': '#674172',
            },
            "praca_pomoc_spoleczna": {
                'title_i18n-pl': u'Praca i Pomoc Społeczna',
                'title_i18n-en': 'Employment and Social Assistance',
                'color': '#bf3607',
            },
            "rolnictwo": {
                'title_i18n-pl': u'Rolnictwo',
                'title_i18n-en': 'Agriculture',
                'color': '#3a539b',
            },
            "spoleczenstwo": {
                'title_i18n-pl': u'Społeczeństwo',
                'title_i18n-en': 'Society',
                'color': '#d35400',
            },
            "sport_turystyka": {
                'title_i18n-pl': u'Sport i Turystyka',
                'title_i18n-en': 'Sports and Tourism',
                'color': '#2574a9',
            },
            "srodowisko": {
                'title_i18n-pl': u'Środowisko',
                'title_i18n-en': 'Environment',
                'color': '#138435',
            }
        }

        for c in categories:
            cid = c['_id']
            icon_path = os.path.dirname(os.path.realpath(__file__)) + os.sep + 'categories' + os.sep + cid.replace('_','-') + '.png'

            g = {
                'name': cid,
                'id': cid,
                # 'type': 'group',
                'image_upload': open(icon_path),
            }
            g.update(category_map[cid])
        
            self.action.group_create(**g)

    def _other_vocabularies(self):
        print '\nProcessing other vocabularies..'
        
        items = self.db.informationResource.distinct('metadata.updateFrequency')
        self.warnings.append(u"Ensure updateFrequency list is complete: " + unicode(items))


        items = self.db.resourceUnit.distinct('metadata.types')
        items = map(lambda u: {'name': u}, set(items))

        v = {
            'name': 'resource_types',
            'tags': items
        }
        self.action.vocabulary_create(**v)
        
    def _organization(self):
        print '\nProcessing organizations..'
        # http://docs.ckan.org/en/latest/api/index.html#ckan.logic.action.create.organization_create

        self._update_known_keys('publisher', [
            '_id', '_class', 'status', 'metadata', 
            # Skipping fields below
            'createdBy', "creationTimestamp", "indexed", "lastUpdateTimestamp", "lastUpdatedBy", 'version'
            ])
        self._update_known_keys('publisher.metadata', [
            'name', "street", "postalCode", "city",
            "webPage", "contactEmail", "contactPhone", "contactFax", "regon","ePuap",
            # Skip
            "country",
            ])
        
        for pd in self.db.publisher.find():
            p = Bunch(pd)
            self._mark_unknown_keys('publisher', pd)
            if p.metadata.additionalMetadata:
                self._add_unknown_key('publisher.metadata.additionalMetadata', p.metadata.additionalMetadata)

            if p.status == 'DRAFT':
                self.warnings.append(u'Dodaję organizację o statusie DRAFT: ' + unicode(str(p.metadata.name)))

            org = {
                'id': str(p._id),
                'name': tr.alphaname(p.metadata.name),
                'title': p.metadata.name,
                'image_url': self.catch(tr.org_image, p.metadata.name.strip()),
                'state': tr.org_state(p.status),

                'website': p.metadata.webPage,
                'fax': p.metadata.contactFax or (' ' if config.dev else ''),
                'tel': p.metadata.contactPhone,
                'address_street': p.metadata.street,
                'address_city': p.metadata.city,
                'address_postal_code': p.metadata.postalCode,
                'regon': p.metadata.regon or (' ' if config.dev else ''),
                'epuap': p.metadata.ePuap or (' ' if config.dev else ''),
                'email': p.metadata.contactEmail
            }

            if config.dev: # Bo CKAN nie wykryje
                if not p.metadata.contactFax:
                    self.errors.append('Missing fax in ' + org['name'])
                if not p.metadata.regon:
                    self.errors.append('Missing regon in ' + org['name'])
                if not p.metadata.ePuap:
                    self.errors.append('Missing ePuap in ' + org['name'])

            self.action.organization_create(**org)
            self.organization_count += 1

    def _package(self):
        print '\nProcessing packages..'
        # http://docs.ckan.org/en/latest/api/index.html#ckan.logic.action.create.package_create
        
        self._update_known_keys('informationResource', [
            '_id', 'metadata', 'publisherId', 'version', 'status',
            'creationTimestamp', 'lastUpdateTimestamp', 'createdBy', 'lastUpdatedBy',
            # Skipping fields below
            'indexed', '_class', 'metadata._id', 'metadata.additionalMetadata', 'publishedBy', 'publicationDate'
            ])
        self._update_known_keys('informationResource.metadata', [
            'title', 'description', 'webPageUrl', 'updateFrequency', 'licensingInformation',
            'categoryId', 'tags'
            ])                
            
        for ird in self.db.informationResource.find():
            ir = Bunch(ird)
            self._mark_unknown_keys('informationResource', ird)
            if ir.metadata.additionalMetadata:
                self._add_unknown_key('informationResource.metadata.additionalMetadata', ir.metadata.additionalMetadata)
            
            p = {
                'name': tr.alphaname(ir.metadata.title)[:100],
                'owner_org': ir.publisherId,
                'title': ir.metadata.title,
                'notes': ir.metadata.description,
                'version': ir.version,
                'state': tr.ir_state(ir.status),
                'private': tr.private_status(ir.status),
                'url': ir.metadata.webPageUrl,
                'update_frequency': ir.metadata.updateFrequency,
                'category': ir.metadata.categoryId,
                #'groups': [{'id': 'biznes_gospodarka'}]
            }

            try:
                tr.package_license(p, ir.metadata.licensingInformation)
            except tr.MappingException as ex:
                self.warnings.append(unicode(ex) + ' in package ' + unicode(p['name']))

            tags = []
            for t in ir.metadata.tags:
                for tt in t.replace(';', ',').split(','):
                    tt = tt.strip()
                    if tt:
                        tags.append({'name': tt})

            p['tags'] = tags
     
            with api_key(self.ckan, self.user_keys[ir.lastUpdatedBy]):
                try:
                    ret = self.ckan.action.package_show(id=p['name'])
                    p['id'] = ret['id']
                    if config.update_existing:
                        ret = self.action.package_update(**p)

                except ckanapi.errors.NotFound:
                    ret = self.action.package_create(**p)

                if ret:
                    self.package_id_map[str(ir._id)] = ret['id']
     
            self.package_count += 1
            
            #     ckan.action 'package_create', p, (err) ->
            #         if err
            #             if err.match /Dataset id already exists/
            #                 ckan.action 'package_update', p, (err) ->
            #                     if err
            #                         # cb err
            #                         errors.append err
            #                     else
            #                         package_count += 1
            #                     cb null
            #                 return
            #             else
            #                 errors.append err
            #         else
            #             package_count+= 1
            #         cb null
            # 

    def _resource(self):
        print '\nProcessing resources..'
        # http://docs.ckan.org/en/latest/api/index.html#ckan.logic.action.create.resource_create
        
        self._update_known_keys('resourceUnit', [
            '_id', 'informationResourceId', 'status', 'version', 'metadata', 
            'creationTimestamp', 'lastUpdateTimestamp', 'publicationDate',
            'lastUpdatedBy', 'createdBy', 'publishedBy',
            # Skipping fields below
            'indexed', '_class', 'metadata._id', 'metadata.additionalMetadata'
            ])
        self._update_known_keys('resourceUnit.metadata', [
            'title', 'informationResourceId', 'status', 'version',
            'sourceUrl', 'contentSourceClassification', 
            'localFileContentId', 'fileName', 'types',
            # warn
            'licensingInformation', 'resourceLicensingInherit',
            # skip
            'fileType'
            ])
                
        for rud in self.db.resourceUnit.find():
            ru = Bunch(rud)
            self._mark_unknown_keys('resourceUnit', rud)
            if ru.metadata.additionalMetadata:
                self._add_unknown_key('resourceUnit.metadata.additionalMetadata', ru.metadata.additionalMetadata)
            
            r = {
                #'id': str(ru._id),
                'package_id': self.package_id_map.get(ru.informationResourceId, None),
                'state': tr.state_ru(ru.status),
                'name': ru.metadata.title,
                # 'format': ru.metadata.fileType,
                # 'mimetype': self.catch(tr.mimetype, ru.metadata.fileType),
                'created': tr.ts(ru.creationTimestamp),
                'last_modified': tr.ts(ru.lastUpdateTimestamp),
            }
            if ru.metadata.types:
                r['resource_type'] = ','.join(ru.metadata.types)

            if ru.status == 'DRAFT':
                self.warnings.append('WARNING: JIP w CKAN nie ma statusu DRAFT, bedzie widoczny dla wszystkich: ' + ru.metadata.title)

            if ru.metadata.licensingInformation:
                self.warnings.append(u'Pomijam licencję specyficzną dla resource: ' + ru.metadata.licensingInformation)
            
            if ru.metadata.contentSourceClassification == 'UPLOADED':
                if ru.metadata.localFileContentId == None:
                    self.errors.append('Wrong file, mising contentId for ' + str(ru._id))
                    continue

                else:
                    local_path = self._download_file(ru.metadata.localFileContentId, ru.metadata.fileName)
                    r.update({
                        'upload': (tr.replacepl(ru.metadata.fileName), open(local_path, 'rb'))
                    })
            
            elif ru.metadata.contentSourceClassification == 'FROM_REMOTE_URL':
                r.update({
                    'url': ru.metadata.sourceUrl,
                })
            else:
                self._add_unknown_key('resourceUnit.metadata.contentSourceClassification', ru.metadata.contentSourceClassification)
         
            with api_key(self.ckan, self.user_keys[ru.lastUpdatedBy]):            
                self.action.resource_create(**r)
            
            self.resource_count += 1

    def _pullUsers(self):
        for u in self.ckan.action.user_list():
            self.user_names[u['id']] = u['name']
            self.user_keys[u['id']] = u['apikey']
            self.user_count += 1
            
    def _user(self):
        print '\nProcessing users..'
        # http://docs.ckan.org/en/latest/api/index.html#ckan.logic.action.create.user_create
        
        self._update_known_keys('user', [
            '_id', 'email', 'role', 'publisherId', 'status', 'metadata',
            # Skipping fields below
            'editor', 'indexed', '_class', 'metadata._id', 'metadata.additionalMetadata', 'lastUpdatedBy',
            'normalizedEmail', 'password', 'creationTimestamp', 'lastUpdateTimestamp', 'createdBy', 'apiKey',
            'metadata.locale', 'lastPasswordResetTimestamp', 'metadata.highContrast', 'version'
            ])
        self._update_known_keys('user.metadata', [
            'firstName', 'lastName', 'phone', 'office'
            ])                

        userno = 0
        for ud in self.db.user.find():
            userno += 1

            u = Bunch(ud)
            self._mark_unknown_keys('user', ud)
            if u.metadata.additionalMetadata:
                self._add_unknown_key('user.metadata.additionalMetadata', u.metadata.additionalMetadata)

            fullname = tr._((u.metadata.firstName or '') + ' ' + (u.metadata.lastName or '')) or 'Anonim'
            
            name = tr.alphaname(fullname)
            while name in self.user_names.itervalues():
                m = re.match('^(.*?)(\d+)$', name)
                if m:
                    name = m.group(1) + str(int(m.group(2)) + 1)
                else:
                    name = name + '2'
            
            self.user_names[str(u._id)] = name
            
            un = {
                'id': str(u._id),
                'name': name, 
                'email': u.email.lower(),
                'password': str(uuid.uuid4()),
                'fullname': fullname,
                'sysadmin': u.role == 'ROLE_ADMIN',
                'state': tr.user_state(u.status)
            }

            if not u.publisherId and config.dev:
                un.update({
                    'email': 'krzysztof.madejski+anonim' + userno + '@epf.org.pl',
                    'fullname': 'Anonim',
                    'name': 'anonim' + userno
                })

            if u.metadata.office or u.metadata.phone:
                un['about'] = json.dumps({'official_position': u.metadata.office, 'official_phone': u.metadata.phone})

            if u.apiKey:
                self.warnings.append("apiKey set for user " + un['id'])
            
            created = self.action.user_create(**un)
            self.user_keys[str(u._id)] = created['apikey']
            self.user_count += 1

            if u.publisherId:
                # Dostawca
                # http://docs.ckan.org/en/latest/api/index.html#ckan.logic.action.create.organization_member_create
                om = {
                    'id': u.publisherId,
                    'username': un['id'],
                    'role': 'admin'
                };
 
                m = self.action.organization_member_create(**om)

    def catch(self, fun, *args):
        try:
            return fun(*args)
        
        except tr.MappingException as ex:
            self.warnings.append(str(ex))
            return None
    
    def _update_known_keys(self, prefix, arr):
        arr = [prefix + '.' + i for i in arr]
        self.known_keys = self.known_keys.union(arr)
        
    def _mark_unknown_keys(self, prefix, obj):
        for fld in obj:
            key = prefix + '.' + fld
            if not key in self.known_keys:   
                self._add_unknown_key(key, obj[fld])
            
            elif type(obj[fld]) == dict: # recurse into dicts
                self._mark_unknown_keys(key, obj[fld])
                
    def _add_unknown_key(self, key, val):
        for_key = self.unprocessed_keys.get(key, set()).union([unicode(val)])
        if len(for_key) < 10: # Max sample values count                 
            self.unprocessed_keys[key] = for_key
        
    def mkdir_p(self, path):
        try:
            os.makedirs(path)
        except OSError as exc: # Python >2.5
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else: raise
                
    def _download_file(self, localFileContentId, filename):
        local_dir = os.path.join(config.tmp_file_dir, str(localFileContentId), '')
        local_path = os.path.join(local_dir, filename)
        out = self.grid.get(localFileContentId)
        
        if os.path.isfile(local_path) and os.path.getsize(local_path) == out.length:
            out.close()
            return local_path
        elif not os.path.exists(local_dir):
            self.mkdir_p(local_dir)
        
        print '\tDownloading ' + filename + ' ' + str(out.length) + ' bytes'
        with io.open(local_path, 'wb', buffering=100*1024) as file:
            for chunk in out:
                file.write(chunk)
        
        out.close()
        
        return local_path
        
    def hold_apikey(self, apikey):
        self.ckan.apikey = apikey
        
    def release_apikey(self):
        self.ckan.apikey = config.ckan['apikey']
    
class api_key:
    def __init__(self, ckan, apikey):
        self.apikey = apikey 
        self.ckan = ckan 
                   
    def __enter__(self):
        self.old_key = self.ckan.apikey
        self.ckan.apikey = self.apikey        
        return self.ckan
    
    def __exit__(self, type, value, traceback):
        self.ckan.apikey = self.old_key
    
if __name__ == "__main__":
    p = Process()
    p.process()
