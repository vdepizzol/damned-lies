import os
import sys
from django.core.management.base import BaseCommand
from people.models import Person
from teams.models import Team
from languages.models import Language
from stats.models import Module, Branch, Domain, Release, Category, Statistics
from stats.conf import settings


class Command(BaseCommand):
    """ Before the migration, set the xml_base directory to a legacy Damned Lies checkout """
    
    help = "Migrate current D-L XML files into database content"

    output_transaction = False
    xml_base = settings.OLD_DAMNEDLIES
    sys.path.append(xml_base)
    import data

    def handle(self, **options):
                
        print self.migrate_people()
        print self.migrate_teams()
        print self.migrate_modules()
        print self.migrate_releases()
        print self.migrate_stats()
        
        # Network_manager domains may need renaming (vpn-daemons/openvpn/po -> po-openvpn, ...)
        return "Migration completed."

    def migrate_people(self):
        people = self.data.readFromFile(os.path.join(self.xml_base, "people.xml.in"))
        for key, p in people.items():

            if not p.has_key('bugzilla-account'):
                p['bugzilla-account'] = None

            if p['id'][:2] != "x-":
                p['svn-account'] = p['id']
            else:
                p['svn-account'] = None

            # WARNING The old data model stores first_name and
            # last_name in the same field.
            # This rule won't work in all cases.
            l_name = p['name'].split()
            first_name = l_name[0]
            last_name = ' '.join(l_name[1:])
            # Claude, please have a look at this and the username (unique key)
            print "Name '%s' becomes '%s' and '%s'" % (p['name'], first_name, last_name)
            if p['icon'] == "/data/nobody.png":
                p['icon'] = None
            new_p = Person(_old_id=p['id'],
                           username=p['svn-account'] or p['email'][:30],
                           first_name=l_name[0],
                           last_name=' '.join(l_name[1:]), 
                           email=p['email'],
                           svn_account=p['svn-account'],
                           image=p['icon'], 
                           webpage_url=p['webpage'],
                           irc_nick=p['nick'], 
                           bugzilla_account=p['bugzilla-account'])
            new_p.save()
        return "People migrated successfully"

    def migrate_teams(self):
        teams = self.data.readFromFile(os.path.join(self.xml_base, "translation-teams.xml.in"))
        for key, team in teams.items():
            if len(team['_language'].items()) <= 1:
                team['_description'] = team['_language'].items()[0][1]['content']
            coord = Person.objects.get(_old_id=team['coordinator'].keys()[0])
            if not team.has_key('mailing-list'):
                team['mailing-list'] = None
            if not team.has_key('mailing-list-subscribe'):
                team['mailing-list-subscribe'] = None
            if not team.has_key('_description'):
                team['_description'] = 'Catalan'
                print "Forced Catalan description"
            new_t = Team(name=key, description=team['_description'], coordinator=coord,
                         webpage_url=team['webpage'],
                         mailing_list=team['mailing-list'],
                         mailing_list_subscribe=team['mailing-list-subscribe'])
            new_t.save()
            for lkey, lang in team['_language'].items():
                new_l = Language(name=lang['content'], 
                                 locale=lang['id'], team=new_t)
                new_l.save()
        return "Teams migrated successfully"

    def migrate_modules(self):
        modules = self.data.readFromFile(os.path.join(self.xml_base, "gnome-modules.xml.in"))
        for key, module in modules.items():
            for prop in ['webpage', '_comment']:
                if not module.has_key(prop):
                    module[prop] = None
            if not module.has_key('_description'):
                module['_description'] = module['id']
            new_m = Module(name=module['id'],
                           description=module['_description'], 
                           homepage=module['webpage'],
                           comment=module['_comment'],
                           bugs_base=module['bugs-baseurl'],
                           bugs_product=module['bugs-product'],
                           bugs_component=module['bugs-component'],
                           vcs_type=module['scmroot']['type'],
                           vcs_root=module['scmroot']['path'],
                           vcs_web=module['scmweb'])
            new_m.save()
            # Adding maintainers
            if module.has_key('maintainer'):
                for m in module['maintainer'].items():
                    person = Person.objects.get(_old_id=m[0])
                    new_m.maintainers.add(person)
            # Adding branches
            for bkey, bval in module['branch'].items():
                new_b = Branch(name=bkey, module=new_m)
                if bval.has_key('subpath'):
                    new_b.vcs_subpath = bval['subpath']
                new_b.save()
                # Adding domains (to module), if not exist
                for dkey, dval in bval['domain'].items():
                    if dval.has_key('directory'):
                        ddir = dval['directory']
                    else:
                        ddir = dval['id']
                    existing_d = Domain.objects.filter(module=new_m, dtype='ui', directory=ddir)
                    if len(existing_d) < 1:
                        if not dval.has_key('_description'):
                            dval['_description'] = None
                        new_domain = Domain(module=new_m, name=dkey, description=dval['_description'], dtype='ui', directory=ddir)
                        new_domain.save()
                    #else:
                for dkey, dval in bval['document'].items():
                    if dval.has_key('directory'):
                        ddir = dval['directory']
                    else:
                        ddir = 'help'
                    existing_d = Domain.objects.filter(module=new_m, dtype='doc', directory=ddir)
                    if len(existing_d) < 1:
                        if not dval.has_key('_description'):
                            dval['_description'] = None
                        new_domain = Domain(module=new_m, name=dkey, description=dval['_description'], dtype='doc', directory=ddir)
                        new_domain.save()
                    
        return "Modules migrated successfully"

    def migrate_releases(self):
        releases = self.data.readFromFile(os.path.join(self.xml_base, "releases.xml.in"))
        for key, release in releases.items():
            try:
                new_r = Release.objects.get(name=release['_description'])
            except:
                new_r = Release(name=release['_description'], string_frozen=False, status=release['status'])
                new_r.save()
            if release.has_key('category'):
                for catname, catcontent in release['category'].items():
                    for mod, content in catcontent['module'].items():
                        # find the right branch
                        if content.has_key('branch'):
                            branch_name = content['branch']
                        else:
                            module = Module.objects.get(name=mod)
                            if module.vcs_type == 'git':
                                branch_name = u'master'
                            else:
                                branch_name = u'HEAD'
                        try:
                            branch = Branch.objects.get(module__name=mod, name=branch_name)
                            cat = Category(release=new_r, branch=branch, name=catcontent['_description'])
                            cat.save()
                        except:
                            print "Unable to find branch '%s' of module '%s' for release '%s'" % (branch_name, mod, release['_description'])
            else:
                for mod, content in release['module'].items():
                    if content.has_key('branch'):
                        branch_name = content['branch']
                    else:
                        module = Module.objects.get(name=mod)
                        if module.vcs_type == 'git':
                            branch_name = u'master'
                        else:
                            branch_name = u'HEAD'
                    try:
                        branch = Branch.objects.get(module__name=mod, name=branch_name)
                        cat = Category(release=new_r, branch=branch, name='default')
                        cat.save()
                    except:
                        print "Unable to find branch '%s' of module '%s' for release '%s'" % (branch_name, mod, release['_description'])
        return "Releases migrated successfully"


    def migrate_stats(self):
        """ This method migrate statistics if there is an old_statistics table (from previous DL)"""
        try:
            mysql_settings = settings.MYSQL_SETTINGS
            # Import just after dict access to avoid a useless import
            import MySQLdb
            conn = MySQLdb.connect(**mysql_settings)
            cursor = conn.cursor()
        except:
            from django.db import connection
            cursor = connection.cursor()
            
        try:
            cursor.execute("SELECT module, branch, language, type, domain, date, translated, fuzzy, untranslated FROM old_statistics")
        except:
            return "No statistics to migrate from old_statistics."

        MODULE, BRANCH, LANGUAGE, TYPE, DOMAIN, DATE, TRANSLATED, FUZZY, UNTRANSLATED = 0, 1, 2, 3, 4, 5, 6, 7, 8
        for stat in cursor.fetchall():
            # link to Branch, Domain and Language
            try:
                mod = Module.objects.get(name=stat[MODULE])
            except:
                print "Unable to find module corresponding to '%s'." % stat[MODULE]
                continue
            try:
                br = Branch.objects.get(name=stat[BRANCH], module=mod.id)
            except:
                print "Unable to find branch corresponding to '%s.%s'." % (stat[MODULE], stat[BRANCH])
                continue
            if stat[LANGUAGE] is not None:
                try:
                    lang = Language.objects.get(locale=stat[LANGUAGE])
                except:
                    lang = Language(name=stat[LANGUAGE], 
                                 locale=stat[LANGUAGE])
                    lang.save()
                    print "Unable to find language corresponding to '%s'. Language created." % (stat[LANGUAGE])
            else:
                # The POT file
                lang = None
            for p in mod.domain_set.all():
                if p.dtype == stat[TYPE] and p.name == stat[DOMAIN]:
                    dom = p
                    break
            new_stat = Statistics(branch=br, language=lang, domain=dom, date=stat[DATE], 
                                  translated=stat[TRANSLATED], fuzzy=stat[FUZZY], untranslated=stat[UNTRANSLATED])
            new_stat.save()
        return "Statistics migrated successfully"

