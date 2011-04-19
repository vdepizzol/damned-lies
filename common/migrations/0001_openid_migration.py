# encoding: utf-8
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):

    def forwards(self, orm):
        "Write your forwards methods here."
        try:
            from django_openid import models
            from django_openid_auth import models as new_models
        except ImportError:
            # skip migration
            pass # return
        import pdb; pdb.set_trace()
        """for nonce in models.Nonce.objects.all():
            new_nonce = new_models.Nonce.objects.create(server_url=nonce.server_url, timestamp=nonce.timestamp, salt=nonce.salt)
        for assoc in models.Association.objects.all():
            new_assoc = new_models.Association.objects.create(server_url=assoc.server_url, handle=assoc.handle, secret=assoc.secret, issued=assoc.issued, lifetime=assoc.lifetime, assoc_type=assoc.assoc_type)"""
        for user_assoc in models.UserOpenidAssociation.objects.all():
            new_uassoc = new_models.UserOpenID.objects.create(user=user_assoc.user, claimed_id=user_assoc.openid, display_id=user_assoc.openid)


    def backwards(self, orm):
        "Write your backwards methods here."


    models = {
        
    }

    complete_apps = ['common']
