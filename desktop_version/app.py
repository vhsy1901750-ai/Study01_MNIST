# 2026-09-20 19:22 KST
"""캔버스에 마우스로 숫자를 그리면 학습된 CNN이 인식하는 Tkinter GUI."""

import os
import tkinter as tk

import torch
import torch.nn.functional as F
from PIL import Image, ImageDraw

from model import MnistCNN
from train import MNIST_MEAN, MNIST_STD

# 바로가기나 더블클릭으로 실행돼 작업 폴더가 달라도 찾을 수 있도록 이 파일 기준 경로를 쓴다
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEIGHTS_PATH = os.path.join(BASE_DIR, "mnist_cnn.pt")
ICON_PATH = os.path.join(BASE_DIR, "app.ico")

CANVAS_SIZE = 280  # 28의 10배 크기로 그려서 그리기 편하게 한다
BRUSH_RADIUS = 10
DEFAULT_MESSAGE = "숫자를 그리고 [인식] 버튼을 누르세요."


def preprocess(image):
    """그린 이미지를 MNIST 형식의 텐서로 바꾼다. 아무것도 그리지 않았으면 None을 돌려준다.

    MNIST 원본은 숫자를 20x20 상자에 맞춘 뒤 28x28 가운데에 놓은 형태이므로 동일하게 만든다.
    """
    bbox = image.getbbox()
    if bbox is None:
        return None

    # 숫자가 그려진 영역만 잘라내고, 긴 변이 20픽셀이 되도록 비율을 유지하며 줄인다
    digit = image.crop(bbox)
    digit.thumbnail((20, 20), Image.LANCZOS)

    # 28x28 검은 배경 가운데에 배치한다
    canvas = Image.new("L", (28, 28), color=0)
    canvas.paste(digit, ((28 - digit.width) // 2, (28 - digit.height) // 2))

    # 학습 때와 같은 정규화를 적용한다
    tensor = torch.tensor(list(canvas.getdata()), dtype=torch.float32).view(1, 1, 28, 28) / 255.0
    return (tensor - MNIST_MEAN) / MNIST_STD


class DigitRecognizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("손글씨 숫자 인식기")
        self.root.iconbitmap(ICON_PATH)

        self.model = MnistCNN()
        self.model.load_state_dict(torch.load(WEIGHTS_PATH, map_location="cpu"))
        self.model.eval()

        # 화면 캔버스와 같은 내용을 담는 흑백 이미지를 예측용으로 따로 유지한다
        self.image = Image.new("L", (CANVAS_SIZE, CANVAS_SIZE), color=0)
        self.draw = ImageDraw.Draw(self.image)

        self.canvas = tk.Canvas(root, width=CANVAS_SIZE, height=CANVAS_SIZE, bg="black", cursor="cross")
        self.canvas.grid(row=0, column=0, columnspan=2, padx=10, pady=10)
        self.canvas.bind("<Button-1>", self.on_draw)
        self.canvas.bind("<B1-Motion>", self.on_draw)

        self.result_label = tk.Label(root, text=DEFAULT_MESSAGE, font=("맑은 고딕", 14))
        self.result_label.grid(row=1, column=0, columnspan=2, pady=(0, 10))

        tk.Button(root, text="인식", width=12, command=self.predict).grid(row=2, column=0, padx=10, pady=(0, 10))
        tk.Button(root, text="지우기", width=12, command=self.clear).grid(row=2, column=1, padx=10, pady=(0, 10))

    def on_draw(self, event):
        x, y, r = event.x, event.y, BRUSH_RADIUS
        # 화면 캔버스와 내부 이미지에 같은 흰색 원을 그린다
        self.canvas.create_oval(x - r, y - r, x + r, y + r, fill="white", outline="white")
        self.draw.ellipse((x - r, y - r, x + r, y + r), fill=255)

    def clear(self):
        self.canvas.delete("all")
        self.draw.rectangle((0, 0, CANVAS_SIZE, CANVAS_SIZE), fill=0)
        self.result_label.config(text=DEFAULT_MESSAGE)

    def predict(self):
        tensor = preprocess(self.image)
        if tensor is None:
            self.result_label.config(text="먼저 숫자를 그려 주세요.")
            return
        with torch.no_grad():
            probabilities = F.softmax(self.model(tensor), dim=1)
        confidence, digit = probabilities.max(dim=1)
        self.result_label.config(text=f"예측 결과: {digit.item()}  (확신도 {confidence.item() * 100:.1f}%)")


def main():
    root = tk.Tk()
    DigitRecognizerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
