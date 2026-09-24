# 2026-09-20 19:12 KST
"""바로가기와 앱 창에 쓸 아이콘(app.ico)을 그려서 만든다."""

from PIL import Image, ImageDraw, ImageFont

SIZE = 256
ICON_PATH = "app.ico"


def main():
    image = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # 진한 남색 둥근 사각형 배경
    draw.rounded_rectangle((8, 8, SIZE - 8, SIZE - 8), radius=48, fill=(30, 41, 82, 255))

    # 가운데에 흰색 굵은 숫자 7
    font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 190)
    draw.text((SIZE / 2, SIZE / 2 - 8), "7", font=font, fill="white", anchor="mm")

    # 손글씨 느낌의 밑줄
    draw.line((60, 212, 196, 204), fill=(255, 196, 0, 255), width=12)

    image.save(ICON_PATH, sizes=[(256, 256), (48, 48), (32, 32), (16, 16)])
    print(f"{ICON_PATH} 생성 완료")


if __name__ == "__main__":
    main()
