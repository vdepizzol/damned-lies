import datetime

from django.db import models
from django.contrib.auth.models import User, UserManager

def obfuscate_email(email):
    if email:
        return email.replace('@', ' at ').replace('.', ' dot ')
    return ''

class Person(User):
    """ The User class of D-L. """

    svn_account = models.SlugField(max_length=20, null=True, blank=True)
    image = models.URLField(null=True, blank=True)
    webpage_url = models.URLField(null=True, blank=True)
    irc_nick = models.SlugField(max_length=20, null=True, blank=True)
    bugzilla_account = models.EmailField(null=True, blank=True)
    activation_key = models.CharField(max_length=40, null=True, blank=True)

    # Use UserManager to get the create_user method, etc.
    objects = UserManager()

    class Meta:
        db_table = 'person'
        ordering = ('username',)

    @classmethod
    def clean_unactivated_accounts(cls):
        accounts = cls.objects.filter(activation_key__isnull=False)
        for account in accounts:
            if account.date_joined + datetime.timedelta(days=5) <= datetime.datetime.now():
                account.delete()

    def save(self):
        if not self.password or self.password == "!":
            self.password = None
            self.set_unusable_password()
        super(User, self).save()
    
    def activate(self):
        self.activation_key = None
        self.is_active = True
        self.save()
        
    def no_spam_email(self):
        return obfuscate_email(self.email)

    def no_spam_bugzilla_account(self):
        return obfuscate_email(self.bugzilla_account)

    @property
    def name(self):
        return self.first_name + " " + self.last_name

    @models.permalink
    def get_absolute_url(self):
        return ('person', [str(self.id)])

    def is_committer(self, team):
        try:
            self.role_set.get(team=team, role='committer')
            return True
        except:
            return False

    def is_reviewer(self, team):
        try:
            self.role_set.get(team=team, role='reviewer')
            return True
        except:
            return False

    def is_translator(self, team):
        try:
            self.role_set.get(team=team, role='translator')
            return True
        except:
            return False

    # Related names
    # - module: maintains_modules
    # - team: coordinates_teams
