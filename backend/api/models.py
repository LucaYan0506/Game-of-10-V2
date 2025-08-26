from django.db import models
from django.conf import settings 
from django.core.exceptions import ValidationError 
from . import game_config

class Game(models.Model):
    # --- Choices ---
    class GameType(models.TextChoices):
        # Format: PYTHON_CONSTANT = 'database_value', 'Human-Readable Label'
        STANDARD = 'STANDARD', 'Standard'
        GAME_OF_X = 'GAME_OF_X', 'Game of x'
        HARD = 'HARD', 'Hard'
        
    class GameMode(models.TextChoices):
        PVP = 'PvP', 'PvP'
        PVAI = 'PvAi', 'PvAi'

    class AiModel(models.TextChoices):
        REINFORCEMENT_LEARNING = 'RL', 'RL'
        MONTE_CARLO = 'MCTS', 'MCTS'
        HARD_CODED = 'Hard coded', 'Hard coded'

    class GameStatus(models.TextChoices):
        WAITING = 'WAITING', 'Waiting for opponent'
        ACTIVE = 'ACTIVE', 'Game started'
        FINISHED = 'FINISHED', 'Game finished'

    def get_value_from_label(label_to_find, choices_class):
        for value, label in choices_class.choices:
            if label == label_to_find:
                return value
        return None

    # --- Fields ---
    game_id = models.CharField(max_length=10, primary_key=True, unique=True)

    game_type = models.CharField(choices=GameType.choices, max_length=10)
    game_mode = models.CharField(choices=GameMode.choices, max_length=10)

    status = models.CharField(choices=GameStatus.choices, max_length=10)
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, # If creator deletes account, game isn't deleted
        related_name='created_games', # Prevents clash with opponent
        null=True, # creator might delete the account
        blank=True
    )

    # PvP-specific field
    opponent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, # If opponent deletes account, game isn't deleted
        related_name='opponent_games',
        null=True, # An opponent might not have joined yet
        blank=True
    )

    # PvAI-specific field
    ai_model = models.CharField(
        choices=AiModel.choices,
        max_length=11,
        null=True,
        blank=True
    )

    board = models.CharField(max_length=1000, default = game_config.EMPTY_BOARD)
    pool = models.CharField(max_length=300, default = game_config.ALL_CARDS)
    creator_point = models.IntegerField(default = 0)
    opponent_point = models.IntegerField(default = 0)
    creator_cards = models.CharField(max_length=60)
    opponent_cards = models.CharField(max_length=60)
    creator_turn = models.BooleanField(default=True)
    tie = models.BooleanField(default=False)
    
    winner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,        # If a user account is deleted, we keep the game record but mark winner as null.
        related_name='games_won',          # Access all games a user has won via user.games_won.all()
        null=True,                         # The game may not have a winner yet.
        blank=True
    )
    # This field stores which player surrendered, if any.
    # It replaces the need for a separate boolean field.
    surrendered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,        # If the surrendering player's account is deleted, we keep the game history.
        related_name='surrendered_games',  # Access games a user surrendered via user.surrendered_games.all()
        null=True,                         # This will be null for games that ended normally (not by surrender).
        blank=True,
    )



    def __str__(self):
        return f"Game {self.game_id} ({self.get_game_mode_display()})"

    # --- Model Validation ---
    def clean(self):
        super().clean()
        if self.game_mode == self.GameMode.PVP and self.ai_model is not None:
            raise ValidationError("A PvP game cannot have an AI model.")

        if self.game_mode == self.GameMode.PVAI and self.opponent is not None:
            raise ValidationError("A PvAI game cannot have a human opponent.")

        if self.game_mode == self.GameMode.PVAI and self.ai_model is None:
            raise ValidationError("A PvAI game must have an AI model selected.")
        
    def save(self, *args, **kwargs):
        # Update fields in the database.
        super().save(*args, **kwargs)

        # If both player slots are empty, delete the instance.
        if self.creator is None and self.opponent is None:
            self.delete()