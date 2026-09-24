<!-- 2026-09-24 16:57 KST -->
# 웹 버전과 데스크톱 버전 분리 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 기존 손글씨 인식기를 `desktop_version`으로 옮기고, 같은 가중치로 브라우저에서 추론하는 `web_version`을 순수 자바스크립트로 새로 만들어 GitHub Pages에 배포한다.

**Architecture:** 의존 방향은 한쪽이다. `desktop_version/export_weights.py`가 `mnist_cnn.pt`를 읽어 `web_version/weights.json`과 검증용 `web_version/golden.json`을 만들고, 웹은 그 JSON만 받아 스스로 추론한다. 웹의 추론 엔진은 합성곱, 최대 풀링, 완전연결, 소프트맥스를 직접 구현하며, PyTorch와 같은 결과를 내는지 골든 테스트로 판정한다.

**Tech Stack:** Python 3.12.1, PyTorch 2.14.0+cpu, pytest 9.1.1, Node.js v24.19.0(내장 테스트 러너), 브라우저 표준 API만 쓰는 ES 모듈.

**Spec:** 별도 스펙 문서는 사용자 요청으로 생략했다. 설계 결정은 아래 "설계 결정" 절에 담았다.

## Global Constraints

- 웹 버전은 런타임과 테스트 모두 외부 라이브러리를 쓰지 않는다. 테스트는 Node 내장 러너 `node --test`만 쓴다.
- 모든 코드, 주석, UI 문자열, 문서는 한글로 쓴다.
- 새로 만드는 파일은 첫머리에 생성 일시를 `2026-09-24 16:57 KST` 형식의 주석으로 남긴다. 시각은 `Get-Date -Format "yyyy-MM-dd HH:mm"`으로 실제 조회한다.
- 정규화 상수는 `MNIST_MEAN = 0.1307`, `MNIST_STD = 0.3081`이다. 각 버전 안에서는 한 곳에만 정의하고 나머지는 import한다.
- 골든 테스트 허용 오차는 로짓의 최대 절대 오차 `1e-4`다.
- 열거에는 가운뎃점을 쓰지 않고 쉼표를 쓴다. 완결된 문장인 메시지는 마침표로 끝낸다. 보조용언은 띄어 쓴다.
- `weights.json`과 `golden.json`은 생성물이지만 GitHub Pages가 서빙해야 하므로 `.gitignore`에 넣지 않고 커밋한다.

---

## 설계 결정

**가중치 전달은 JSON 텍스트로 한다.** 약 3.5MB이며 GitHub Pages의 gzip 압축을 거치면 전송량은 2MB 안팎이다. 브라우저 개발자 도구에서 숫자를 그대로 확인할 수 있어 학습용으로 투명하다.

**골든 테스트는 28x28 입력부터 비교한다.** 캔버스 축소는 PIL의 LANCZOS와 브라우저 구현이 달라 픽셀 단위로 일치시킬 수 없다. 그래서 MNIST 테스트 이미지(이미 28x28)를 양쪽에 같은 값으로 넣고 로짓을 비교해 추론 엔진 자체의 정확성만 판정한다. 축소 단계는 별도 단위 테스트로 덮는다.

**축소는 캔버스 API 대신 직접 구현한다.** `drawImage`의 축소 결과는 브라우저마다 다르다. 박스 필터 평균을 직접 짜면 어디서나 같은 값이 나오고 Node에서도 테스트할 수 있다.

**GitHub Pages는 Actions 워크플로로 배포한다.** 브랜치 배포는 저장소 루트나 `/docs`만 서빙할 수 있어 `web_version/`을 올릴 수 없다.

## File Structure

```
Study01_MNIST/
├── CLAUDE.md                       # 수정: 두 버전 공통 규칙만
├── README.md                       # 수정: 저장소 전체 소개
├── claude 전역.md                  # 그대로
├── .gitignore                      # 수정: data/ 경로를 desktop_version/data/로
├── .gitattributes                  # 수정: app.bat 경로
├── .github/workflows/pages.yml     # 신규: web_version 배포
├── desktop_version/
│   ├── CLAUDE.md                   # 신규: 데스크톱 전용 지침
│   ├── export_weights.py           # 신규: 가중치와 골든 데이터 내보내기
│   ├── test_export_weights.py      # 신규: 위 스크립트 검증
│   ├── model.py, train.py, app.py, make_icon.py   # 이동
│   ├── app.bat, app.ico, mnist_cnn.pt             # 이동
│   └── data/                       # 이동 (커밋 대상 아님)
└── web_version/
    ├── CLAUDE.md                   # 신규: 웹 전용 지침
    ├── index.html                  # 신규: 캔버스와 버튼
    ├── style.css                   # 신규
    ├── package.json                # 신규: {"type":"module"} 만, 의존성 없음
    ├── weights.json                # 신규(생성물, 커밋함)
    ├── golden.json                 # 신규(생성물, 커밋함)
    ├── src/model.js                # 신규: 추론 엔진
    ├── src/preprocess.js           # 신규: 전처리
    ├── src/app.js                  # 신규: 화면 연결
    └── tests/model.test.js, tests/preprocess.test.js   # 신규
```

각 파일의 책임은 하나다. `model.js`는 숫자 계산만 하고 DOM을 모른다. `preprocess.js`는 픽셀 배열만 다루고 모델을 모른다. `app.js`만 브라우저 API를 안다. 덕분에 앞의 두 파일은 Node에서 테스트할 수 있다.

---

### Task 1: 데스크톱 코드를 desktop_version으로 옮긴다

**Files:**
- Move: `model.py`, `train.py`, `app.py`, `make_icon.py`, `app.bat`, `app.ico`, `mnist_cnn.pt` → `desktop_version/`
- Move: `data/` → `desktop_version/data/`
- Create: `desktop_version/CLAUDE.md`
- Modify: `.gitignore`, `.gitattributes`

**Interfaces:**
- Consumes: 없음
- Produces: `desktop_version/mnist_cnn.pt` 경로. Task 2의 `export_weights.py`가 이 경로를 읽는다.

