from django.core.management.base import BaseCommand

from people.models import Person
from teams.models import Role

class Command(BaseCommand):
    help = "Run maintenance tasks"

    def handle(self, *args, **options):
        Person.clean_unactivated_accounts()
        Role.inactivate_unused_roles()

