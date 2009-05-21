import shutil
from django.core.management.base import BaseCommand
from stats.models import Module, Branch
from stats import utils

class Command(BaseCommand):

    def handle(self, *args, **options):
        """ Migrate GNOME SVN modules to git repos in bulk """
        if len(args) == 1:
            modules = [Module.objects.get(name = args[0])]
        else:
            modules = Module.objects.filter(vcs_root='http://svn.gnome.org/svn')
        for module in modules:
            old_branch_dirs = []
            for branch in module.branch_set.all():
                old_branch_dirs.append(branch.co_path())

            module.vcs_type = "git"
            module.vcs_root = "git://git.gnome.org/%s" % module.name
            module.vcs_web = "http://git.gnome.org/cgit/%s/" % module.name
            module.save()

            # Checkout new git repo with master branch
            head_branch = Branch.objects.get(module__name=module.name, name='HEAD')
            head_branch.name = "master"
            try:
                head_branch.save() # Save will do a checkout
            except Exception, e:
                print "Unable to save master branch for module '%s': %s" % (module.name, e)
                continue

            for branch in module.branch_set.exclude(name='master'):
                # Checkout branch (other than master)
                cmd = "cd \"%(localdir)s\" && git checkout --track -b %(branch)s  origin/%(branch)s" % {
                        "localdir" : branch.co_path(),
                        "branch" : branch.name,
                        }
                try:
                    utils.run_shell_command(cmd, raise_on_error=True)
                except Exception, e:
                    print "Unable to checkout branch '%s' of module '%s': %s" % (branch.name, module.name, e)
                    continue
                branch.update_stats(force=False)

            # delete old checkouts
            for branch_dir in old_branch_dirs:
                shutil.rmtree(branch_dir)