- [ ] **Step 1: 이동 전 기준값을 확인한다**

Run:
```bash
cd /c/study01_mnist && PYTHONIOENCODING=utf-8 python -c "
import torch
from model import MnistCNN
m = MnistCNN(); m.load_state_dict(torch.load('mnist_cnn.pt', map_location='cpu'))
print('로딩 성공', sum(p.numel() for p in m.parameters()))"
```
Expected: `로딩 성공 421642`

- [ ] **Step 2: git mv로 옮긴다**

`git mv`를 써야 이력이 이어진다. `data/`는 추적 대상이 아니므로 일반 `mv`로 옮긴다.

```bash
cd /c/study01_mnist
mkdir -p desktop_version
git mv model.py train.py app.py make_icon.py app.bat app.ico mnist_cnn.pt desktop_version/
mv data desktop_version/data
rm -rf __pycache__
```

- [ ] **Step 3: .gitignore와 .gitattributes의 경로를 고친다**

`.gitignore` 전체를 다음으로 바꾼다.

```
# 2026-09-24 12:35 KST
# MNIST 원본 데이터(약 64MB)는 train.py가 자동으로 내려받으므로 저장소에 두지 않는다
desktop_version/data/

__pycache__/
*.pyc
```

`.gitattributes` 전체를 다음으로 바꾼다.

```
# 2026-09-24 12:35 KST
# app.bat은 CRLF 줄바꿈이어야 cmd.exe가 주석 줄을 올바르게 건너뛴다
desktop_version/app.bat text eol=crlf
```

- [ ] **Step 4: 옮긴 뒤에도 동작하는지 확인한다**

`app.py`는 `__file__` 기준 경로를 쓰므로 수정 없이 동작해야 한다. 이것이 이 단계의 회귀 검사다.

Run:
```bash
cd /c/study01_mnist/desktop_version && PYTHONIOENCODING=utf-8 python -c "
import os, torch
from model import MnistCNN
from app import preprocess, WEIGHTS_PATH
from torchvision import datasets
from PIL import Image
print('가중치 경로 존재:', os.path.exists(WEIGHTS_PATH))
m = MnistCNN(); m.load_state_dict(torch.load(WEIGHTS_PATH, map_location='cpu')); m.eval()
ds = datasets.MNIST(root='./data', train=False)
ok = sum(m(preprocess(ds[i][0].resize((280, 280), Image.NEAREST))).argmax(1).item() == ds[i][1] for i in range(200))
print(f'전처리 경유 정확도: {ok / 2:.1f}%')"
```
Expected: `가중치 경로 존재: True` 와 `전처리 경유 정확도: 92.0%`

- [ ] **Step 5: 배치 파일도 확인한다**

Run: `cmd /c "C:\study01_mnist\desktop_version\app.bat"`
Expected: 콘솔 오류 없이 창이 뜬다. 확인한 뒤 창을 닫는다.

- [ ] **Step 6: desktop_version/CLAUDE.md를 만든다**

최상위 `CLAUDE.md`에 있던 데스크톱 관련 내용을 이 파일로 옮긴다. 파일 첫머리에 생성 일시를 넣고 다음을 담는다.

- 명령어: `python train.py`, `python app.py`, `python make_icon.py`, `python export_weights.py`, `python -m pytest`
- 검증: 학습은 테스트 정확도 약 99%, 전처리는 Step 4의 스니펫으로 90% 이상
- 건드리면 안 되는 것: 정규화 상수는 `train.py`에만 정의, `preprocess()`의 20x20 중앙 정렬, `__file__` 기준 경로, `app.bat`의 CRLF와 CP949
- `export_weights.py`나 모델 구조를 고치면 `web_version`의 골든 테스트를 다시 돌려야 한다는 점
- 바탕 화면 바로가기 재생성 방법. 인수 경로가 `desktop_version/app.py`로 바뀌었다는 점

- [ ] **Step 7: 커밋한다**

