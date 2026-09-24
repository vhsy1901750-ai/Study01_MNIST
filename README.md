<!-- 2026-09-25 00:50 KST -->
# Study01_MNIST

MNIST로 학습한 CNN으로 손글씨 숫자를 인식합니다. 같은 가중치를 쓰는 두 가지 버전이 있습니다.

| 버전 | 실행 환경 | 추론 |
| --- | --- | --- |
| [web_version](web_version/) | 브라우저 | 외부 라이브러리 없이 순수 자바스크립트 |
| [desktop_version](desktop_version/) | Windows | PyTorch |

## 웹에서 바로 써 보기

**https://vhsy1901750-ai.github.io/Study01_MNIST/**

검은 캔버스에 마우스나 손가락으로 숫자를 그린 뒤 [인식]을 누르면 예측한 숫자와 확신도가 나옵니다. 처음 열 때 가중치 파일(약 6MB)을 받으므로 잠시 기다려야 합니다.

## 데스크톱 버전 실행

```bash
pip install torch torchvision pillow
cd desktop_version
python app.py
```

학습된 `mnist_cnn.pt`가 들어 있어 바로 실행됩니다. 직접 다시 학습하려면 `python train.py`를 실행합니다. MNIST를 자동으로 내려받아 5 에폭 학습하며, CPU 기준 약 10분이 걸리고 테스트 정확도는 약 99%입니다.

## 두 버전은 어떻게 이어지나

```
desktop_version/train.py           학습 -> mnist_cnn.pt
desktop_version/export_weights.py  변환 -> web_version/weights.json
web_version/src/model.js           추론
```

브라우저는 PyTorch의 저장 형식을 읽을 수 없으므로, 변환 스크립트가 가중치를 JSON으로 내보냅니다. 함께 만들어지는 `golden.json`에는 MNIST 이미지 20장과 그에 대한 PyTorch의 출력값이 들어 있고, 자바스크립트 추론이 같은 값을 내는지 테스트가 확인합니다. 두 버전이 같은 예측을 한다는 근거입니다.

## 인식이 잘 되는 이유

캔버스에 그린 그림을 그냥 28x28로 줄이면 인식률이 낮습니다. MNIST 원본은 숫자를 20x20 상자에 맞춘 뒤 28x28 가운데에 놓은 형태이기 때문입니다. 두 버전 모두 그린 영역만 잘라내 같은 형식으로 맞춘 뒤 모델에 넣습니다.

## 테스트

```bash
cd desktop_version && python -m pytest    # 가중치 내보내기 검증
cd web_version && node --test             # 추론 엔진과 전처리 검증
```
