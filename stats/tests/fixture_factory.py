from tempfile import NamedTemporaryFile

from django.core.management.commands.dumpdata import Command as Dumpdata
from django.test import TestCase

from languages.models import Language
from teams.models import Team, Role
from people.models import Person
from stats.models import Module, Domain, Branch, Release, Category, Statistics, Information, PoFile

class FixtureFactory(TestCase):
    """ Fake Test case to create fixture.
        To create a JSON fixture, run:
        python manage.py test stats.FixtureFactory.make_fixture
    """

    def make_fixture(self):
        # Creating models: Teams
        t1 = Team.objects.create(name='fr', description="French",
            webpage_url="http://gnomefr.traduc.org/",
            mailing_list="gnomefr@traduc.org",
            mailing_list_subscribe="http://www.traduc.org/mailman/listinfo/gnomefr",
            presentation="Here can come any custom description for a team")
        t2 = Team.objects.create(name='it', description="Italian",
            webpage_url="http://www.it.gnome.org/")

        # Creating models: Languages
        l_en = Language.objects.create(name='en', locale='en', plurals="nplurals=2; plural=(n != 1)")
        l_fr = Language.objects.create(name='French', locale='fr', plurals="nplurals=2; plural=(n > 1)",
                      team=t1)
        l_it = Language.objects.create(name='Italian', locale='it', plurals="nplurals=2; plural=(n != 1)",
                      team=t2)
        # Lang with no team and no stats
        l_bem = Language.objects.create(name='Bemba', locale='bem')

        # Creating models: Persons/Roles
        p0 = Person.objects.create(username='admin1') # Fake person (deleted below), just not to use pk=1 for user
        p1 = Person.objects.create(first_name='Robert', last_name='Translator',
            email='bob@example.org', username='bob', irc_nick='bobby',
            svn_account='bob1')
        p1.set_password('bob')
        r1 = Role.objects.create(team=t1, person=p1, role='translator')
        p2 = Person.objects.create(first_name='John', last_name='Coordinator',
            email='coord@example.org', username='coord', svn_account='coord_fr')
        p2.set_password('coord')
        r2 = Role.objects.create(team=t1, person=p2, role='coordinator')
        p3 = Person.objects.create(first_name='Alessio', last_name='Reviewer',
            email='alessio@example.org', username='alessio')
        p1.set_password('alessio')
        r3 = Role.objects.create(team=t2, person=p3, role='reviewer')
        p0.delete()

        # Creating models: Modules
        gnome_hello = Module.objects.create(name="gnome-hello", vcs_type="git",
            vcs_root="git://git.gnome.org/gnome-hello",
            vcs_web="http://git.gnome.org/browse/gnome-hello/",
            bugs_base="http://bugzilla.gnome.org",
            bugs_product="gnome-hello",
            bugs_component="test")
        zenity = Module.objects.create(name="zenity", vcs_type="git",
            vcs_root="git://git.gnome.org/zenity",
            vcs_web="http://git.gnome.org/browse/zenity/",
            bugs_base="http://bugzilla.gnome.org",
            bugs_product="zenity",
            bugs_component="general")
        s_m_i = Module.objects.create(name="shared-mime-info", vcs_type="git",
            description="Shared MIME Info",
            vcs_root="git://anongit.freedesktop.org/xdg/shared-mime-info",
            vcs_web="http://cgit.freedesktop.org/xdg/shared-mime-info/",
            bugs_base="https://bugs.freedesktop.org/",
            bugs_product="shared-mime-info",
            bugs_component="general",
            comment="This is not a GNOME-specific module. Please submit your translation " \
            "through the <a href=\"http://www.transifex.net/projects/p/shared-mime-info/c/default/\">Transifex platform</a>.")

        # Creating models: Domains
        dom = {}
        for mod in (gnome_hello, zenity, s_m_i):
            dom['%s-ui' % mod.name] = Domain.objects.create(module=mod, name='po', description='UI Translations', dtype='ui', directory='po')
            dom['%s-doc' % mod.name] = Domain.objects.create(module=mod, name='help', description='User Guide', dtype='doc', directory='help')

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
        rel1 = Release.objects.create(name='gnome-2-30', status='official',
                     description='GNOME 2.30 (stable)',
                     string_frozen=True)
        rel2 = Release.objects.create(name='gnome-dev', status='official',
                     description='GNOME in Development',
                     string_frozen=False)
        rel3 = Release.objects.create(name='freedesktop-org', status='xternal',
                     description='freedesktop.org (non-GNOME)',
                     string_frozen=False)

        cat1 = Category.objects.create(release=rel1, branch=b1, name='desktop')
        cat2 = Category.objects.create(release=rel2, branch=b1, name='desktop')
        cat3 = Category.objects.create(release=rel1, branch=b2, name='desktop')
        cat4 = Category.objects.create(release=rel3, branch=b4, name='desktop')

        # Creating models: Statistics
        # gnome-hello ui, gnome-hello doc (POT, fr, it)
        pofile = PoFile.objects.create(untranslated=47)
        Statistics.objects.create(branch=b1, domain=dom['gnome-hello-ui'], language=None, full_po=pofile, part_po=pofile)
        pofile = PoFile.objects.create(translated=47)
        Statistics.objects.create(branch=b1, domain=dom['gnome-hello-ui'], language=l_fr, full_po=pofile, part_po=pofile)
        pofile = PoFile.objects.create(translated=30, fuzzy=10, untranslated=7)
        Statistics.objects.create(branch=b1, domain=dom['gnome-hello-ui'], language=l_it, full_po=pofile, part_po=pofile)
        pofile = PoFile.objects.create(untranslated=20)
        Statistics.objects.create(branch=b1, domain=dom['gnome-hello-doc'], language=None, full_po=pofile, part_po=pofile)
        pofile = PoFile.objects.create(translated=20)
        Statistics.objects.create(branch=b1, domain=dom['gnome-hello-doc'], language=l_fr, full_po=pofile, part_po=pofile)
        pofile = PoFile.objects.create(translated=20)
        Statistics.objects.create(branch=b1, domain=dom['gnome-hello-doc'], language=l_it, full_po=pofile, part_po=pofile)
        # zenity ui 2.30, zenity doc 2.30, zenity ui master, zenity doc master (POT, fr, it)
        pofile = PoFile.objects.create(untranslated=136)
        part_pofile = PoFile.objects.create(untranslated=128)
        Statistics.objects.create(branch=b2, domain=dom['zenity-ui'], language=None, full_po=pofile, part_po=part_pofile)
        pofile = PoFile.objects.create(translated=136)
        Statistics.objects.create(branch=b2, domain=dom['zenity-ui'], language=l_fr, full_po=pofile, part_po=pofile)
        pofile = PoFile.objects.create(translated=130, untranslated=6)
        part_pofile = PoFile.objects.create(translated=100, untranslated=28)
        Statistics.objects.create(branch=b2, domain=dom['zenity-ui'], language=l_it, full_po=pofile, part_po=part_pofile)
        pofile = PoFile.objects.create(untranslated=259)
        Statistics.objects.create(branch=b2, domain=dom['zenity-doc'], language=None, full_po=pofile, part_po=pofile)
        pofile = PoFile.objects.create(untranslated=259)
        Statistics.objects.create(branch=b2, domain=dom['zenity-doc'], language=l_fr, full_po=pofile, part_po=pofile)
        pofile = PoFile.objects.create(translated=259)
        Statistics.objects.create(branch=b2, domain=dom['zenity-doc'], language=l_it, full_po=pofile, part_po=pofile)
        pofile = PoFile.objects.create(untranslated=149)
        stat1 = Statistics.objects.create(branch=b3, domain=dom['zenity-ui'], language=None, full_po=pofile, part_po=pofile)
        pofile = PoFile.objects.create(translated=255, fuzzy=4)
        Statistics.objects.create(branch=b3, domain=dom['zenity-ui'], language=l_fr, full_po=pofile, part_po=pofile)
        pofile = PoFile.objects.create(translated=259)
        Statistics.objects.create(branch=b3, domain=dom['zenity-ui'], language=l_it, full_po=pofile, part_po=pofile)
        pofile = PoFile.objects.create(untranslated=259)
        Statistics.objects.create(branch=b3, domain=dom['zenity-doc'], language=None, full_po=pofile, part_po=pofile)
        pofile = PoFile.objects.create(untranslated=259)
        Statistics.objects.create(branch=b3, domain=dom['zenity-doc'], language=l_fr, full_po=pofile, part_po=pofile)
        pofile = PoFile.objects.create(translated=259)
        Statistics.objects.create(branch=b3, domain=dom['zenity-doc'], language=l_it, full_po=pofile, part_po=pofile)
        # shared-mime-info ui (POT, fr, it)
        pofile = PoFile.objects.create(untranslated=626)
        Statistics.objects.create(branch=b4, domain=dom['shared-mime-info-ui'], language=None, full_po=pofile, part_po=pofile)
        pofile = PoFile.objects.create(translated=598, fuzzy=20, untranslated=2)
        Statistics.objects.create(branch=b4, domain=dom['shared-mime-info-ui'], language=l_fr, full_po=pofile, part_po=pofile)
        pofile = PoFile.objects.create(translated=620, fuzzy=6)
        Statistics.objects.create(branch=b4, domain=dom['shared-mime-info-ui'], language=l_it, full_po=pofile, part_po=pofile)

        # Example of error
        stat1.information_set.add(Information(
            type='error',
            description="Error regenerating POT file for zenity:\n<pre>intltool-update -g 'zenity' -p\nERROR: xgettext failed to generate PO template file.</pre>"))

        # Output fixture
        data = Dumpdata().handle(*['auth.User', 'people', 'teams', 'languages', 'stats'],
                                 **{'indent':1})
        out_file = NamedTemporaryFile(suffix=".json", dir=".", delete=False)
        out_file.write(data)
        out_file.close()
        print "Fixture created in the file %s" % out_file.name
