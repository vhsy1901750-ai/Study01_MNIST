// 2026-09-25 00:50 KST
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
