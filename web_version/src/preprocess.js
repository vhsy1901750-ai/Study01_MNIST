// 2026-09-25 00:50 KST
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
