import hashlib, random

from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy, ugettext as _
from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site
from teams.models import Team
from people.models import Person

class RegistrationForm(forms.Form):
    """ Form for user registration """
    username = forms.RegexField(max_length=30, regex=r'^\w+$',
                               label=ugettext_lazy(u'Choose a username:'),
                               help_text=ugettext_lazy(u'May contain only letters, numbers, underscores or hyphens'))
    email = forms.EmailField(label=ugettext_lazy(u'Email:'))
    openid_url = forms.URLField(label=ugettext_lazy(u'OpenID:'),
                                required=False)
    password1 = forms.CharField(widget=forms.PasswordInput(render_value=False),
                                label=ugettext_lazy(u'Password:'), required=False, min_length=7,
                                help_text=ugettext_lazy(u'At least 7 characters'))
    password2 = forms.CharField(widget=forms.PasswordInput(render_value=False),
                                label=ugettext_lazy(u'Confirm password:'), required=False)

    def clean_username(self):
        """  Validate the username (correctness and uniqueness)"""
        try:
            user = Person.objects.get(username__iexact=self.cleaned_data['username'])
        except Person.DoesNotExist:
            return self.cleaned_data['username']
        raise forms.ValidationError(_(u'This username is already taken. Please choose another.'))

    def clean(self):
        cleaned_data = self.cleaned_data
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        openid_url = cleaned_data.get('openid_url')
        if not password1 and not openid_url:
            raise forms.ValidationError(_(u'You must either provide an OpenID or a password'))

        if password1 and password1 != password2:
            raise forms.ValidationError(_(u'The passwords do not match'))
        return cleaned_data

    def save(self):
        """ Create the user """
        username = self.cleaned_data['username']
        email = self.cleaned_data['email']

        password = self.cleaned_data['password1']
        new_user = Person.objects.create_user(username=username,
                           email=email,
                           password=password or "!")
        openid = self.cleaned_data['openid_url']
        if openid:
            new_user.openids.create(openid = openid)
        salt = hashlib.sha1(str(random.random())).hexdigest()[:5]
        activation_key = hashlib.sha1(salt+username).hexdigest()
        new_user.activation_key = activation_key
        new_user.is_active = False
        new_user.save()
        # Send activation email
        from django.core.mail import send_mail
        current_site = Site.objects.get_current()
        subject = settings.EMAIL_SUBJECT_PREFIX + _(u'Account activation')
        message = _(u"This is a confirmation that your registration on %s succeeded. To activate your account, please click on the link below or copy and paste it in a browser.") % current_site.name
        message += "\n\nhttp://%s%s\n\n" % (current_site.domain, str(reverse("register_activation", kwargs={'key': activation_key})))
        message += _(u"Administrators of %s" % current_site.name)

        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL,
                  (email,), fail_silently=False)

        return new_user

class DetailForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = ('first_name', 'last_name', 'email', 'image', 'webpage_url', 'irc_nick', 'bugzilla_account')

    def clean_image(self):
        url = self.cleaned_data['image']
        if not url:
            return
        size = get_image_size(url)
        if size[0]>100 or size[1]>100:
            raise forms.ValidationError(_(u"Image too high or too wide (%dx%d, maximum is 100x100 pixels)") % size) 

class TeamJoinForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(TeamJoinForm, self).__init__(*args, **kwargs)
        # FIXME: exclude team to which user is already member
        self.fields['teams'] = forms.ModelChoiceField(queryset=Team.objects.all())

def get_image_size(url):
    """ Returns width and height (as tuple) of the image poited at by the url
        Code partially copied from http://effbot.org/zone/pil-image-size.htm """
    import urllib
    import ImageFile

    try:
        file = urllib.urlopen(url)
    except IOError:
        raise forms.ValidationError(_(u"The URL you provided is not valid"))
    size = None
    p = ImageFile.Parser()
    while 1:
        data = file.read(1024)
        if not data:
            break
        p.feed(data)
        if p.image:
            size = p.image.size
            break
    file.close()
    if not size:
        raise forms.ValidationError(_(u"The URL you provided seems not to correspond to a valid image"))
    return size
