from django.core.management.base import BaseCommand

from people.models import Person
from teams.models import Role
from vertimus.models import ActionArchived
from languages.views import clean_tar_files

class Command(BaseCommand):
    help = "Run maintenance tasks"

    def handle(self, *args, **options):
        Person.clean_unactivated_accounts()
        Role.inactivate_unused_roles()
        ActionArchived.clean_old_actions(365)
        clean_tar_files()