```bash
cd /c/study01_mnist
git add -A
git commit -m "데스크톱 코드를 desktop_version 폴더로 이동

파일 위치만 옮기고 코드는 고치지 않았다. app.py가 __file__ 기준
경로를 쓰고 있어 이동만으로 동작한다.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 2: 가중치와 골든 데이터를 JSON으로 내보낸다

**Files:**
- Create: `desktop_version/export_weights.py`
- Test: `desktop_version/test_export_weights.py`
- Produces: `web_version/weights.json`, `web_version/golden.json`

**Interfaces:**
- Consumes: `desktop_version/mnist_cnn.pt` (Task 1)
- Produces: 두 JSON 파일의 구조. Task 3이 이 구조를 그대로 읽는다.

  `weights.json`은 파라미터 이름을 키로 갖는 객체다.
  ```json
  {"conv1.weight": {"shape": [32, 1, 3, 3], "data": [0.1, -0.2]},
   "conv1.bias": {"shape": [32], "data": []},
   "conv2.weight": {"shape": [64, 32, 3, 3], "data": []},
   "conv2.bias": {"shape": [64], "data": []},
   "fc1.weight": {"shape": [128, 3136], "data": []},
   "fc1.bias": {"shape": [128], "data": []},
   "fc2.weight": {"shape": [10, 128], "data": []},
   "fc2.bias": {"shape": [10], "data": []}}
  ```
  `data`는 PyTorch 텐서를 C 순서로 편 1차원 배열이다.

  `golden.json`은 다음 구조다.
  ```json
  {"images": [[0, 0, 253]],
   "labels": [7],
   "logits": [[-3.1, 0.5]]}
  ```
  `images`는 장마다 784개의 0~255 정수, `logits`는 장마다 10개의 실수이며 소프트맥스 적용 전 값이다. 장수는 20이다.

- [ ] **Step 1: 실패하는 테스트를 쓴다**

Create `desktop_version/test_export_weights.py`:

```python
# 생성 일시 주석은 파일을 만들 때 실제 시각으로 적는다
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
        assert exported[name]["data"] == tensor.flatten().tolist()


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
```

- [ ] **Step 2: 테스트가 실패하는 것을 확인한다**

Run: `cd /c/study01_mnist/desktop_version && python -m pytest test_export_weights.py -v`
Expected: FAIL. `export_weights.py`가 없어 `subprocess.run`이 파일을 찾지 못한다.

- [ ] **Step 3: export_weights.py를 쓴다**

Create `desktop_version/export_weights.py`:

```python
# 생성 일시 주석은 파일을 만들 때 실제 시각으로 적는다
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
    """state_dict를 이름, 모양, 1차원 배열 구조의 JSON으로 저장한다."""
    payload = {
        name: {"shape": list(tensor.shape), "data": tensor.flatten().tolist()}
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
```

- [ ] **Step 4: 테스트가 통과하는 것을 확인한다**

Run: `cd /c/study01_mnist/desktop_version && python -m pytest test_export_weights.py -v`
Expected: PASS 2개

- [ ] **Step 5: 커밋한다**

```bash
cd /c/study01_mnist
git add desktop_version/export_weights.py desktop_version/test_export_weights.py web_version/weights.json web_version/golden.json
git commit -m "가중치와 골든 데이터를 JSON으로 내보내는 스크립트 추가

웹 버전이 읽을 weights.json과, 추론 결과를 비교할 기준인
golden.json을 만든다.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 3: 순수 자바스크립트 추론 엔진을 만든다

**Files:**
- Create: `web_version/package.json`
- Create: `web_version/src/model.js`
- Test: `web_version/tests/model.test.js`

**Interfaces:**
- Consumes: `web_version/weights.json`, `web_version/golden.json` (Task 2)
- Produces: `model.js`가 내보내는 이름들. Task 5의 `app.js`가 `MnistCNN`과 `softmax`를 쓴다.
  ```js
  export function conv2d(input, inChannels, size, weight, bias, outChannels) // → Float32Array(outChannels*size*size)
  export function relu(array)                                                // 제자리 수정, array 반환
  export function maxPool2x2(input, channels, size)                          // → Float32Array(channels*(size/2)**2)
  export function linear(input, weight, bias, inFeatures, outFeatures)       // → Float32Array(outFeatures)
  export function softmax(logits)                                            // → Float32Array(logits.length)
  export class MnistCNN {
    constructor(weights)  // weights: weights.json을 JSON.parse한 객체
    forward(x)            // x: Float32Array(784) 정규화된 입력 → Float32Array(10) 로짓
  }
  ```

- [ ] **Step 1: package.json을 만든다**

Node가 `.js` 파일을 ES 모듈로 다루게 하는 최소 설정이다. 의존성은 없다.

Create `web_version/package.json`:
```json
{
  "name": "mnist-web",
  "private": true,
  "type": "module"
}
```

- [ ] **Step 2: 실패하는 테스트를 쓴다**

Create `web_version/tests/model.test.js`:

```js
// 생성 일시 주석은 파일을 만들 때 실제 시각으로 적는다
// 추론 엔진이 PyTorch와 같은 결과를 내는지 검증한다.

import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { conv2d, relu, maxPool2x2, linear, softmax, MnistCNN } from '../src/model.js';

const MNIST_MEAN = 0.1307;
const MNIST_STD = 0.3081;

const weights = JSON.parse(readFileSync(new URL('../weights.json', import.meta.url), 'utf-8'));
const golden = JSON.parse(readFileSync(new URL('../golden.json', import.meta.url), 'utf-8'));

/** 골든 이미지 한 장을 정규화된 모델 입력으로 바꾼다. */
function toInput(image) {
  const x = new Float32Array(784);
  for (let i = 0; i < 784; i++) {
    x[i] = (image[i] / 255 - MNIST_MEAN) / MNIST_STD;
  }
  return x;
}

test('relu는 음수를 0으로 만든다', () => {
  const a = Float32Array.from([-1, 0, 2]);
  relu(a);
  assert.deepEqual(Array.from(a), [0, 0, 2]);
});

test('maxPool2x2는 2x2 구역의 최댓값을 고른다', () => {
  // 채널 1개, 2x2 입력이므로 1x1이 나온다
  const out = maxPool2x2(Float32Array.from([1, 5, 3, 2]), 1, 2);
  assert.deepEqual(Array.from(out), [5]);
});

test('linear는 가중치 행과 입력의 내적에 편향을 더한다', () => {
  // 입력 2개, 출력 2개. weight는 행 우선으로 편 배열이다.
  const out = linear(
    Float32Array.from([1, 2]),
    Float32Array.from([1, 0, 0, 1]),
    Float32Array.from([10, 20]),
    2,
    2,
  );
  assert.deepEqual(Array.from(out), [11, 22]);
});

test('conv2d는 3x3 커널에 패딩 1을 적용한다', () => {
  // 1채널 2x2 입력에 값이 모두 1인 커널을 적용하면 유효한 이웃 4개의 합이 된다
  const out = conv2d(
    Float32Array.from([1, 1, 1, 1]),
    1,
    2,
    Float32Array.from(new Array(9).fill(1)),
    Float32Array.from([0]),
    1,
  );
  assert.deepEqual(Array.from(out), [4, 4, 4, 4]);
});

test('softmax 결과의 합은 1이다', () => {
  const p = softmax(Float32Array.from([1, 2, 3]));
  let sum = 0;
  for (const value of p) sum += value;
  assert.ok(Math.abs(sum - 1) < 1e-6);
  assert.ok(p[2] > p[1] && p[1] > p[0]);
});

test('골든 데이터의 로짓이 PyTorch와 1e-4 이내로 일치한다', () => {
  const model = new MnistCNN(weights);
  let maxDiff = 0;

  for (let i = 0; i < golden.images.length; i++) {
    const logits = model.forward(toInput(golden.images[i]));
    for (let c = 0; c < 10; c++) {
      maxDiff = Math.max(maxDiff, Math.abs(logits[c] - golden.logits[i][c]));
    }
  }

  assert.ok(maxDiff < 1e-4, `최대 오차 ${maxDiff}가 허용치 1e-4를 넘었다`);
});

test('예측 숫자가 PyTorch와 같다', () => {
  // 정답 라벨이 아니라 PyTorch의 예측과 비교한다. 모델이 틀린 장이 있어도
  // 두 구현이 똑같이 틀려야 맞는 것이며, 라벨과 비교하면 모델 정확도 때문에
  // 구현이 멀쩡해도 간헐적으로 실패한다.
  const model = new MnistCNN(weights);
  const argmax = (values) => {
    let best = 0;
    for (let c = 1; c < 10; c++) if (values[c] > values[best]) best = c;
    return best;
  };

  for (let i = 0; i < golden.images.length; i++) {
    const predicted = argmax(model.forward(toInput(golden.images[i])));
    assert.equal(predicted, argmax(golden.logits[i]), `${i}번째 이미지의 예측이 다르다`);
  }
});
```

- [ ] **Step 3: 테스트가 실패하는 것을 확인한다**

Run: `cd /c/study01_mnist/web_version && node --test tests/`
Expected: FAIL. `../src/model.js`를 찾을 수 없다는 오류가 난다.

- [ ] **Step 4: model.js를 쓴다**

텐서 배치는 PyTorch와 같은 C 순서다. 채널 `c`, 행 `y`, 열 `x`의 위치는 `(c * size + y) * size + x`다.

Create `web_version/src/model.js`:

```js
// 생성 일시 주석은 파일을 만들 때 실제 시각으로 적는다
// MNIST 손글씨 숫자 인식 CNN의 추론 부분을 외부 라이브러리 없이 구현한다.
// 텐서는 모두 1차원 Float32Array이며 PyTorch와 같은 C 순서로 담는다.

/** 3x3 커널에 패딩 1을 적용하는 합성곱. 입력과 출력의 가로세로 크기가 같다. */
export function conv2d(input, inChannels, size, weight, bias, outChannels) {
  const output = new Float32Array(outChannels * size * size);

  for (let oc = 0; oc < outChannels; oc++) {
    for (let oy = 0; oy < size; oy++) {
      for (let ox = 0; ox < size; ox++) {
        let sum = bias[oc];

        for (let ic = 0; ic < inChannels; ic++) {
          for (let ky = 0; ky < 3; ky++) {
            const iy = oy + ky - 1;
            if (iy < 0 || iy >= size) continue;  // 패딩 구역은 0이므로 건너뛴다

            for (let kx = 0; kx < 3; kx++) {
              const ix = ox + kx - 1;
              if (ix < 0 || ix >= size) continue;

              sum += input[(ic * size + iy) * size + ix]
                   * weight[((oc * inChannels + ic) * 3 + ky) * 3 + kx];
            }
          }
        }

        output[(oc * size + oy) * size + ox] = sum;
      }
    }
  }

  return output;
}

/** 음수를 0으로 바꾼다. 배열을 제자리에서 고친다. */
export function relu(array) {
  for (let i = 0; i < array.length; i++) {
    if (array[i] < 0) array[i] = 0;
  }
  return array;
}

/** 2x2 최대 풀링. 가로세로가 절반이 된다. */
export function maxPool2x2(input, channels, size) {
  const half = size / 2;
  const output = new Float32Array(channels * half * half);

  for (let c = 0; c < channels; c++) {
    const base = c * size * size;

    for (let y = 0; y < half; y++) {
      for (let x = 0; x < half; x++) {
        const topLeft = base + 2 * y * size + 2 * x;
        output[(c * half + y) * half + x] = Math.max(
          input[topLeft],
          input[topLeft + 1],
          input[topLeft + size],
          input[topLeft + size + 1],
        );
      }
    }
  }

  return output;
}

/** 완전연결 계층. weight는 (출력, 입력) 모양을 행 우선으로 편 배열이다. */
export function linear(input, weight, bias, inFeatures, outFeatures) {
  const output = new Float32Array(outFeatures);

  for (let o = 0; o < outFeatures; o++) {
    let sum = bias[o];
    const row = o * inFeatures;
    for (let i = 0; i < inFeatures; i++) {
      sum += weight[row + i] * input[i];
    }
    output[o] = sum;
  }

  return output;
}

/** 로짓을 확률로 바꾼다. 지수 폭주를 막으려고 최댓값을 빼고 계산한다. */
export function softmax(logits) {
  let max = -Infinity;
  for (let i = 0; i < logits.length; i++) {
    if (logits[i] > max) max = logits[i];
  }

  const output = new Float32Array(logits.length);
  let sum = 0;
  for (let i = 0; i < logits.length; i++) {
    output[i] = Math.exp(logits[i] - max);
    sum += output[i];
  }
  for (let i = 0; i < output.length; i++) {
    output[i] /= sum;
  }

  return output;
}

/** 학습된 가중치로 추론만 하는 CNN. 드롭아웃은 추론에서 항등이므로 빼 두었다. */
export class MnistCNN {
  constructor(weights) {
    const pick = (name) => Float32Array.from(weights[name].data);

    this.conv1Weight = pick('conv1.weight');
    this.conv1Bias = pick('conv1.bias');
    this.conv2Weight = pick('conv2.weight');
    this.conv2Bias = pick('conv2.bias');
    this.fc1Weight = pick('fc1.weight');
    this.fc1Bias = pick('fc1.bias');
    this.fc2Weight = pick('fc2.weight');
    this.fc2Bias = pick('fc2.bias');
  }

  /** 정규화된 28x28 입력(784개)을 받아 10개 로짓을 돌려준다. */
  forward(x) {
    let h = relu(conv2d(x, 1, 28, this.conv1Weight, this.conv1Bias, 32));
    h = maxPool2x2(h, 32, 28);                                  // 28 -> 14

    h = relu(conv2d(h, 32, 14, this.conv2Weight, this.conv2Bias, 64));
    h = maxPool2x2(h, 64, 14);                                  // 14 -> 7

    const hidden = relu(linear(h, this.fc1Weight, this.fc1Bias, 3136, 128));
    return linear(hidden, this.fc2Weight, this.fc2Bias, 128, 10);
  }
}
```

- [ ] **Step 5: 테스트가 통과하는 것을 확인한다**

Run: `cd /c/study01_mnist/web_version && node --test tests/`
Expected: PASS 7개. 골든 테스트가 통과해야 한다. 실패하면 오차 값이 메시지에 찍히므로 어느 계층이 어긋났는지 좁혀 들어간다.

- [ ] **Step 6: 커밋한다**

```bash
cd /c/study01_mnist
git add web_version/package.json web_version/src/model.js web_version/tests/model.test.js
git commit -m "순수 자바스크립트 CNN 추론 엔진 추가

합성곱, 최대 풀링, 완전연결, 소프트맥스를 직접 구현했다. 골든
테스트로 PyTorch 로짓과 1e-4 이내로 일치함을 확인한다.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 4: 캔버스 전처리를 만든다

**Files:**
- Create: `web_version/src/preprocess.js`
- Test: `web_version/tests/preprocess.test.js`

**Interfaces:**
- Consumes: 없음. 순수 함수만 있다.
- Produces:
  ```js
  export const MNIST_MEAN  // 0.1307
  export const MNIST_STD   // 0.3081
  export function boundingBox(pixels, width, height)        // → {x0, y0, x1, y1} | null (x1, y1은 포함)
  export function crop(pixels, width, box)                  // → {data: Float32Array, width, height}
  export function resize(source, sourceWidth, sourceHeight, targetWidth, targetHeight) // → Float32Array
  export function centerOn28(source, width, height)         // → Float32Array(784)
  export function preprocess(pixels, width, height)         // → Float32Array(784) | null
  ```
  `pixels`는 0~255 밝기값 배열이다. Task 5의 `app.js`는 `preprocess`만 쓴다.

- [ ] **Step 1: 실패하는 테스트를 쓴다**

Create `web_version/tests/preprocess.test.js`:

```js
// 생성 일시 주석은 파일을 만들 때 실제 시각으로 적는다
// 캔버스 픽셀을 MNIST 형식으로 바꾸는 전처리를 검증한다.

import test from 'node:test';
import assert from 'node:assert/strict';
import {
  MNIST_MEAN,
  MNIST_STD,
  boundingBox,
  crop,
  resize,
  centerOn28,
  preprocess,
} from '../src/preprocess.js';

test('빈 이미지의 경계 상자는 null이다', () => {
  assert.equal(boundingBox(new Float32Array(16), 4, 4), null);
});

test('경계 상자는 값이 있는 구역만 감싼다', () => {
  // 4x4 가운데 2x2에만 값이 있다
  const pixels = Float32Array.from([
    0, 0, 0, 0,
    0, 255, 255, 0,
    0, 255, 255, 0,
    0, 0, 0, 0,
  ]);
  assert.deepEqual(boundingBox(pixels, 4, 4), { x0: 1, y0: 1, x1: 2, y1: 2 });
});

test('crop은 경계 상자 안쪽만 잘라낸다', () => {
  const pixels = Float32Array.from([
    0, 0, 0,
    0, 9, 0,
    0, 0, 0,
  ]);
  const result = crop(pixels, 3, { x0: 1, y0: 1, x1: 1, y1: 1 });
  assert.equal(result.width, 1);
  assert.equal(result.height, 1);
  assert.deepEqual(Array.from(result.data), [9]);
});

test('resize는 축소할 때 구역 평균을 낸다', () => {
  // 2x2를 1x1로 줄이면 네 값의 평균이 나온다
  const out = resize(Float32Array.from([0, 255, 255, 0]), 2, 2, 1, 1);
  assert.ok(Math.abs(out[0] - 127.5) < 1e-6);
});

test('resize는 같은 크기면 값을 보존한다', () => {
  const out = resize(Float32Array.from([1, 2, 3, 4]), 2, 2, 2, 2);
  assert.deepEqual(Array.from(out), [1, 2, 3, 4]);
});

test('centerOn28은 28x28 가운데에 배치한다', () => {
  // 2x2 이미지는 (13, 13)에서 시작한다
  const out = centerOn28(Float32Array.from([255, 255, 255, 255]), 2, 2);
  assert.equal(out.length, 784);
  assert.equal(out[13 * 28 + 13], 255);
  assert.equal(out[14 * 28 + 14], 255);
  assert.equal(out[0], 0);
});

test('preprocess는 빈 입력에 null을 돌려준다', () => {
  assert.equal(preprocess(new Float32Array(280 * 280), 280, 280), null);
});

test('preprocess는 정규화된 784개 값을 돌려준다', () => {
  // 280x280 가운데에 100x100 사각형을 그린다
  const pixels = new Float32Array(280 * 280);
  for (let y = 90; y < 190; y++) {
    for (let x = 90; x < 190; x++) pixels[y * 280 + x] = 255;
  }

  const result = preprocess(pixels, 280, 280);
  assert.equal(result.length, 784);

  // 배경 0은 (0 - 평균) / 표준편차로 바뀐다
  const background = (0 - MNIST_MEAN) / MNIST_STD;
  assert.ok(Math.abs(result[0] - background) < 1e-6);

  // 가운데는 밝으므로 배경보다 크다
  assert.ok(result[14 * 28 + 14] > background);
});

test('preprocess는 그린 위치가 달라도 같은 결과를 낸다', () => {
  // 같은 크기의 사각형을 왼쪽 위와 오른쪽 아래에 그리면 중앙 정렬 뒤 같아진다
  const draw = (offset) => {
    const pixels = new Float32Array(280 * 280);
    for (let y = offset; y < offset + 60; y++) {
      for (let x = offset; x < offset + 60; x++) pixels[y * 280 + x] = 255;
    }
    return preprocess(pixels, 280, 280);
  };

  const a = draw(10);
  const b = draw(200);
  for (let i = 0; i < 784; i++) {
    assert.ok(Math.abs(a[i] - b[i]) < 1e-6, `${i}번째 값이 다르다`);
  }
});
```

- [ ] **Step 2: 테스트가 실패하는 것을 확인한다**

Run: `cd /c/study01_mnist/web_version && node --test tests/preprocess.test.js`
Expected: FAIL. `../src/preprocess.js`를 찾을 수 없다.

- [ ] **Step 3: preprocess.js를 쓴다**

Create `web_version/src/preprocess.js`:

```js
// 생성 일시 주석은 파일을 만들 때 실제 시각으로 적는다
// 캔버스에 그린 그림을 MNIST 형식(28x28, 숫자를 20x20 상자에 맞춰 중앙 정렬)으로 바꾼다.
// 데스크톱 버전의 preprocess()와 같은 절차를 따른다.

export const MNIST_MEAN = 0.1307;
export const MNIST_STD = 0.3081;

const DIGIT_BOX = 20;   // 숫자를 담는 상자의 한 변
const CANVAS_28 = 28;   // 모델 입력 크기

/** 값이 0보다 큰 픽셀을 모두 감싸는 경계 상자를 찾는다. 아무것도 없으면 null이다. */
export function boundingBox(pixels, width, height) {
  let x0 = width;
  let y0 = height;
  let x1 = -1;
  let y1 = -1;

  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      if (pixels[y * width + x] > 0) {
        if (x < x0) x0 = x;
        if (x > x1) x1 = x;
        if (y < y0) y0 = y;
        if (y > y1) y1 = y;
      }
    }
  }

  return x1 < 0 ? null : { x0, y0, x1, y1 };
}

