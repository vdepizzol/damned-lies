# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'ActionArchived.merged_file'
        db.add_column('action_archived', 'merged_file', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['stats.PoFile'], unique=True, null=True), keep_default=False)

        # Adding field 'Action.merged_file'
        db.add_column('action', 'merged_file', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['stats.PoFile'], unique=True, null=True), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'ActionArchived.merged_file'
        db.delete_column('action_archived', 'merged_file_id')

        # Deleting field 'Action.merged_file'
        db.delete_column('action', 'merged_file_id')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'languages.language': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Language', 'db_table': "'language'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'locale': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '15'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            'plurals': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'team': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['teams.Team']", 'null': 'True', 'blank': 'True'})
        },
        'people.person': {
            'Meta': {'ordering': "('username',)", 'object_name': 'Person', 'db_table': "'person'", '_ormbases': ['auth.User']},
            'activation_key': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'bugzilla_account': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True', 'blank': 'True'}),
            'image': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'irc_nick': ('django.db.models.fields.SlugField', [], {'db_index': 'True', 'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'svn_account': ('django.db.models.fields.SlugField', [], {'db_index': 'True', 'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'user_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True', 'primary_key': 'True'}),
            'webpage_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        },
        'stats.branch': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('name', 'module'),)", 'object_name': 'Branch', 'db_table': "'branch'"},
            'file_hashes': ('common.fields.DictionaryField', [], {'default': "''", 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'module': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['stats.Module']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'vcs_subpath': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'weight': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'stats.domain': {
            'Meta': {'ordering': "('-dtype', 'name')", 'object_name': 'Domain', 'db_table': "'domain'"},
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'directory': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'dtype': ('django.db.models.fields.CharField', [], {'default': "'ui'", 'max_length': '5'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'linguas_location': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'module': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['stats.Module']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'pot_method': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'red_filter': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'})
        },
        'stats.module': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Module', 'db_table': "'module'"},
            'bugs_base': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'bugs_component': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'bugs_product': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'comment': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'ext_platform': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'homepage': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'maintainers': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'maintains_modules'", 'blank': 'True', 'db_table': "'module_maintainer'", 'to': "orm['people.Person']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'vcs_root': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'vcs_type': ('django.db.models.fields.CharField', [], {'max_length': '5'}),
            'vcs_web': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        },
        'stats.pofile': {
            'Meta': {'object_name': 'PoFile', 'db_table': "'pofile'"},
            'figures': ('common.fields.JSONField', [], {'null': 'True', 'blank': 'True'}),
            'fuzzy': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'translated': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'untranslated': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        'teams.role': {
            'Meta': {'unique_together': "(('team', 'person'),)", 'object_name': 'Role', 'db_table': "'role'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['people.Person']"}),
            'role': ('django.db.models.fields.CharField', [], {'default': "'translator'", 'max_length': '15'}),
            'team': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['teams.Team']"})
        },
        'teams.team': {
            'Meta': {'ordering': "('description',)", 'object_name': 'Team', 'db_table': "'team'"},
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mailing_list': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True', 'blank': 'True'}),
            'mailing_list_subscribe': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'members': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'teams'", 'symmetrical': 'False', 'through': "orm['teams.Role']", 'to': "orm['people.Person']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'presentation': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'use_workflow': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'webpage_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        },
        'vertimus.action': {
            'Meta': {'object_name': 'Action', 'db_table': "'action'"},
            'comment': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'merged_file': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['stats.PoFile']", 'unique': 'True', 'null': 'True'}),
            'name': ('django.db.models.fields.SlugField', [], {'max_length': '8', 'db_index': 'True'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['people.Person']"}),
            'state_db': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['vertimus.State']"})
        },
        'vertimus.actionarchived': {
            'Meta': {'object_name': 'ActionArchived', 'db_table': "'action_archived'"},
            'comment': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'merged_file': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['stats.PoFile']", 'unique': 'True', 'null': 'True'}),
            'name': ('django.db.models.fields.SlugField', [], {'max_length': '8', 'db_index': 'True'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['people.Person']"}),
            'sequence': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'state_db': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['vertimus.State']"})
        },
        'vertimus.state': {
            'Meta': {'unique_together': "(('branch', 'domain', 'language'),)", 'object_name': 'State', 'db_table': "'state'"},
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
