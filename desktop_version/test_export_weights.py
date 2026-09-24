# 2026-09-25 00:50 KST
"""export_weights.py가 만든 JSON이 원본 모델과 일치하는지 검증한다."""

import json
import subprocess
import sys
from pathlib import Path

import torch

BASE_DIR = Path(__file__).resolve().parent
WEB_DIR = BASE_DIR.parent / "web_version"


def test_내보낸_가중치가_원본과_일치한다():
    subprocess.run([sys.executable, "export_weights.py"], cwd=BASE_DIR, check=True)

    exported = json.loads((WEB_DIR / "weights.json").read_text(encoding="utf-8"))
    state = torch.load(BASE_DIR / "mnist_cnn.pt", map_location="cpu")

    assert set(exported) == set(state)
    for name, tensor in state.items():
        assert exported[name]["shape"] == list(tensor.shape)
        # 자릿수를 줄여 적으므로 float64로는 다를 수 있다. float32로 읽으면 같아야 한다.
        restored = torch.tensor(exported[name]["data"], dtype=torch.float32)
        assert torch.equal(restored, tensor.flatten())


def test_골든_데이터가_모델_출력과_일치한다():
    golden = json.loads((WEB_DIR / "golden.json").read_text(encoding="utf-8"))

    assert len(golden["images"]) == 20
    assert len(golden["labels"]) == 20
    assert len(golden["logits"]) == 20
    assert all(len(row) == 784 for row in golden["images"])
    assert all(len(row) == 10 for row in golden["logits"])
    assert all(0 <= value <= 255 for value in golden["images"][0])

    # 저장된 이미지를 다시 모델에 넣으면 저장된 로짓이 나와야 한다
    sys.path.insert(0, str(BASE_DIR))
    from model import MnistCNN
    from train import MNIST_MEAN, MNIST_STD

    model = MnistCNN()
    model.load_state_dict(torch.load(BASE_DIR / "mnist_cnn.pt", map_location="cpu"))
    model.eval()

    images = torch.tensor(golden["images"], dtype=torch.float32).view(20, 1, 28, 28) / 255.0
    with torch.no_grad():
        logits = model((images - MNIST_MEAN) / MNIST_STD)

    assert torch.allclose(logits, torch.tensor(golden["logits"]), atol=1e-5)