/** 경계 상자 안쪽만 잘라낸다. */
export function crop(pixels, width, box) {
  const cropWidth = box.x1 - box.x0 + 1;
  const cropHeight = box.y1 - box.y0 + 1;
  const data = new Float32Array(cropWidth * cropHeight);

  for (let y = 0; y < cropHeight; y++) {
    for (let x = 0; x < cropWidth; x++) {
      data[y * cropWidth + x] = pixels[(box.y0 + y) * width + box.x0 + x];
    }
  }

  return { data, width: cropWidth, height: cropHeight };
}

/** 박스 필터 평균으로 크기를 바꾼다. 브라우저마다 결과가 다른 drawImage 대신 직접 계산한다. */
export function resize(source, sourceWidth, sourceHeight, targetWidth, targetHeight) {
  const output = new Float32Array(targetWidth * targetHeight);
  const scaleX = sourceWidth / targetWidth;
  const scaleY = sourceHeight / targetHeight;

  for (let y = 0; y < targetHeight; y++) {
    const startY = Math.floor(y * scaleY);
    const endY = Math.max(startY + 1, Math.ceil((y + 1) * scaleY));

    for (let x = 0; x < targetWidth; x++) {
      const startX = Math.floor(x * scaleX);
      const endX = Math.max(startX + 1, Math.ceil((x + 1) * scaleX));

      let sum = 0;
      let count = 0;
      for (let sy = startY; sy < endY && sy < sourceHeight; sy++) {
        for (let sx = startX; sx < endX && sx < sourceWidth; sx++) {
          sum += source[sy * sourceWidth + sx];
          count++;
        }
      }

      output[y * targetWidth + x] = count > 0 ? sum / count : 0;
    }
  }

  return output;
}

