# Generated by Django 5.2.1 on 2025-06-18 14:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0006_alter_game_creator_cards_alter_game_opponent_cards'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='creator_turn',
            field=models.BooleanField(default=False),
        ),
    ]
