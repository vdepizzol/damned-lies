import sys, os, traceback
from optparse import make_option
from django.core.management.base import BaseCommand
from django.core.mail import mail_admins
from stats.models import Module, Branch

class Command(BaseCommand):
    help = "Update statistics about po file"
    args = "[MODULE_ID [BRANCH]]"
    
    option_list = BaseCommand.option_list + (
        make_option('--force', action='store_true', dest='force', default=False,
            help="force statistics generation, even if files didn't change"),
    )        

    output_transaction = False

    def handle(self, *args, **options):
        if len(args) <= 2:
            if len(args) == 2:
                # Update the specific branch of a module
                module_arg = args[0]
                branch_arg = args[1]
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
                        print "Error while updating stats for %s (branch '%s')" % (module_arg, branch.name)
            else:
                # Update all modules
                modules = Module.objects.all()
                for mod in modules:
                    print "Updating stats for %s..." % (mod.name)
                    branches = Branch.objects.filter(module__name=mod)
                    for branch in branches.all():
                        try:
                            branch.update_stats(options['force'])
                        except:
                            print "Error while updating stats for %s (branch '%s')" % (module_arg, branch.name)
        else:
            return "Too much command line arguments."

        return "Update completed."


