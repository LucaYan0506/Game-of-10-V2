# Generated by Django 5.2.1 on 2025-06-06 15:43

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_alter_game_ai_model_alter_game_game_mode_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='game',
            old_name='group_id',
            new_name='game_id',
        ),
    ]
