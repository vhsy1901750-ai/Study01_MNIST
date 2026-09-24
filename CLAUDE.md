# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 저장소 구조

같은 CNN으로 손글씨 숫자를 인식하는 두 버전이 들어 있다. 각 폴더의 `CLAUDE.md`에 그 버전의 명령어, 검증 방법, 건드리면 안 되는 것이 있으니 해당 폴더에서 일할 때는 그 문서를 본다.

| 폴더 | 무엇인가 | 상세 |
| --- | --- | --- |
| `desktop_version/` | PyTorch로 학습하고 Tkinter로 실행하는 Windows 앱 | `desktop_version/CLAUDE.md` |
| `web_version/` | 외부 라이브러리 없이 브라우저에서 추론하는 정적 페이지 | `web_version/CLAUDE.md` |

`docs/superpowers/plans/`에는 이 구조를 만든 구현 계획이 있다.

## 두 버전의 관계

의존 방향은 한쪽이다.

```
desktop_version/train.py          학습 -> mnist_cnn.pt
desktop_version/export_weights.py 변환 -> web_version/weights.json, golden.json
web_version/                      읽기만 한다
```

웹은 파이썬 파일을 직접 읽지 않는다. 순수 자바스크립트로는 PyTorch의 저장 형식을 풀 수 없으므로, 변환 스크립트가 만든 JSON만 받는다.

**모델 구조나 가중치를 바꾸면 세 가지를 모두 다시 해야 한다.** 재학습(`train.py`), 재내보내기(`export_weights.py`), 웹 골든 테스트(`web_version`에서 `node --test`). 하나라도 빠지면 두 버전의 예측이 말없이 갈라진다.

## 공통 규칙

- 모든 코드, 주석, UI 문자열, 문서는 한글로 쓴다.
- 정규화 상수는 `MNIST_MEAN = 0.1307`, `MNIST_STD = 0.3081`이다. 각 버전 안에서 한 곳에만 정의하고 나머지는 import한다.
- 새로 만드는 파일은 첫머리에 생성 일시를 `2026-09-25 00:50 KST` 형식의 주석으로 남긴다. 시각은 추측하지 않고 조회한다.
- 열거에는 가운뎃점을 쓰지 않고 쉼표를 쓴다. 완결된 문장인 메시지는 마침표로 끝낸다. 보조용언은 띄어 쓴다.

## 배포

`web_version/`이 바뀐 채로 `main`에 푸시되면 `.github/workflows/pages.yml`이 그 폴더를 GitHub Pages에 올린다. 브랜치 배포는 저장소 루트나 `/docs`만 서빙할 수 있어 Actions를 쓴다.

로컬 테스트 통과는 배포 성공의 증거가 아니다. 워크플로가 끝난 뒤 실제 주소를 열어 숫자가 인식되는지 확인한다.
