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

    def get_name(self):
        if self.name != self.locale:
            return _(self.name)
        else:
            return self.locale

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
