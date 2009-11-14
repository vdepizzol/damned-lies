# -*- coding: utf-8 -*-

from south.db import db
from django.db import models
from stats.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding field 'Release.weight'
        db.add_column('release', 'weight', orm['stats.release:weight'])
        
    
    
    def backwards(self, orm):
        
        # Deleting field 'Release.weight'
        db.delete_column('release', 'weight')
        
    
    
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
            'name': ('BranchCharField', [], {'max_length': '50'}),
            'vcs_subpath': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'})
        },
        'stats.category': {
            'Meta': {'unique_together': "(('release', 'branch'),)", 'db_table': "'category'"},
            'branch': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['stats.Branch']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'default': "'default'", 'max_length': '30'}),
            'release': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['stats.Release']"})
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
        'stats.information': {
            'Meta': {'db_table': "'information'"},
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'statistics': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['stats.Statistics']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        'stats.informationarchived': {
            'Meta': {'db_table': "'information_archived'"},
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'statistics': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['stats.StatisticsArchived']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '10'})
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
        'stats.release': {
            'Meta': {'db_table': "'release'"},
            'branches': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['stats.Branch']"}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.SlugField', [], {'max_length': '20', 'db_index': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '12'}),
            'string_frozen': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'weight': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'stats.statistics': {
            'Meta': {'unique_together': "(('branch', 'domain', 'language'),)", 'db_table': "'statistics'"},
            'branch': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['stats.Branch']"}),
            'date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'domain': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['stats.Domain']"}),
            'fuzzy': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['languages.Language']", 'null': 'True'}),
            'num_figures': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'translated': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'untranslated': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'stats.statisticsarchived': {
            'Meta': {'db_table': "'statistics_archived'"},
            'branch': ('django.db.models.fields.TextField', [], {}),
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'domain': ('django.db.models.fields.TextField', [], {}),
            'fuzzy': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'module': ('django.db.models.fields.TextField', [], {}),
            'translated': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            'untranslated': ('django.db.models.fields.IntegerField', [], {'default': '0'})
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
        }
    }
    
    complete_apps = ['stats']
