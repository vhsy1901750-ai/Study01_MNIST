// 2026-09-25 00:50 KST
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