/** 28x28 검은 배경의 가운데에 배치한다. */
export function centerOn28(source, width, height) {
  const output = new Float32Array(CANVAS_28 * CANVAS_28);
  const offsetX = Math.floor((CANVAS_28 - width) / 2);
  const offsetY = Math.floor((CANVAS_28 - height) / 2);

  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      output[(offsetY + y) * CANVAS_28 + offsetX + x] = source[y * width + x];
    }
  }

  return output;
}

/** 캔버스 픽셀을 모델에 넣을 정규화된 784개 값으로 바꾼다. 빈 캔버스면 null이다. */
export function preprocess(pixels, width, height) {
  const box = boundingBox(pixels, width, height);
  if (box === null) return null;

  const digit = crop(pixels, width, box);

  // 긴 변이 20이 되도록 비율을 유지하며 줄인다
  const scale = Math.min(DIGIT_BOX / digit.width, DIGIT_BOX / digit.height);
  const targetWidth = Math.max(1, Math.round(digit.width * scale));
  const targetHeight = Math.max(1, Math.round(digit.height * scale));

  const resized = resize(digit.data, digit.width, digit.height, targetWidth, targetHeight);
  const centered = centerOn28(resized, targetWidth, targetHeight);

  const normalized = new Float32Array(CANVAS_28 * CANVAS_28);
  for (let i = 0; i < normalized.length; i++) {
    normalized[i] = (centered[i] / 255 - MNIST_MEAN) / MNIST_STD;
  }

  return normalized;
}
```

- [ ] **Step 4: 테스트가 통과하는 것을 확인한다**

Run: `cd /c/study01_mnist/web_version && node --test tests/`
Expected: PASS 16개 (Task 3의 7개와 이번 9개)

- [ ] **Step 5: 커밋한다**

```bash
cd /c/study01_mnist
git add web_version/src/preprocess.js web_version/tests/preprocess.test.js
git commit -m "캔버스 전처리 추가

