import torch
import torch.nn as nn
import torch.optim as optim
import random

class TransformerAgent(nn.Module):

    def __init__(self):

        super().__init__()

        self.embed = nn.Linear(3, 32)

        self.tr = nn.TransformerEncoder(
            nn.TransformerEncoderLayer(d_model=32, nhead=4),
            num_layers=2
        )

        self.out = nn.Linear(32, 2)

        self.opt = optim.Adam(self.parameters(), lr=0.001)
        self.loss = nn.MSELoss()

    def forward(self, x):

        x = self.embed(x)
        x = self.tr(x)
        x = self.out(x[-1])

        return x

    def act(self, seq):

        if random.random() < 0.1:
            return random.randint(0,1)

        x = torch.FloatTensor(seq).unsqueeze(1)
        q = self.forward(x)

        return torch.argmax(q).item()