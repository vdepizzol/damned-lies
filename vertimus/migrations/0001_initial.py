# -*- coding: utf-8 -*-

from south.db import db
from django.db import models
from vertimus.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding model 'StateDb'
        db.create_table('state', (
            ('id', orm['vertimus.StateDb:id']),
            ('branch', orm['vertimus.StateDb:branch']),
            ('domain', orm['vertimus.StateDb:domain']),
            ('language', orm['vertimus.StateDb:language']),
            ('person', orm['vertimus.StateDb:person']),
            ('name', orm['vertimus.StateDb:name']),
            ('updated', orm['vertimus.StateDb:updated']),
        ))
        db.send_create_signal('vertimus', ['StateDb'])
        
        # Adding model 'ActionDbArchived'
        db.create_table('action_archived', (
            ('id', orm['vertimus.ActionDbArchived:id']),
            ('state_db', orm['vertimus.ActionDbArchived:state_db']),
            ('person', orm['vertimus.ActionDbArchived:person']),
            ('name', orm['vertimus.ActionDbArchived:name']),
            ('created', orm['vertimus.ActionDbArchived:created']),
            ('comment', orm['vertimus.ActionDbArchived:comment']),
            ('file', orm['vertimus.ActionDbArchived:file']),
            ('sequence', orm['vertimus.ActionDbArchived:sequence']),
        ))
        db.send_create_signal('vertimus', ['ActionDbArchived'])
        
        # Adding model 'ActionDb'
        db.create_table('action', (
            ('id', orm['vertimus.ActionDb:id']),
            ('state_db', orm['vertimus.ActionDb:state_db']),
            ('person', orm['vertimus.ActionDb:person']),
            ('name', orm['vertimus.ActionDb:name']),
            ('created', orm['vertimus.ActionDb:created']),
            ('comment', orm['vertimus.ActionDb:comment']),
            ('file', orm['vertimus.ActionDb:file']),
        ))
        db.send_create_signal('vertimus', ['ActionDb'])
        
        # Creating unique_together for [branch, domain, language] on StateDb.
        db.create_unique('state', ['branch_id', 'domain_id', 'language_id'])
        
    
    
    def backwards(self, orm):
        
        # Deleting unique_together for [branch, domain, language] on StateDb.
        db.delete_unique('state', ['branch_id', 'domain_id', 'language_id'])
        
        # Deleting model 'StateDb'
        db.delete_table('state')
        
        # Deleting model 'ActionDbArchived'
        db.delete_table('action_archived')
        
        # Deleting model 'ActionDb'
        db.delete_table('action')
        
    
    
    models = {
        'auth.group': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'unique_together': "(('content_type', 'codename'),)"},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'languages.language': {
            'Meta': {'db_table': "'language'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'locale': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '15'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            'plurals': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'team': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['teams.Team']", 'null': 'True', 'blank': 'True'})
        },
        'people.person': {
            'Meta': {'db_table': "'person'"},
            'activation_key': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'bugzilla_account': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True', 'blank': 'True'}),
            'image': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'irc_nick': ('django.db.models.fields.SlugField', [], {'db_index': 'True', 'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'svn_account': ('django.db.models.fields.SlugField', [], {'db_index': 'True', 'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'user_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True', 'primary_key': 'True'}),
            'webpage_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        },
        'stats.branch': {
            'Meta': {'unique_together': "(('name', 'module'),)", 'db_table': "'branch'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'module': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['stats.Module']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'vcs_subpath': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'})
        },
        'stats.domain': {
            'Meta': {'db_table': "'domain'"},
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'directory': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'dtype': ('django.db.models.fields.CharField', [], {'default': "'ui'", 'max_length': '5'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'linguas_location': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'module': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['stats.Module']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'pot_method': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        },
        'stats.module': {
            'Meta': {'db_table': "'module'"},
            'bugs_base': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'bugs_component': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'bugs_product': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'comment': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'homepage': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'maintainers': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['people.Person']", 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'vcs_root': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'vcs_type': ('django.db.models.fields.CharField', [], {'max_length': '5'}),
            'vcs_web': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        },
        'teams.team': {
            'Meta': {'db_table': "'team'"},
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mailing_list': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True', 'blank': 'True'}),
            'mailing_list_subscribe': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'members': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['people.Person']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'webpage_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        },
        'vertimus.actiondb': {
            'Meta': {'db_table': "'action'"},
            'comment': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.SlugField', [], {'max_length': '8', 'db_index': 'True'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['people.Person']"}),
            'state_db': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['vertimus.StateDb']"})
        },
        'vertimus.actiondbarchived': {
            'Meta': {'db_table': "'action_archived'"},
            'comment': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.SlugField', [], {'max_length': '8', 'db_index': 'True'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['people.Person']"}),
            'sequence': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'state_db': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['vertimus.StateDb']"})
        },
        'vertimus.statedb': {
            'Meta': {'unique_together': "(('branch', 'domain', 'language'),)", 'db_table': "'state'"},
            'branch': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['stats.Branch']"}),
            'domain': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['stats.Domain']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['languages.Language']"}),
            'name': ('django.db.models.fields.SlugField', [], {'default': "'None'", 'max_length': '20', 'db_index': 'True'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['people.Person']", 'null': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'})
        }
    }
    
    complete_apps = ['vertimus']