경계 상자로 자르고 20x20에 맞춰 줄인 뒤 28x28 가운데에 놓는다.
브라우저마다 결과가 다른 drawImage 대신 박스 필터를 직접 구현했다.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 5: 브라우저 화면을 만든다

**Files:**
- Create: `web_version/index.html`
- Create: `web_version/style.css`
- Create: `web_version/src/app.js`
- Create: `web_version/CLAUDE.md`

**Interfaces:**
- Consumes: `MnistCNN`, `softmax` (Task 3), `preprocess` (Task 4), `weights.json` (Task 2)
- Produces: 없음. 최종 화면이다.

- [ ] **Step 1: index.html을 만든다**

```html
<!-- 생성 일시 주석은 파일을 만들 때 실제 시각으로 적는다 -->
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>손글씨 숫자 인식기</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <main>
    <h1>손글씨 숫자 인식기</h1>
    <canvas id="canvas" width="280" height="280"></canvas>
    <p id="result">가중치를 불러오는 중입니다.</p>
    <div class="buttons">
      <button id="predict" type="button" disabled>인식</button>
      <button id="clear" type="button">지우기</button>
    </div>
  </main>
  <script type="module" src="src/app.js"></script>
</body>
</html>
```

- [ ] **Step 2: style.css를 만든다**

