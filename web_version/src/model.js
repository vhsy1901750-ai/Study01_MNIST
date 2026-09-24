// 2026-09-25 00:50 KST
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
