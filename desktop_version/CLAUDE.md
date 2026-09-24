<!-- 2026-09-25 00:50 KST -->
# CLAUDE.md (desktop_version)

Tkinter 캔버스에 마우스로 그린 숫자를 PyTorch CNN으로 인식하는 Windows 데스크톱 앱이다. 저장소 전체에 걸친 규칙은 최상위 `CLAUDE.md`에 있다.

## 명령어

```bash
pip install torch torchvision pillow      # 의존성 (CPU 버전 torch로 충분)
python train.py                           # MNIST 학습 후 mnist_cnn.pt 저장 (CPU 기준 약 10분, 5 에폭)
python app.py                             # 손글씨 인식 GUI 실행 (mnist_cnn.pt가 있어야 함)
python export_weights.py                  # 웹 버전이 쓸 weights.json, golden.json 생성
python make_icon.py                       # app.ico 재생성 (아이콘 모양을 바꿀 때)
python -m pytest                          # 내보내기 검증 테스트
```

Git Bash에서 한글 출력이 깨지면 `PYTHONIOENCODING=utf-8 python ...`으로 실행한다.

## 변경별 검증 방법

| 무엇을 고쳤나 | 검증 |
| --- | --- |
| 모델 구조(`model.py`) | `python train.py`로 재학습해 테스트 정확도 약 99%를 확인한다. 이어서 `export_weights.py`를 다시 돌리고 웹 골든 테스트까지 통과시킨다. |
| 전처리(`app.py`의 `preprocess()`) | 아래 스니펫으로 90% 이상을 확인한다. |
| 내보내기(`export_weights.py`) | `python -m pytest`와 `cd ../web_version && node --test tests/` 양쪽을 통과시킨다. |
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

## 건드리면 안 되는 것

아래는 그렇게 만든 이유가 있다. 취향에 맞지 않아 보여도 요청 없이 되돌리지 않는다.

- **정규화 상수는 `train.py`에만 있다.** `app.py`와 `export_weights.py`가 `MNIST_MEAN`, `MNIST_STD`를 import해서 쓴다. 값을 다시 적으면 학습과 추론이 어긋난다.
- **`preprocess()`의 20x20 중앙 정렬은 필수다.** MNIST 원본이 그 형식이라, 캔버스를 그냥 28x28로 줄이면 실제 손글씨 인식률이 크게 떨어진다.
- **`app.py`는 `__file__` 기준 경로를 쓴다.** 바로가기나 더블클릭으로 실행하면 작업 폴더가 달라지므로 상대 경로로 되돌리지 않는다.
- **`app.bat`은 CRLF 줄바꿈에 CP949 인코딩이다.** LF나 UTF-8로 저장하면 cmd.exe가 `rem` 주석 줄을 명령으로 잘못 읽는다. 최상위 `.gitattributes`가 이 줄바꿈을 고정한다.

## 저장소 밖에 있는 것

- `data/`: MNIST 원본 약 64MB. `train.py`가 자동으로 내려받으며 `.gitignore`로 제외했다.
- 바탕 화면 바로가기 `손글씨 숫자 인식기.lnk`: 대상 `pythonw.exe`, 인수 `"C:\study01_mnist\desktop_version\app.py"`, 작업 폴더 `C:\study01_mnist\desktop_version`, 아이콘 `app.ico,0`으로 WScript.Shell을 써서 만든다. 폴더를 나누면서 경로가 바뀌었으므로 예전 바로가기는 다시 만들어야 한다. 작업 표시줄 고정은 Windows 정책상 사용자가 직접 해야 한다.
