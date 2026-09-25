# 2026-09-26 02:10 KST
"""MNIST에 없는 글씨체를 그려서 학습 데이터로 만든다.

MNIST의 6은 모두 위쪽이 둥글게 흘러내린다. 위가 평평한 6(가로줄로 시작해
왼쪽으로 내려온 뒤 아래에 고리를 그리는 형태)은 한 장도 없어서, 그렇게 쓴
6을 모델이 5로 읽는다. 5도 함께 만들어 넣지 않으면 이번에는 5를 6으로
잘못 읽게 되므로 두 글자를 같이 생성한다.
"""

import random

from PIL import Image, ImageDraw

from app import preprocess

CANVAS = 280
BRUSH = 20  # 웹, 데스크톱 앱과 같은 획 굵기


def _stroke(draw, points, width):
    """점들을 둥근 이음매로 이어 손으로 그은 획처럼 만든다."""
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        draw.line((x0, y0, x1, y1), fill=255, width=width)
    for x, y in points:
        r = width / 2
        draw.ellipse((x - r, y - r, x + r, y + r), fill=255)


def _jitter(points, amount, rng):
    return [(x + rng.uniform(-amount, amount), y + rng.uniform(-amount, amount)) for x, y in points]


def flat_six(rng):
    """위가 평평한 6. 가로줄로 시작해 왼쪽을 타고 내려와 아래에 고리를 그린다."""
    top_y = rng.uniform(50, 75)
    right_x = rng.uniform(165, 200)
    left_x = rng.uniform(78, 100)
    loop_top = rng.uniform(125, 150)
    bottom_y = rng.uniform(205, 235)
    loop_right = rng.uniform(160, 195)

    return [[
        (right_x, top_y),                                   # 가로줄 오른쪽 끝
        ((right_x + left_x) / 2, top_y + rng.uniform(-6, 6)),
        (left_x, top_y + rng.uniform(0, 12)),               # 가로줄 왼쪽 끝
        (left_x - rng.uniform(0, 8), loop_top),             # 왼쪽 세로 내림
        (left_x, bottom_y - rng.uniform(15, 30)),
        (left_x + rng.uniform(15, 30), bottom_y),           # 아래 고리 시작
        ((left_x + loop_right) / 2, bottom_y),
        (loop_right, bottom_y - rng.uniform(15, 30)),
        (loop_right - rng.uniform(5, 15), loop_top + rng.uniform(5, 20)),
        ((left_x + loop_right) / 2, loop_top),              # 고리를 닫는다
        (left_x + rng.uniform(0, 12), loop_top + rng.uniform(10, 25)),
    ]]


def flat_five(rng):
    """같은 손으로 쓴 5. 6과 구별을 유지하려면 함께 학습해야 한다."""
    top_y = rng.uniform(50, 70)
    right_x = rng.uniform(170, 200)
    left_x = rng.uniform(85, 105)
    mid_y = rng.uniform(120, 145)
    bottom_y = rng.uniform(200, 230)
    bowl_right = rng.uniform(170, 200)

    return [[
        (right_x, top_y),
        ((right_x + left_x) / 2, top_y + rng.uniform(-5, 5)),
        (left_x, top_y + rng.uniform(0, 8)),
        (left_x - rng.uniform(0, 6), mid_y),                # 세로 내림은 중간에서 끝난다
        (left_x + rng.uniform(25, 50), mid_y - rng.uniform(0, 10)),
        (bowl_right, mid_y + rng.uniform(15, 30)),          # 오른쪽으로 부푼 아래 배
        (bowl_right - rng.uniform(5, 15), bottom_y - rng.uniform(10, 25)),
        ((left_x + bowl_right) / 2, bottom_y),
        (left_x + rng.uniform(0, 15), bottom_y - rng.uniform(0, 15)),
    ]]


def render(strokes, rng):
    """획을 캔버스에 그린 뒤 앱과 같은 전처리를 거쳐 28x28 텐서로 만든다."""
    image = Image.new("L", (CANVAS, CANVAS), color=0)
    draw = ImageDraw.Draw(image)

    # 기울기와 크기를 조금씩 바꿔 같은 그림이 반복되지 않게 한다
    scale = rng.uniform(0.75, 1.1)
    shift_x = rng.uniform(-25, 25)
    shift_y = rng.uniform(-25, 25)

    for points in strokes:
        moved = [((x - 140) * scale + 140 + shift_x, (y - 140) * scale + 140 + shift_y)
                 for x, y in _jitter(points, 6, rng)]
        _stroke(draw, moved, int(BRUSH * scale))

    image = image.rotate(rng.uniform(-12, 12), resample=Image.BILINEAR, fillcolor=0)
    return preprocess(image)


def main():
    """샘플을 그려 눈으로 확인할 수 있게 한 장의 그림으로 저장한다."""
    rng = random.Random(20260926)
    sheet = Image.new("L", (28 * 10, 28 * 4), color=0)

    for row, maker in enumerate([flat_six, flat_five]):
        for col in range(10):
            tensor = render(maker(rng), rng)
            pixels = [max(0, min(255, int((v * 0.3081 + 0.1307) * 255))) for v in tensor.flatten().tolist()]
            tile = Image.new("L", (28, 28))
            tile.putdata(pixels)
            sheet.paste(tile, (col * 28, row * 28))

    sheet.resize((28 * 10 * 3, 28 * 4 * 3), Image.NEAREST).save("flat_sample.png")
    print("flat_sample.png 저장 완료 (위 줄: 평평한 6, 아래 줄: 같은 손의 5)")


if __name__ == "__main__":
    main()
