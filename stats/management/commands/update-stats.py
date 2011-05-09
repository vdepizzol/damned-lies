import sys, traceback
from optparse import make_option
from django.core.management.base import BaseCommand
from django.core.mail import mail_admins
from stats.models import Module, Branch

class Command(BaseCommand):
    help = "Update statistics about po file"
    args = "[MODULE [BRANCH]]"

    option_list = BaseCommand.option_list + (
        make_option('--force', action='store_true', dest='force', default=False,
            help="force statistics generation, even if files didn't change"),
        make_option('--non-gnome', action='store_true', dest='non-gnome', default=False,
            help="generate statistics for non-gnome modules (externally hosted)"),
        make_option('--debug', action='store_true', dest='debug', default=False,
            help="activate interactive debug mode"),
    )

    output_transaction = False

    def handle(self, *args, **options):
        if options['debug']:
            import pdb; pdb.set_trace()
        if len(args) >= 2:
            # Update the specific branch(es) of a module
            module_arg = args[0]
            branch_list = args[1:]
            for branch_arg in branch_list:
                if branch_arg == "trunk":
                    branch_arg = "HEAD"
                try:
                    branch = Branch.objects.get(module__name=module_arg, name=branch_arg)
                except:
                    print >> sys.stderr, "Unable to find branch '%s' for module '%s' in the database." % (branch_arg, module_arg)
                    return "Update unsuccessful."
                print "Updating stats for %s.%s..." % (module_arg, branch_arg)
                try:
                    branch.update_stats(options['force'])
                except:
                    tbtext = traceback.format_exc()
                    mail_admins("Error while updating %s %s" % (module_arg, branch_arg), tbtext)
                    print >> sys.stderr, "Error during updating, mail sent to admins"

        elif len(args) == 1:
            # Update all branches of a module
            module_arg = args[0]
            print "Updating stats for %s..." % (module_arg)
            branches = Branch.objects.filter(module__name=module_arg)
            for branch in branches.all():
                try:
                    branch.update_stats(options['force'])
                except:
                    print >> sys.stderr, traceback.format_exc()
                    print "Error while updating stats for %s (branch '%s')" % (module_arg, branch.name)
        else:
            # Update all modules
            if options['non-gnome']:
                modules = Module.objects.exclude(vcs_root__startswith='git://git.gnome.org/')
            else:
                modules = Module.objects.all()
            for mod in modules:
                print "Updating stats for %s..." % (mod.name)
                branches = Branch.objects.filter(module__name=mod)
                for branch in branches.all():
                    try:
                        branch.update_stats(options['force'])
                    except:
                        print >> sys.stderr, traceback.format_exc()
                        print "Error while updating stats for %s (branch '%s')" % (mod.name, branch.name)

        return "Update completed.\n"
