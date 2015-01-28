# encoding: utf-8
import config
import mapper as tr
import uuid, json
from pymongo import MongoClient
import ckanapi

class Bunch(dict):
    def __getattr__(self,name):
        v = self.get(name)
        if type(v) == dict:
            return Bunch(v)
        return v
    __setattr__ = dict.__setitem__

class ActionMock(object):
    def __getattr__(self, name):
        def action(**kwargs):
            print name + ': ' + json.dumps(kwargs) 
        return action 
        # TODO catch error
        # TODO invoke self.ckan.action

class Process(object):
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.user_count = 0
        self.organization_count = 0
        self.package_count = 0
        self.resource_count = 0
        self.action = ActionMock()         
    
    def process(self):
        # connect to Mongo
        client = MongoClient(config.mongo['connection'])
        self.db = client[config.mongo['database']]
        
        # Connect to CKAN
        self.ckan = ckanapi.RemoteCKAN(config.ckan['host'],
            apikey=config.ckan['apikey'],
            user_agent=config.ckan['user_agent'])
        
        self._category()
        self._other_vocabularies()
        self._organization()
        self._package()
        self._resource()
        self._user()

        print '\nClosing connection to mongo..'
        client.close()
        
        self.summary()
        
    def summary(self):
        if self.warnings:
            print ' ======== WARNINGS ======='
            for w in self.warnings:
                print w
                
        if self.errors:
            print ' ======== WARNINGS ======='
            for w in self.warnings:
                print w
                
            print 'Found errors!'        
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
        
        categories = self.db.category.find() 

        # TODO add categories as new objects with translation
        #    db_category = {
        #        _id: true,
        #        name: true,
        #        localizedName: {pl: true, en: true}
        #    }
         
        v = {
            'name': 'categories3',
            'tags': map(lambda c: {'name': c['_id']}, categories)
        }
        
        self.action.vocabulary_create(**v)

    def _other_vocabularies(self):
        print '\nProcessing other vocabularies..'
        
        items = self.db.informationResource.distinct('metadata.updateFrequency')

        v = {
            'name': 'update_frequencies',
            'tags': map(lambda u: {'name': tr.alphaname(u)}, items )
        }
        
        self.action.vocabulary_create(**v)
        
    def _organization(self):
        print '\nProcessing organizations..'
        # http://docs.ckan.org/en/latest/api/index.html#ckan.logic.action.create.organization_create
        
        for p in self.db.publisher.find():
            p = Bunch(p)                
            org = {
                'id': str(p._id),
                'name': tr.alphaname(p.metadata.name),
                'title': p.metadata.name,
                'image_url': tr.org_image(p.metadata.name.strip()),
                'state': tr.org_state(p.status)
            }
    
            #    //TODO p.metadata. czy tego wymaga ustawa?
            #    // place, street, postalCode, city, country,
            #    // webPage, contactEmail, contactPhone, contactFax,
            #    // regon, ePuap
            
            self.action.organization_create(**org)
            self.organization_count += 1
        
    def _package(self):
        print '\nProcessing packages..'
        # http://docs.ckan.org/en/latest/api/index.html#ckan.logic.action.create.package_create
            
        for ir in self.db.informationResource.find():
            ir = Bunch(ir)
            p = {
                'id': str(ir._id),
                'name': tr.alphaname(ir.metadata.title),
                'owner_org': ir.publisherId,
                'title': ir.metadata.title,
                'notes': ir.metadata.description,
                #author: ir.publishedBy, TODO nie ma jeszcze userów
                #maintainer: ir.lastUpdateBy, // TODO nie ma userów
                'version': ir.version,
                'state': tr.ir_state(ir.status),
                'private': tr.private_status(ir.status),
                'url': ir.metadata.webPageUrl,
                'update_frequency': tr.alphaname(ir.metadata.updateFrequency),
                'license_restrictions': tr.package_license(ir.metadata.licensingInformation),
                'category': ir.metadata.categoryId
            }
            
            p['tags'] = map(lambda t: {'name': tr.alphaname(t)}, ir.metadata.tags)
    
            #    // TODO lastUpdateTimestamp
            #    // TODO lastUpdateBy
            #    // TODO publicationDate
            #    // TODO creationDate
            #    // TODO creationBy
            #
     
            self.action.package_create(**p)
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
        
        for ru in self.db.resourceUnit.find():
            ru = Bunch(ru)
            if ru.metadata.contentSourceClassification == 'UPLOADED':
                continue # TODO
                        
            r = {
                'id': str(ru._id),
                'package_id': ru.informationResourceId,
                'state': tr.state_ru(ru.status),
                'revision_id': ru.version,
                'name': ru.metadata.title,
         
        #        // ru.metadata.fileType, {"xlsx","xls","html","zip","pdf","ods","doc","docx","7z","rtf","txt","csv","jpg"
                'url': ru.metadata.sourceUrl,
        #        // ru.metadata.contentSourceClassification // TODO FROM_REMOTE_URL or UPLOADED
        #        // upload: FieldStorage??
        #        // size:
        #        // resource_type:
        #        // mimetype:
         
                # FROM_REMOTE_URL
                # types
                # sourceUrl
                # fileType
         
                # UPLOADED:
                # types: ['raport', 'tabela', 'tekst' ]
                # filename: bla.xlsx
                # fileType
                # localFileContentId
         
                'created': tr.ts(ru.creationTimestamp),
                'last_modified': tr.ts(ru.lastUpdateTimestamp) # TODO check timezone in ckan
            }
         
            if ru.status == 'DRAFT':
                self.warnings.append('WARNING: JIP w CKAN nie ma statusu DRAFT, bedzie widoczny dla wszystkich: ' + ru.metadata.title)
            #
            #    // TODO lastUpdateBy
            #    // TODO publicationDate
            #    // TODO publicationBy
            #    // TODO creationBy

            self.action.resource_create(**r)
            self.resource_count += 1
            
    def _user(self):
        print '\nProcessing users..'
        # http://docs.ckan.org/en/latest/api/index.html#ckan.logic.action.create.user_create
        
        for u in self.db.user.find():
            u = Bunch(u)
            un = {
                'id': str(u._id),
                'name': str(u._id), # TODO login with email
                'email': u.email,
                'password': config.dev_password if config.dev else uuid.uuid4(),
                'fullname': tr._((u.metadata.firstName or '') + ' ' + (u.metadata.lastName or '')),
                'sysadmin': u.role == 'ROLE_ADMIN'
            }

            self.action.user_create(**un)
            self.user_count += 1

            if u.publisherId:
                # Dostawca
                # http://docs.ckan.org/en/latest/api/index.html#ckan.logic.action.create.organization_member_create
                om = {
                    'id': u.publisherId,
                    'username': un['id'],
                    'role': 'admin'
                };
 
                self.action.organization_member_create(**om)
  
        #
        #    // TODO Dla dostawców: pełną nazwę urzędu obsługującego dostawcę;2)  określenie nazwy profilu;3)  imię i nazwisko; 4)  stanowisko służbowe; 5)  służbowy numer telefonu oraz adres poczty elektronicznej.
        #    // metadata.phone, metadata.office
        
if __name__ == "__main__":
    p = Process()
    p.process()