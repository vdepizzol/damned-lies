from tempfile import NamedTemporaryFile

from django.core.management.commands.dumpdata import Command as Dumpdata
from django.test import TestCase

from languages.models import Language
from teams.models import Team, Role
from people.models import Person
from stats.models import Module, Domain, Branch, Release, Category, Statistics

class FixtureFactory(TestCase):
    """ Fake Test case to create fixture.
        To create a JSON fixture, run:
        python manage.py test stats.FixtureFactory.make_fixture
    """

    def make_fixture(self):
        # Creating models: Teams
        t1 = Team(name='fr', description="French",
            webpage_url="http://gnomefr.traduc.org/",
            mailing_list="gnomefr@traduc.org",
            mailing_list_subscribe="http://www.traduc.org/mailman/listinfo/gnomefr",
            presentation="Here can come any custom description for a team")
        t1.save()
        t2 = Team(name='it', description="Italian",
            webpage_url="http://www.it.gnome.org/")
        t2.save()

        # Creating models: Languages
        l_en = Language(name='en', locale='en', plurals="nplurals=2; plural=(n != 1)")
        l_en.save()
        l_fr = Language(name='French', locale='fr', plurals="nplurals=2; plural=(n > 1)",
                      team=t1)
        l_fr.save()
        l_it = Language(name='Italian', locale='it', plurals="nplurals=2; plural=(n != 1)",
                      team=t2)
        l_it.save()

        # Creating models: Persons/Roles
        p1 = Person(first_name='Robert', last_name='Translator',
            email='bob@example.org', username='bob', irc_nick='bobby',
            svn_account='bob1')
        p1.save()
        p1.set_password('bob')
        r1 = Role(team=t1, person=p1, role='translator')
        r1.save()
        p2 = Person(first_name='John', last_name='Coordinator',
            email='coord@example.org', username='coord', svn_account='coord_fr')
        p2.save()
        p2.set_password('coord')
        r2 = Role(team=t1, person=p2, role='coordinator')
        r2.save()
        p3 = Person(first_name='Alessio', last_name='Reviewer',
            email='alessio@example.org', username='alessio')
        p3.save()
        p1.set_password('alessio')
        r3 = Role(team=t2, person=p3, role='reviewer')
        r3.save()

        # Creating models: Modules
        gnome_hello = Module(name="gnome-hello", vcs_type="git",
            vcs_root="git://git.gnome.org/gnome-hello",
            vcs_web="http://git.gnome.org/browse/gnome-hello/",
            bugs_base="http://bugzilla.gnome.org",
            bugs_product="gnome-hello",
            bugs_component="test")
        gnome_hello.save()
        zenity = Module(name="zenity", vcs_type="git",
            vcs_root="git://git.gnome.org/zenity",
            vcs_web="http://git.gnome.org/browse/zenity/",
            bugs_base="http://bugzilla.gnome.org",
            bugs_product="zenity",
            bugs_component="general")
        zenity.save()
        s_m_i = Module(name="shared-mime-info", vcs_type="git",
            description="Shared MIME Info",
            vcs_root="git://anongit.freedesktop.org/xdg/shared-mime-info",
            vcs_web="http://cgit.freedesktop.org/xdg/shared-mime-info/",
            bugs_base="https://bugs.freedesktop.org/",
            bugs_product="shared-mime-info",
            bugs_component="general",
            comment="This is not a GNOME-specific module. Please submit your translation " \
            "through the <a href=\"http://www.transifex.net/projects/p/shared-mime-info/c/default/\">Transifex platform</a>.")
        s_m_i.save()

        # Creating models: Domains
        dom = {}
        for mod in (gnome_hello, zenity, s_m_i):
            dom['%s-ui' % mod.name] = Domain(module=mod, name='po', description='UI Translations', dtype='ui', directory='po')
            dom['%s-ui' % mod.name].save()
            dom['%s-doc' % mod.name] = Domain(module=mod, name='help', description='User Guide', dtype='doc', directory='help')
            dom['%s-doc' % mod.name].save()

        # Creating models: Branches
        Branch.checkout_on_creation = False
        b1 = Branch(name='master', module=gnome_hello)
        b1.save(update_statistics=False)
        b2 = Branch(name='gnome-2-30', module=zenity)
        b2.save(update_statistics=False)
        b3 = Branch(name='master', module=zenity)
        b3.save(update_statistics=False)
        b4 = Branch(name='master', module=s_m_i)
        b4.save(update_statistics=False)

        # Creating models: Releases/Categories
        rel1 = Release(name='gnome-2-30', status='official',
                     description='GNOME 2.30 (stable)',
                     string_frozen=True)
        rel1.save()
        rel2 = Release(name='gnome-dev', status='official',
                     description='GNOME in Development',
                     string_frozen=False)
        rel2.save()
        rel3 = Release(name='freedesktop-org', status='xternal',
                     description='freedesktop.org (non-GNOME)',
                     string_frozen=False)
        rel3.save()

        cat1 = Category(release=rel1, branch=b1, name='desktop')
        cat1.save()
        cat2 = Category(release=rel2, branch=b1, name='desktop')
        cat2.save()
        cat3 = Category(release=rel1, branch=b2, name='desktop')
        cat3.save()
        cat4 = Category(release=rel3, branch=b4, name='desktop')
        cat4.save()

        # Creating models: Statistics
        # gnome-hello ui, gnome-hello doc (POT, fr, it)
        stats = []
        stats.append(Statistics(branch=b1, domain=dom['gnome-hello-ui'], language=None, untranslated=47))
        stats.append(Statistics(branch=b1, domain=dom['gnome-hello-ui'], language=l_fr, translated=47))
        stats.append(Statistics(branch=b1, domain=dom['gnome-hello-ui'], language=l_it, translated=30, fuzzy=10, untranslated=7))
        stats.append(Statistics(branch=b1, domain=dom['gnome-hello-doc'], language=None, untranslated=20, num_figures=1))
        stats.append(Statistics(branch=b1, domain=dom['gnome-hello-doc'], language=l_fr, translated=20))
        stats.append(Statistics(branch=b1, domain=dom['gnome-hello-doc'], language=l_it, translated=20))
        # zenity ui 2.30, zenity doc 2.30, zenity ui master, zenity doc master (POT, fr, it)
        stats.append(Statistics(branch=b2, domain=dom['zenity-ui'], language=None, untranslated=136))
        stats.append(Statistics(branch=b2, domain=dom['zenity-ui'], language=l_fr, translated=136))
        stats.append(Statistics(branch=b2, domain=dom['zenity-ui'], language=l_it, translated=130, untranslated=6))
        stats.append(Statistics(branch=b2, domain=dom['zenity-doc'], language=None, untranslated=259, num_figures=11))
        stats.append(Statistics(branch=b2, domain=dom['zenity-doc'], language=l_fr, untranslated=259))
        stats.append(Statistics(branch=b2, domain=dom['zenity-doc'], language=l_it, translated=259))
        stats.append(Statistics(branch=b3, domain=dom['zenity-ui'], language=None, untranslated=149))
        stats.append(Statistics(branch=b3, domain=dom['zenity-ui'], language=l_fr, translated=255, fuzzy=4))
        stats.append(Statistics(branch=b3, domain=dom['zenity-ui'], language=l_it, translated=259))
        stats.append(Statistics(branch=b3, domain=dom['zenity-doc'], language=None, untranslated=259, num_figures=11))
        stats.append(Statistics(branch=b3, domain=dom['zenity-doc'], language=l_fr, untranslated=259))
        stats.append(Statistics(branch=b3, domain=dom['zenity-doc'], language=l_it, translated=259))
        # shared-mime-info ui (POT, fr, it)
        stats.append(Statistics(branch=b4, domain=dom['shared-mime-info-ui'], language=None, untranslated=626))
        stats.append(Statistics(branch=b4, domain=dom['shared-mime-info-ui'], language=l_fr, translated=598, fuzzy=20, untranslated=2))
        stats.append(Statistics(branch=b4, domain=dom['shared-mime-info-ui'], language=l_it, translated=620, fuzzy=6))
        for st in stats:
            st.save()

        # Output fixture
        data = Dumpdata().handle(*['auth.User', 'people', 'languages', 'teams', 'stats'],
                                 **{'indent':1})
        out_file = NamedTemporaryFile(suffix=".json", dir=".", delete=False)
        out_file.write(data)
        out_file.close()
        print "Fixture created in the file %s" % out_file.name