데스크톱 버전처럼 검은 캔버스에 흰 획으로 그린다.

```css
/* 생성 일시 주석은 파일을 만들 때 실제 시각으로 적는다 */
body {
  margin: 0;
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #f4f4f6;
  font-family: "맑은 고딕", "Malgun Gothic", sans-serif;
}

main {
  text-align: center;
}

h1 {
  font-size: 1.25rem;
  font-weight: 600;
}

canvas {
  background: #000;
  border-radius: 8px;
  cursor: crosshair;
  touch-action: none;   /* 손가락으로 그릴 때 화면이 스크롤되지 않게 한다 */
  max-width: 90vw;
}

#result {
  font-size: 1.125rem;
  min-height: 1.5em;
}

.buttons {
  display: flex;
  gap: 12px;
  justify-content: center;
}

button {
  padding: 8px 24px;
  font-size: 1rem;
  font-family: inherit;
  border: 1px solid #c8c8cc;
  border-radius: 6px;
  background: #fff;
  cursor: pointer;
}

button:disabled {
  color: #9a9aa0;
  cursor: default;
}
```

- [ ] **Step 3: app.js를 쓴다**

```js
// 생성 일시 주석은 파일을 만들 때 실제 시각으로 적는다
// 캔버스 입력을 받아 추론 결과를 화면에 보여 준다. 계산은 model.js와 preprocess.js가 맡는다.

import { MnistCNN, softmax } from './model.js';
import { preprocess } from './preprocess.js';

const BRUSH_RADIUS = 10;
const DEFAULT_MESSAGE = '숫자를 그리고 [인식] 버튼을 누르세요.';
const LOADING_MESSAGE = '가중치를 불러오는 중입니다.';

const canvas = document.getElementById('canvas');
const context = canvas.getContext('2d', { willReadFrequently: true });
const resultLabel = document.getElementById('result');
const predictButton = document.getElementById('predict');
const clearButton = document.getElementById('clear');

let model = null;
let drawing = false;

function clearCanvas() {
  context.fillStyle = '#000';
  context.fillRect(0, 0, canvas.width, canvas.height);
  resultLabel.textContent = model === null ? LOADING_MESSAGE : DEFAULT_MESSAGE;
}

/** 포인터 위치를 캔버스 좌표로 바꾼다. 화면에서 캔버스가 축소돼 있어도 맞게 계산한다. */
function toCanvasPoint(event) {
  const rect = canvas.getBoundingClientRect();
  return {
    x: (event.clientX - rect.left) * (canvas.width / rect.width),
    y: (event.clientY - rect.top) * (canvas.height / rect.height),
  };
}

function drawDot(event) {
  const { x, y } = toCanvasPoint(event);
  context.fillStyle = '#fff';
  context.beginPath();
  context.arc(x, y, BRUSH_RADIUS, 0, Math.PI * 2);
  context.fill();
}

/** 캔버스에서 밝기값만 뽑는다. 흰 획이므로 빨강 채널 하나로 충분하다. */
function readPixels() {
  const image = context.getImageData(0, 0, canvas.width, canvas.height).data;
  const pixels = new Float32Array(canvas.width * canvas.height);
  for (let i = 0; i < pixels.length; i++) {
    pixels[i] = image[i * 4];
  }
  return pixels;
}

function predict() {
  const input = preprocess(readPixels(), canvas.width, canvas.height);
  if (input === null) {
    resultLabel.textContent = '먼저 숫자를 그려 주세요.';
    return;
  }

  const probabilities = softmax(model.forward(input));
  let best = 0;
  for (let digit = 1; digit < 10; digit++) {
    if (probabilities[digit] > probabilities[best]) best = digit;
  }

  const percent = (probabilities[best] * 100).toFixed(1);
  resultLabel.textContent = `예측 결과: ${best}  (확신도 ${percent}%)`;
}

async function loadModel() {
  try {
    const response = await fetch('weights.json');
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    model = new MnistCNN(await response.json());
    predictButton.disabled = false;
    resultLabel.textContent = DEFAULT_MESSAGE;
  } catch (error) {
    resultLabel.textContent = `가중치를 불러오지 못했습니다. (${error.message})`;
  }
}

canvas.addEventListener('pointerdown', (event) => {
  drawing = true;
  canvas.setPointerCapture(event.pointerId);
  drawDot(event);
});
canvas.addEventListener('pointermove', (event) => {
  if (drawing) drawDot(event);
});
canvas.addEventListener('pointerup', () => { drawing = false; });
canvas.addEventListener('pointercancel', () => { drawing = false; });

predictButton.addEventListener('click', predict);
clearButton.addEventListener('click', clearCanvas);

clearCanvas();
loadModel();
```

- [ ] **Step 4: 로컬에서 확인한다**

`file://`로 열면 ES 모듈과 `fetch`가 막히므로 정적 서버로 연다. 외부 패키지를 받지 않고 Node 내장 모듈만 쓴다.

Run:
```bash
cd /c/study01_mnist/web_version && node -e "const http=require('http'),fs=require('fs'),path=require('path');const types={'.html':'text/html','.js':'text/javascript','.css':'text/css','.json':'application/json'};http.createServer((q,s)=>{const f=path.join(process.cwd(),q.url==='/'?'index.html':q.url.split('?')[0]);fs.readFile(f,(e,d)=>{if(e){s.writeHead(404);s.end('없음');return;}s.writeHead(200,{'Content-Type':types[path.extname(f)]||'application/octet-stream'});s.end(d);});}).listen(8080,()=>console.log('http://localhost:8080'));"
```

브라우저로 `http://localhost:8080`을 열고 다음을 확인한다.
1. 처음에는 "가중치를 불러오는 중입니다."가 보이고 [인식] 버튼이 비활성이다.
2. 잠시 뒤 "숫자를 그리고 [인식] 버튼을 누르세요."로 바뀌고 버튼이 활성화된다.
3. 숫자 몇 개를 그려 [인식]을 누르면 맞는 숫자와 확신도가 나온다.
4. [지우기]를 누르면 캔버스가 비고 안내 문구로 돌아온다.
5. 아무것도 그리지 않고 [인식]을 누르면 "먼저 숫자를 그려 주세요."가 나온다.

