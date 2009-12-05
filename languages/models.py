from django.db import models
from django.utils.translation import ugettext as _
from teams.models import Team, FakeTeam

class Language(models.Model):
    name = models.CharField(max_length=50, unique=True)
    locale = models.CharField(max_length=15, unique=True)
    team = models.ForeignKey(Team, null=True, blank=True, default=None)
    plurals = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = 'language'
        ordering = ('name',)

    def __unicode__(self):
        return "%s (%s)" % (self.name, self.locale)

    @classmethod
    def get_language_from_ianacode(cls, ianacode):
        """ Return a matching Language object corresponding to LANGUAGE_CODE (BCP47-formatted)
            This is a sort of BCP47 to ISO639 conversion function """
        iana_splitted = ianacode.split("-", 1)
        iana_suffix = len(iana_splitted) > 1 and iana_splitted[1] or ""
        iana_suffix = iana_suffix.replace('Latn','latin').replace('Cyrl','cyrillic')
        lang_list = cls.objects.filter(locale__startswith=iana_splitted[0])
        if len(lang_list) == 0:
            return None
        elif len(lang_list) > 1:
            # Find the best language to return
            best_lang = lang_list[0]
            for lang in lang_list:
                if lang.get_suffix():
                    if iana_suffix.lower() == lang.get_suffix().lower():
                        return lang
                else:
                    best_lang = lang
            return best_lang
        return lang_list[0]

    def get_name(self):
        if self.name != self.locale:
            return _(self.name)
        else:
            return self.locale

    def get_suffix(self):
        splitted = self.locale.replace('@','_').split('_')
        if len(splitted) > 1:
            return splitted[-1]
        return None

    def get_plurals(self):
        # Translators: this concerns an unknown plural form
        return self.plurals or _("Unknown")

    def bugs_url_enter(self):
        return "http://bugzilla.gnome.org/enter_bug.cgi?product=l10n&amp;component=%s%%20[%s]" %  (self.name, self.locale)

    def bugs_url_show(self):
        return "http://bugzilla.gnome.org/buglist.cgi?product=l10n&amp;component=%s%%20[%s]&amp;bug_status=NEW&amp;bug_status=REOPENED&amp;bug_status=ASSIGNED&amp;bug_status=UNCONFIRMED" % (self.name, self.locale)

    def get_release_stats(self, archives=False):
        # FIXME Here be dragons
        """ Get summary stats for all releases """
        from stats.models import Release

        if archives:
            releases = Release.objects.all().filter(weight__lt=0).order_by('status', '-weight', '-name')
        else:
            releases = Release.objects.all().filter(weight__gte=0).order_by('status', '-weight', '-name')
        stats = []
        for rel in releases:
            stats.append(rel.total_for_lang(self))
        return stats

    def get_team_url(self):
        if self.team:
            return self.team.get_absolute_url()
        else:
            return FakeTeam(self).get_absolute_url()
