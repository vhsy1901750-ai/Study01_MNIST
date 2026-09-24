// 2026-09-25 00:50 KST
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
let lastPoint = null;   // 직전 포인터 위치. 이벤트 사이를 선으로 이어 획이 끊기지 않게 한다.

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

/** 직전 위치에서 지금 위치까지 획을 잇는다. 포인터 이벤트는 띄엄띄엄 오므로 선으로 메운다. */
function drawStroke(event) {
  const point = toCanvasPoint(event);

  context.fillStyle = '#fff';
  context.beginPath();
  context.arc(point.x, point.y, BRUSH_RADIUS, 0, Math.PI * 2);
  context.fill();

  if (lastPoint !== null) {
    context.strokeStyle = '#fff';
    context.lineWidth = BRUSH_RADIUS * 2;
    context.lineCap = 'round';
    context.beginPath();
    context.moveTo(lastPoint.x, lastPoint.y);
    context.lineTo(point.x, point.y);
    context.stroke();
  }

  lastPoint = point;
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
  lastPoint = null;   // 새 획은 이전 획과 이어지면 안 된다
  canvas.setPointerCapture(event.pointerId);
  drawStroke(event);
});
canvas.addEventListener('pointermove', (event) => {
  if (drawing) drawStroke(event);
});
canvas.addEventListener('pointerup', () => { drawing = false; });
canvas.addEventListener('pointercancel', () => { drawing = false; });

predictButton.addEventListener('click', predict);
clearButton.addEventListener('click', clearCanvas);

clearCanvas();
loadModel();
