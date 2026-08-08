import cv2
from PIL import Image
from PIL import ImageDraw
import numpy as np

WIDTH = 800
HEIGHT = 800

def run() :

    codec = cv2.VideoWriter_fourcc(*'mp4v') #type: ignore

    video = cv2.VideoWriter('video.mp4', codec, 24, (WIDTH, HEIGHT))

    for i in range(0, 240) :
        img = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        index = i // 24
        draw.text((200 + index * 2, 200 + index * 2), f"Hello World {index}", fill=(255, 255, 0))
        frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        video.write(frame)


if __name__ == '__main__' :
    run()