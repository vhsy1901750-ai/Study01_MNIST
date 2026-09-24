<!-- 2026-09-24 16:28 KST -->
# 프로젝트 작업 지침 (Study01_MNIST)

전역 지침(`~/.claude/CLAUDE.md`)을 이 프로젝트에 적용한 문서입니다. 전역 지침이 원칙을 정하고, 이 문서는 그 원칙이 이 코드베이스에서 구체적으로 무엇을 뜻하는지 적습니다.

## 프로젝트 개요

PyTorch로 MNIST를 학습한 CNN으로, Tkinter 캔버스에 마우스로 그린 숫자를 인식하는 Windows 데스크톱 앱입니다. 모든 코드, 주석, UI 문자열은 한글로 작성합니다.

## 명령어

```bash
pip install torch torchvision pillow   # 의존성 (CPU 버전 torch로 충분)
python train.py                        # MNIST 학습 후 mnist_cnn.pt 저장 (CPU 기준 약 10분, 5 에폭)
python app.py                          # 손글씨 인식 GUI 실행 (mnist_cnn.pt가 있어야 함)
python make_icon.py                    # app.ico 재생성 (아이콘 모양을 바꿀 때)
```

Git Bash에서 한글 출력이 깨지면 `PYTHONIOENCODING=utf-8 python ...`으로 실행합니다.

## 변경별 검증 방법 (전역 §4 목표 기반 실행)

이 프로젝트에는 테스트 스위트가 없습니다. "동작하게 해줘" 대신 아래 기준으로 성공을 판정합니다.

| 무엇을 고쳤나 | 검증 |
| --- | --- |
| 모델 구조(`model.py`) | `python train.py`를 다시 돌려 테스트 정확도 약 99%를 확인한다. |
| 전처리(`preprocess()`) | 아래 스니펫으로 전처리 경로를 통과시켜 90% 이상을 확인한다. |
| GUI 동작(`app.py`) | 앱을 실행해 숫자를 그리고 인식, 지우기가 동작하는지 눈으로 확인한다. |
| 실행 방식(`app.bat`, 바로가기) | 다른 작업 폴더에서 실행해도 창이 뜨는지 확인한다. |

```bash
python -c "
import torch; from torchvision import datasets; from PIL import Image
from model import MnistCNN; from app import preprocess
m = MnistCNN(); m.load_state_dict(torch.load('mnist_cnn.pt', map_location='cpu')); m.eval()
ds = datasets.MNIST(root='./data', train=False)
ok = sum(m(preprocess(ds[i][0].resize((280, 280), Image.NEAREST))).argmax(1).item() == ds[i][1] for i in range(200))
print(f'{ok / 2:.1f}%')"
```

학습은 CPU에서 약 10분이 걸리므로, 모델을 건드리지 않은 변경에 재학습을 요구하지 않습니다.

## 건드리면 안 되는 것 (전역 §3 외과적 변경)

아래 항목은 그렇게 만든 이유가 있습니다. 취향에 맞지 않아 보여도 요청 없이 되돌리지 않습니다.

- **정규화 상수는 `train.py`에만 있습니다.** `MNIST_MEAN`, `MNIST_STD`를 `app.py`가 import해서 씁니다. 값을 `app.py`에 다시 적으면 학습과 추론의 정규화가 어긋나 인식률이 떨어집니다.
- **`preprocess()`의 20x20 중앙 정렬은 필수입니다.** MNIST 원본이 그 형식이라, 캔버스를 그냥 28x28로 줄이는 코드로 바꾸면 실제 손글씨 인식률이 크게 떨어집니다.
- **`app.py`는 `__file__` 기준 경로를 씁니다.** 바로가기나 더블클릭으로 실행하면 작업 폴더가 달라지므로 상대 경로로 되돌리지 않습니다.
- **`app.bat`은 CRLF 줄바꿈에 CP949 인코딩입니다.** LF나 UTF-8로 저장하면 cmd.exe가 `rem` 주석 줄을 명령으로 잘못 읽습니다. `.gitattributes`가 이 줄바꿈을 고정합니다.

## 저장소 밖에 있는 것

- `data/`: MNIST 원본 약 64MB. `train.py`가 자동으로 내려받으며 `.gitignore`로 제외했습니다.
- 바탕 화면 바로가기 `손글씨 숫자 인식기.lnk`: 대상 `pythonw.exe`, 인수 `"C:\study01_mnist\app.py"`, 작업 폴더 `C:\study01_mnist`, 아이콘 `app.ico,0`으로 WScript.Shell을 써서 만듭니다. 작업 표시줄 고정은 Windows 정책상 사용자가 직접 해야 합니다.

## 작업 전에 확인할 것 (전역 §1, §2)

- 재학습이 필요한 변경인지 먼저 밝힙니다. 10분이 드는 작업을 조용히 시작하지 않습니다.
- 인식률 개선 요청은 해석이 갈립니다. 전처리 개선, 학습 에폭 증가, 모델 확장 중 무엇을 뜻하는지 확인하고 시작합니다.
- 이 프로젝트는 학습용 예제입니다. 설정 파일, 플러그인 구조, 예외 처리 계층처럼 요청하지 않은 일반화를 넣지 않습니다.
