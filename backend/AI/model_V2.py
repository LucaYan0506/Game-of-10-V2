import torch
import torch.nn as nn
import torch.nn.functional as F


class ValueNet(nn.Module):
    def __init__(self):
        super().__init__()

        self.board_net = nn.Sequential(
            nn.Conv2d(in_channels=15, out_channels=32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv2d(in_channels=32, out_channels=64, kernel_size=3, padding=1),
            nn.ReLU()
        )

        self.cards_net = nn.Sequential(
            nn.Linear(14, 32),
            nn.Linear(32, 32)
        )

        # score diff as input. I.e (player_score - opp_score) / MAX_SCORE
        self.score_net = nn.Sequential(
            nn.Linear(1, 8),
            nn.ReLU()
        )

        # stage = max(player_score, opp_score) / MAX_SCORE
        self.stage_net = nn.Sequential(
            nn.Linear(1, 8),
            nn.ReLU()
        )

        self.fusion_net = nn.Sequential(
            nn.Linear(64+32+8+8, 128),
            nn.ReLU(),
            nn.Linear(128, 1),
            nn.Tanh()
        )

    def forward(self, board, cards, score, stage):
        board_feat = self.board_net(board)          # (B, 64, 13, 13)
        board_feat = torch.amax(board_feat, dim=(2, 3))  # max pooling

        cards_feat = self.cards_net(cards)           # (B, 32)
        score_feat = self.score_net(score)          # (B, 8)
        stage_feat = self.stage_net(stage)          # (B, 8)

        # Fusion
        fused = torch.cat([board_feat, cards_feat, score_feat, stage_feat], dim=1)

        value = self.fusion_net(fused)
        return value
