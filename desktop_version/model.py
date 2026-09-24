# 2026-09-20 19:22 KST
"""MNIST 손글씨 숫자 인식용 CNN 모델 정의."""

import torch.nn as nn
import torch.nn.functional as F


class MnistCNN(nn.Module):
    """28x28 흑백 숫자 이미지를 입력받아 0~9 중 하나로 분류한다."""

    def __init__(self):
        super().__init__()
        # 합성곱 2단: 1채널 -> 32채널 -> 64채널
        self.conv1 = nn.Conv2d(1, 32, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.pool = nn.MaxPool2d(2)
        self.dropout = nn.Dropout(0.25)
        # 2x2 풀링을 두 번 거치면 28x28 -> 7x7
        self.fc1 = nn.Linear(64 * 7 * 7, 128)
        self.fc2 = nn.Linear(128, 10)

    def forward(self, x):
        x = self.pool(F.relu(self.conv1(x)))  # 28x28 -> 14x14
        x = self.pool(F.relu(self.conv2(x)))  # 14x14 -> 7x7
        x = self.dropout(x)
        x = x.flatten(1)
        x = F.relu(self.fc1(x))
        return self.fc2(x)
