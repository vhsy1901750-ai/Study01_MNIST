# 2026-09-20 19:22 KST
"""MNIST 데이터셋으로 CNN을 학습하고 가중치를 mnist_cnn.pt로 저장한다."""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

from model import MnistCNN

EPOCHS = 8   # 증강을 넣으면 수렴이 느려지므로 늘렸다
BATCH_SIZE = 64
LEARNING_RATE = 0.001
WEIGHTS_PATH = "mnist_cnn.pt"

# MNIST 표준 평균/표준편차. app.py의 전처리와 반드시 같은 값을 써야 한다.
MNIST_MEAN = 0.1307
MNIST_STD = 0.3081


def evaluate(model, loader, device):
    """테스트셋 정확도(%)를 계산한다."""
    model.eval()
    correct = 0
    total = 0
    with torch.no_grad():
        for images, labels in loader:
            images, labels = images.to(device), labels.to(device)
            correct += (model(images).argmax(dim=1) == labels).sum().item()
            total += labels.size(0)
    return 100.0 * correct / total


def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"사용 장치: {device}", flush=True)

    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((MNIST_MEAN,), (MNIST_STD,)),
    ])

    # 학습셋에만 회전, 이동, 확대를 조금씩 넣는다. MNIST 원본은 획이 고른 탓에,
    # 그대로 학습하면 사람이 마우스로 그린 삐뚤한 숫자에 약해진다. 특히 6을 5로 읽었다.
    train_transform = transforms.Compose([
        transforms.RandomAffine(degrees=12, translate=(0.1, 0.1), scale=(0.85, 1.15), shear=8),
        transforms.ToTensor(),
        transforms.Normalize((MNIST_MEAN,), (MNIST_STD,)),
    ])

    train_set = datasets.MNIST(root="./data", train=True, download=True, transform=train_transform)
    test_set = datasets.MNIST(root="./data", train=False, download=True, transform=transform)
    train_loader = DataLoader(train_set, batch_size=BATCH_SIZE, shuffle=True)
    test_loader = DataLoader(test_set, batch_size=BATCH_SIZE)

    model = MnistCNN().to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)

    for epoch in range(1, EPOCHS + 1):
        model.train()
        total_loss = 0.0
        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            loss = criterion(model(images), labels)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        avg_loss = total_loss / len(train_loader)
        accuracy = evaluate(model, test_loader, device)
        print(f"[에폭 {epoch}/{EPOCHS}] 평균 손실: {avg_loss:.4f}, 테스트 정확도: {accuracy:.2f}%", flush=True)

    torch.save(model.state_dict(), WEIGHTS_PATH)
    print(f"학습된 가중치를 {WEIGHTS_PATH}에 저장했습니다.", flush=True)


if __name__ == "__main__":
    main()
