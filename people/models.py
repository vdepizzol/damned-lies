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
    bugzilla_account = models.SlugField(null=True, blank=True)

    # Use UserManager to get the create_user method, etc.
    objects = UserManager()
    
    class Meta:
        db_table = 'person'
        ordering = ('username',)

    def save(self):
        if not self.password or self.password == "!":
            self.password = None
            self.set_unusable_password()
        super(User, self).save()
        
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

    # Related names
    # - module: maintains_modules
    # - team: coordinates_teams