확인이 끝나면 서버를 멈춘다.

- [ ] **Step 5: web_version/CLAUDE.md를 만든다**

파일 첫머리에 생성 일시를 넣고 다음을 담는다.

- 명령어: `node --test tests/`로 전체 테스트, Step 4의 정적 서버 실행법
- 외부 라이브러리 금지 규칙. 런타임과 테스트 모두 표준 API만 쓴다.
- 가중치는 직접 만들지 않는다. `desktop_version/export_weights.py`가 만든다. 모델 구조가 바뀌면 그 스크립트를 다시 돌리고 골든 테스트로 확인한다.
- `model.js`는 DOM을 모르고 `preprocess.js`는 모델을 모른다. 이 경계를 지켜야 Node에서 테스트할 수 있다.
- 골든 테스트의 의미와 허용 오차 1e-4
- 축소는 `drawImage` 대신 박스 필터를 직접 쓴다는 점과 그 이유
- `weights.json`, `golden.json`은 생성물이지만 Pages 배포에 필요하므로 커밋한다는 점

- [ ] **Step 6: 커밋한다**

```bash
cd /c/study01_mnist
git add web_version/index.html web_version/style.css web_version/src/app.js web_version/CLAUDE.md
git commit -m "웹 버전 화면 추가

캔버스 입력과 결과 표시를 붙였다. 포인터 이벤트를 써서 마우스와
터치를 함께 받는다.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 6: GitHub Pages에 배포하고 최상위 문서를 정리한다

**Files:**
- Create: `.github/workflows/pages.yml`
- Modify: `CLAUDE.md`, `README.md`

**Interfaces:**
- Consumes: `web_version/` 전체 (Task 3~5)
- Produces: 공개 URL

- [ ] **Step 1: 워크플로를 만든다**

브랜치 배포는 저장소 루트나 `/docs`만 서빙하므로 `web_version/`을 올리려면 Actions를 쓴다.

Create `.github/workflows/pages.yml`:

```yaml
# 생성 일시 주석은 파일을 만들 때 실제 시각으로 적는다
name: web_version을 GitHub Pages에 배포

on:
  push:
    branches: [main]
    paths:
      - 'web_version/**'
      - '.github/workflows/pages.yml'
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: false

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/configure-pages@v5
      - uses: actions/upload-pages-artifact@v3
        with:
          path: web_version
      - id: deployment
        uses: actions/deploy-pages@v4
```

- [ ] **Step 2: 저장소에서 Pages를 켠다**

Run:
```bash
gh api -X POST repos/vhsy1901750-ai/Study01_MNIST/pages -f build_type=workflow
```
Expected: 201 응답. 이미 켜져 있어 409가 나오면 방식만 바꾼다.
```bash
gh api -X PUT repos/vhsy1901750-ai/Study01_MNIST/pages -f build_type=workflow
```

- [ ] **Step 3: 최상위 CLAUDE.md를 공통 규칙만 남기도록 고친다**

데스크톱 세부는 Task 1에서, 웹 세부는 Task 5에서 각 폴더로 갔다. 최상위에는 다음만 남긴다.

- 저장소가 두 버전으로 나뉜다는 구조 설명과 각 폴더 CLAUDE.md로 가는 안내
- 두 버전 공통 규칙: 한글 작성, 정규화 상수 값, 새 파일 생성 일시
- 가중치 흐름: `desktop_version`이 학습하고 `export_weights.py`로 `web_version`에 공급한다. 방향은 한쪽이며 웹은 파이썬 파일을 직접 읽지 않는다.
- 모델 구조를 바꾸면 재학습, 재내보내기, 골든 테스트를 모두 다시 해야 한다는 점
- 배포: `web_version/`이 바뀌면 Actions가 Pages에 올린다

- [ ] **Step 4: README.md를 저장소 전체 소개로 고친다**

두 버전을 표로 소개하고, 웹 데모 링크와 각 버전 실행법을 적는다. 상세는 각 폴더의 CLAUDE.md로 안내한다.

- [ ] **Step 5: 전체 테스트를 다시 돌린다**

배포 전 마지막 확인이다.

Run:
```bash
cd /c/study01_mnist/desktop_version && python -m pytest -q
cd /c/study01_mnist/web_version && node --test tests/
```
Expected: 양쪽 모두 실패 0개

- [ ] **Step 6: 커밋하고 푸시한다**

```bash
cd /c/study01_mnist
git add -A
git commit -m "GitHub Pages 배포 워크플로와 최상위 문서 정리

web_version은 브랜치 배포로 서빙할 수 없어 Actions로 올린다.
최상위 CLAUDE.md는 공통 규칙만 남기고 상세는 각 폴더로 옮겼다.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
git push origin main
```

- [ ] **Step 7: 배포 결과를 확인한다**

로컬 통과는 배포 성공의 증거가 아니다. 실제로 올라간 페이지를 연다.

Run:
```bash
gh run list --workflow=pages.yml --limit 1
gh api repos/vhsy1901750-ai/Study01_MNIST/pages --jq .html_url
```
Expected: 워크플로가 `completed success`이고 URL이 나온다.

브라우저로 그 URL을 열어 Task 5 Step 4의 다섯 가지를 그대로 확인한다. 특히 `weights.json`이 정상적으로 내려받아지는지 개발자 도구 네트워크 탭에서 200 응답을 확인한다. 로컬에서는 보이지 않던 경로 문제나 MIME 문제가 여기서 드러난다.

---

## 완료 기준

1. `desktop_version`에서 `python -m pytest`가 통과한다.
2. `web_version`에서 `node --test tests/`가 통과하며, 골든 테스트의 로짓 오차가 1e-4 미만이다.
3. 배포된 Pages URL에서 숫자를 그려 인식이 된다.
4. 최상위와 두 폴더에 각각 CLAUDE.md가 있고 내용이 겹치지 않는다.
