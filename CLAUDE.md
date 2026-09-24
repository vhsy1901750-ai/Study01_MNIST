<!-- 2026-09-20 19:15 KST -->
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

PyTorch로 MNIST를 학습한 CNN으로, Tkinter 캔버스에 마우스로 그린 숫자를 인식하는 Windows 데스크톱 앱. 모든 코드, 주석, UI 문자열은 한글로 작성한다.

## 명령어

```bash
pip install torch torchvision pillow   # 의존성 (CPU 버전 torch로 충분)
python train.py                        # MNIST 학습 → mnist_cnn.pt 저장 (CPU 기준 약 10분, 5 에폭)
python app.py                          # 손글씨 인식 GUI 실행 (mnist_cnn.pt가 있어야 함)
python make_icon.py                    # app.ico 재생성 (아이콘 모양을 바꿀 때)
```

- 테스트 스위트는 없다. 동작 검증은 `train.py`의 에폭별 테스트 정확도 출력(약 99%)과 GUI 실행으로 한다.
- `preprocess()`를 고쳤다면 MNIST 이미지를 캔버스 크기로 키워 전처리 경로를 통과시켜 본다 (정상이면 90% 이상).

  ```bash
  python -c "
  import torch; from torchvision import datasets; from PIL import Image
  from model import MnistCNN; from app import preprocess
  m = MnistCNN(); m.load_state_dict(torch.load('mnist_cnn.pt', map_location='cpu')); m.eval()
  ds = datasets.MNIST(root='./data', train=False)
  ok = sum(m(preprocess(ds[i][0].resize((280, 280), Image.NEAREST))).argmax(1).item() == ds[i][1] for i in range(200))
  print(f'{ok / 2:.1f}%')"
  ```
- Git Bash에서 한글 출력이 깨지면 `PYTHONIOENCODING=utf-8 python ...`으로 실행한다.
- `app.bat`과 바탕 화면 바로가기(`손글씨 숫자 인식기.lnk`)는 `pythonw.exe`로 `app.py`를 실행해 콘솔 창 없이 GUI만 띄운다.

## 구조와 주의점

- `model.py`의 `MnistCNN`을 `train.py`와 `app.py`가 공유한다. 모델 구조를 바꾸면 `mnist_cnn.pt`를 다시 학습해야 한다.
- 정규화 상수 `MNIST_MEAN`, `MNIST_STD`는 `train.py`에만 정의하고 `app.py`가 import해서 쓴다. `app.py`에 값을 따로 적지 않는다 (학습과 추론의 정규화가 어긋나면 인식률이 떨어진다).
- `app.py`의 `preprocess()`는 그린 영역만 잘라내 20x20으로 줄이고 28x28 중앙에 배치한다. MNIST 원본이 이 형식이라 이 단계를 빼면 실제 손글씨 인식률이 크게 떨어진다.
- `app.py`는 `mnist_cnn.pt`, `app.ico`를 `__file__` 기준 경로로 찾는다. 바로가기, 더블클릭 실행 시 작업 폴더가 다를 수 있으므로 상대 경로로 되돌리지 않는다.
- `app.bat`은 cmd.exe가 읽으므로 **CRLF 줄바꿈 + CP949 인코딩**으로 저장해야 한다. LF나 UTF-8로 저장하면 `rem` 주석 줄이 명령으로 잘못 해석된다.
- `data/`에는 MNIST 원본이 내려받아져 있고, `mnist_cnn.pt`(1.7MB)는 학습 산출물이다.
- 바로가기(`%USERPROFILE%\Desktop\손글씨 숫자 인식기.lnk`)는 저장소 밖에 있다. 다시 만들려면 대상 `pythonw.exe`, 인수 `"C:\study01_mnist\app.py"`, 작업 폴더 `C:\study01_mnist`, 아이콘 `app.ico,0`으로 WScript.Shell 바로가기를 생성한다. 작업 표시줄 고정은 Windows 정책상 사용자가 직접 해야 한다.
