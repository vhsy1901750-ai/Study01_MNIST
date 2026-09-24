# 2026-09-25 00:50 KST
"""학습된 가중치와 검증용 골든 데이터를 web_version에 JSON으로 내보낸다."""

import json
from pathlib import Path

import torch
from torchvision import datasets

from model import MnistCNN
from train import MNIST_MEAN, MNIST_STD

BASE_DIR = Path(__file__).resolve().parent
WEB_DIR = BASE_DIR.parent / "web_version"
GOLDEN_COUNT = 20  # 골든 테스트에 쓸 MNIST 테스트 이미지 장수


def export_weights(state):
    """state_dict를 이름, 모양, 1차원 배열 구조의 JSON으로 저장한다.

    값은 유효숫자 9자리로 줄여 적는다. float32는 9자리면 비트 단위로 똑같이
    복원되므로 정밀도는 그대로면서 파일이 3할 넘게 작아진다.
    """
    payload = {
        name: {
            "shape": list(tensor.shape),
            "data": [float(f"{value:.9g}") for value in tensor.flatten().tolist()],
        }
        for name, tensor in state.items()
    }
    path = WEB_DIR / "weights.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def export_golden(model):
    """MNIST 테스트 이미지 몇 장과 그에 대한 모델 로짓을 함께 저장한다.

    웹 버전의 추론 엔진이 같은 입력에 같은 값을 내는지 비교하는 기준이 된다.
    """
    dataset = datasets.MNIST(root=str(BASE_DIR / "data"), train=False, download=True)

    images = []
    labels = []
    for index in range(GOLDEN_COUNT):
        image, label = dataset[index]
        images.append(list(image.getdata()))
        labels.append(int(label))

    tensor = torch.tensor(images, dtype=torch.float32).view(GOLDEN_COUNT, 1, 28, 28) / 255.0
    with torch.no_grad():
        logits = model((tensor - MNIST_MEAN) / MNIST_STD)

    payload = {"images": images, "labels": labels, "logits": logits.tolist()}
    path = WEB_DIR / "golden.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def main():
    WEB_DIR.mkdir(exist_ok=True)

    state = torch.load(BASE_DIR / "mnist_cnn.pt", map_location="cpu")
    model = MnistCNN()
    model.load_state_dict(state)
    model.eval()

    weights_path = export_weights(state)
    golden_path = export_golden(model)

    print(f"{weights_path.name} 저장 완료 ({weights_path.stat().st_size / 1024 / 1024:.2f}MB)")
    print(f"{golden_path.name} 저장 완료 ({GOLDEN_COUNT}장)")


if __name__ == "__main__":
    main()
