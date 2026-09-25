# 2026-09-26 02:10 KST
"""make_flat_six.py가 그린 글씨체를 학습에 넣기 위한 데이터셋."""

import random

from torch.utils.data import Dataset

from make_flat_six import flat_five, flat_six, render


class FlatStyleDataset(Dataset):
    """위가 평평한 6과 같은 손의 5를 미리 그려 두고 꺼내 쓴다.

    매번 새로 그리면 학습이 느려지므로 처음에 한 번만 만든다.
    """

    def __init__(self, per_class, seed=20260926):
        rng = random.Random(seed)
        self.samples = []

        for maker, label in ((flat_six, 6), (flat_five, 5)):
            for _ in range(per_class):
                self.samples.append((render(maker(rng), rng).squeeze(0), label))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, index):
        # 라벨은 MNIST와 같이 정수로 돌려준다. 텐서로 주면 두 데이터셋을 섞을 때 배치가 깨진다.
        return self.samples[index]
