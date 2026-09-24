<!-- 2026-09-25 00:50 KST -->
# CLAUDE.md (web_version)

브라우저에서 순수 자바스크립트로 추론하는 손글씨 숫자 인식기다. GitHub Pages에 정적으로 배포된다. 저장소 전체에 걸친 규칙은 최상위 `CLAUDE.md`에 있다.

## 명령어

```bash
node --test          # 전체 테스트. tests/ 를 인자로 주면 Windows에서 디렉터리를 모듈로 읽어 실패한다.
```

로컬 확인은 정적 서버로 연다. `file://`로 열면 ES 모듈과 `fetch`가 막힌다. 외부 패키지를 받지 않고 Node 내장 모듈만 쓴다.

```bash
node -e "const http=require('http'),fs=require('fs'),path=require('path');const types={'.html':'text/html','.js':'text/javascript','.css':'text/css','.json':'application/json'};http.createServer((q,s)=>{const f=path.join(process.cwd(),q.url==='/'?'index.html':q.url.split('?')[0]);fs.readFile(f,(e,d)=>{if(e){s.writeHead(404);s.end('없음');return;}s.writeHead(200,{'Content-Type':types[path.extname(f)]||'application/octet-stream'});s.end(d);});}).listen(8080,()=>console.log('http://localhost:8080'));"
```

## 외부 라이브러리를 쓰지 않는다

런타임과 테스트 모두 표준 API만 쓴다. 테스트는 Node 내장 러너를 쓰고, `package.json`에는 `type: module` 선언만 있으며 의존성이 없다. 이 조건이 깨지면 GitHub Pages에 그대로 올릴 수 없다.

## 파일의 경계

- `src/model.js`는 숫자 계산만 한다. DOM을 모른다.
- `src/preprocess.js`는 픽셀 배열만 다룬다. 모델을 모른다.
- `src/app.js`만 브라우저 API를 안다.

이 경계 덕분에 앞의 두 파일을 Node에서 테스트할 수 있다. `model.js`나 `preprocess.js`에 `document`나 `canvas`를 들이지 않는다.

## 가중치는 직접 만들지 않는다

`weights.json`과 `golden.json`은 `desktop_version/export_weights.py`가 만든다. 이 폴더에서 손으로 고치지 않는다. 모델 구조나 가중치가 바뀌면 그 스크립트를 다시 돌리고 아래 골든 테스트로 확인한다.

두 파일은 생성물이지만 Pages가 서빙해야 하므로 `.gitignore`에 넣지 않고 커밋한다.

## 골든 테스트의 의미와 한계

`tests/model.test.js`의 골든 테스트는 PyTorch가 같은 입력에 대해 낸 로짓과 비교해 최대 절대 오차가 `1e-4` 미만인지 본다. 화면에 그럴듯한 숫자가 떠도 계산이 틀릴 수 있으므로, 이것이 추론 엔진이 맞다는 유일한 근거다.

비교는 28x28 입력부터 시작한다. 캔버스 축소는 PIL의 LANCZOS와 브라우저 구현이 달라 픽셀 단위로 일치시킬 수 없기 때문이다. 축소 단계는 `tests/preprocess.test.js`가 따로 덮는다.

예측 숫자를 비교하는 테스트는 정답 라벨이 아니라 PyTorch의 예측과 맞춘다. 라벨과 비교하면 모델 정확도가 99%인 탓에 구현이 멀쩡해도 간헐적으로 실패한다.

## 축소는 drawImage를 쓰지 않는다

`preprocess.js`의 `resize()`는 박스 필터 평균을 직접 계산한다. `drawImage`의 축소 결과는 브라우저마다 달라 같은 그림에 다른 예측이 나올 수 있고, Node에서 테스트할 수도 없다.

## 획은 선으로 잇는다

포인터 이벤트는 띄엄띄엄 들어온다. 점만 찍으면 빠르게 그을 때 획이 끊겨 인식이 무너진다. `app.js`의 `drawStroke()`가 직전 위치와 현재 위치를 선으로 잇는 이유다. 새 획을 시작할 때 `lastPoint`를 비우는 것도 이전 획과 이어지지 않게 하려는 것이다.
