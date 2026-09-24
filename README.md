<!-- 2026-09-24 12:35 KST -->
# Study01_MNIST

PyTorch로 MNIST를 학습한 CNN으로, 마우스로 그린 손글씨 숫자를 인식하는 Windows 데스크톱 앱입니다.

## 설치

```bash
pip install torch torchvision pillow
```

## 실행

```bash
python app.py
```

검은 캔버스에 마우스로 숫자를 그린 뒤 **[인식]** 버튼을 누르면 예측한 숫자와 확신도가 표시됩니다. **[지우기]** 버튼으로 캔버스를 비웁니다.

학습된 가중치 `mnist_cnn.pt`가 포함되어 있어 바로 실행할 수 있습니다. 직접 다시 학습하려면:

```bash
python train.py
```

MNIST 데이터셋을 `data/`에 자동으로 내려받아 5 에폭 학습한 뒤 `mnist_cnn.pt`를 덮어씁니다. CPU 기준 약 10분이 걸리며, 테스트 정확도는 약 99%입니다.

## 파일 구성

| 파일 | 설명 |
| --- | --- |
| `model.py` | CNN 모델 정의 (합성곱 2단 + 완전연결 2단) |
| `train.py` | MNIST 학습 및 가중치 저장 |
| `app.py` | Tkinter 손글씨 인식 GUI |
| `make_icon.py` | 앱 아이콘 `app.ico` 생성 |
| `app.bat` | 콘솔 창 없이 앱을 실행하는 배치 파일 |

## 동작 방식

캔버스에 그린 그림을 그대로 28x28로 줄이면 인식률이 낮습니다. MNIST 원본이 숫자를 20x20 상자에 맞춘 뒤 28x28 가운데에 놓은 형태이기 때문입니다. `app.py`의 `preprocess()`가 그린 영역만 잘라내 같은 형식으로 맞춘 뒤 모델에 넣습니다.
