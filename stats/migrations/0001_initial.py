# -*- coding: utf-8 -*-

from south.db import db
from django.db import models
from stats.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding model 'Category'
        db.create_table('category', (
            ('id', orm['stats.Category:id']),
            ('release', orm['stats.Category:release']),
            ('branch', orm['stats.Category:branch']),
            ('name', orm['stats.Category:name']),
        ))
        db.send_create_signal('stats', ['Category'])
        
        # Adding model 'Release'
        db.create_table('release', (
            ('id', orm['stats.Release:id']),
            ('name', orm['stats.Release:name']),
            ('description', orm['stats.Release:description']),
            ('string_frozen', orm['stats.Release:string_frozen']),
            ('status', orm['stats.Release:status']),
        ))
        db.send_create_signal('stats', ['Release'])
        
        # Adding model 'Statistics'
        db.create_table('statistics', (
            ('id', orm['stats.Statistics:id']),
            ('branch', orm['stats.Statistics:branch']),
            ('domain', orm['stats.Statistics:domain']),
            ('language', orm['stats.Statistics:language']),
            ('date', orm['stats.Statistics:date']),
            ('translated', orm['stats.Statistics:translated']),
            ('fuzzy', orm['stats.Statistics:fuzzy']),
            ('untranslated', orm['stats.Statistics:untranslated']),
            ('num_figures', orm['stats.Statistics:num_figures']),
        ))
        db.send_create_signal('stats', ['Statistics'])
        
        # Adding model 'InformationArchived'
        db.create_table('information_archived', (
            ('id', orm['stats.InformationArchived:id']),
            ('statistics', orm['stats.InformationArchived:statistics']),
            ('type', orm['stats.InformationArchived:type']),
            ('description', orm['stats.InformationArchived:description']),
        ))
        db.send_create_signal('stats', ['InformationArchived'])
        
        # Adding model 'Branch'
        db.create_table('branch', (
            ('id', orm['stats.Branch:id']),
            ('name', orm['stats.Branch:name']),
            ('vcs_subpath', orm['stats.Branch:vcs_subpath']),
            ('module', orm['stats.Branch:module']),
        ))
        db.send_create_signal('stats', ['Branch'])
        
        # Adding model 'Domain'
        db.create_table('domain', (
            ('id', orm['stats.Domain:id']),
            ('module', orm['stats.Domain:module']),
            ('name', orm['stats.Domain:name']),
            ('description', orm['stats.Domain:description']),
            ('dtype', orm['stats.Domain:dtype']),
            ('directory', orm['stats.Domain:directory']),
            ('pot_method', orm['stats.Domain:pot_method']),
            ('linguas_location', orm['stats.Domain:linguas_location']),
        ))
        db.send_create_signal('stats', ['Domain'])
        
        # Adding model 'StatisticsArchived'
        db.create_table('statistics_archived', (
            ('id', orm['stats.StatisticsArchived:id']),
            ('module', orm['stats.StatisticsArchived:module']),
            ('type', orm['stats.StatisticsArchived:type']),
            ('domain', orm['stats.StatisticsArchived:domain']),
            ('branch', orm['stats.StatisticsArchived:branch']),
            ('language', orm['stats.StatisticsArchived:language']),
            ('date', orm['stats.StatisticsArchived:date']),
            ('translated', orm['stats.StatisticsArchived:translated']),
            ('fuzzy', orm['stats.StatisticsArchived:fuzzy']),
            ('untranslated', orm['stats.StatisticsArchived:untranslated']),
        ))
        db.send_create_signal('stats', ['StatisticsArchived'])
        
        # Adding model 'Information'
        db.create_table('information', (
            ('id', orm['stats.Information:id']),
            ('statistics', orm['stats.Information:statistics']),
            ('type', orm['stats.Information:type']),
            ('description', orm['stats.Information:description']),
        ))
        db.send_create_signal('stats', ['Information'])
        
        # Adding model 'Module'
        db.create_table('module', (
            ('id', orm['stats.Module:id']),
            ('name', orm['stats.Module:name']),
            ('homepage', orm['stats.Module:homepage']),
            ('description', orm['stats.Module:description']),
            ('comment', orm['stats.Module:comment']),
            ('bugs_base', orm['stats.Module:bugs_base']),
            ('bugs_product', orm['stats.Module:bugs_product']),
            ('bugs_component', orm['stats.Module:bugs_component']),
            ('vcs_type', orm['stats.Module:vcs_type']),
            ('vcs_root', orm['stats.Module:vcs_root']),
            ('vcs_web', orm['stats.Module:vcs_web']),
        ))
        db.send_create_signal('stats', ['Module'])
        
        # Adding ManyToManyField 'Module.maintainers'
        db.create_table('module_maintainer', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('module', models.ForeignKey(orm.Module, null=False)),
            ('person', models.ForeignKey(orm['people.Person'], null=False))
        ))
        
        # Creating unique_together for [name, module] on Branch.
        db.create_unique('branch', ['name', 'module_id'])
        
        # Creating unique_together for [branch, domain, language] on Statistics.
        db.create_unique('statistics', ['branch_id', 'domain_id', 'language_id'])
        
        # Creating unique_together for [release, branch] on Category.
        db.create_unique('category', ['release_id', 'branch_id'])
        
    
    
    def backwards(self, orm):
        
        # Deleting unique_together for [release, branch] on Category.
        db.delete_unique('category', ['release_id', 'branch_id'])
        
        # Deleting unique_together for [branch, domain, language] on Statistics.
        db.delete_unique('statistics', ['branch_id', 'domain_id', 'language_id'])
        
        # Deleting unique_together for [name, module] on Branch.
        db.delete_unique('branch', ['name', 'module_id'])
        
        # Deleting model 'Category'
        db.delete_table('category')
        
        # Deleting model 'Release'
        db.delete_table('release')
        
        # Deleting model 'Statistics'
        db.delete_table('statistics')
        
        # Deleting model 'InformationArchived'
        db.delete_table('information_archived')
        
        # Deleting model 'Branch'
        db.delete_table('branch')
        
        # Deleting model 'Domain'
        db.delete_table('domain')
        
        # Deleting model 'StatisticsArchived'
        db.delete_table('statistics_archived')
        
        # Deleting model 'Information'
        db.delete_table('information')
        
        # Deleting model 'Module'
        db.delete_table('module')
        
        # Dropping ManyToManyField 'Module.maintainers'
        db.delete_table('module_maintainer')
        
    
    
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
            'string_frozen': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'})
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
