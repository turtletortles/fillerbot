import cv2
import numpy as np

class GridDetection:
    hex_colors = {
        0: "#e55767",
        1: "#add367",
        2: "#fae251",
        3: "#61acee",
        4: "#6b539f",
        5: "#414141"
    }

    def __init__(self):
        self.grid = None  # Initialize as None

    def hex_to_nparr(self, x):
        color = self.hex_colors.get(x)
        return np.array([int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)])

    def process(self, file_path: str):
        img = cv2.imread(file_path)
        if img is None:
            raise ValueError(f"Failed to read image: {file_path}")

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blur, 6, 15)
        kernel = np.ones((3, 3), np.uint8)
        edges = cv2.dilate(edges, kernel, iterations=2)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            raise ValueError("No contours in image...")

        contour = [max(contours, key=lambda x: cv2.contourArea(x))]
        x, y, w, h = cv2.boundingRect(contour[0])
        cropped = img[y:y+h, x:x+w]

        n, m, _ = cropped.shape
        cropped = cropped[: (n // 7) * 7, : (m // 8) * 8, :]
        n, m, _ = cropped.shape
        grid = np.empty((7, 8), dtype=int)

        for i in range(7):
            for j in range(8):
                cell = cropped[i * n // 7 : (i + 1) * n // 7, j * m // 8 : (j + 1) * m // 8]
                avg_color = np.average(cell, axis=(0, 1))[::-1]  # Convert BGR to RGB
                grid[i][j] = min(range(6), key=lambda x: np.linalg.norm(avg_color - self.hex_to_nparr(x)))

        self.grid = grid

    def get_board(self):
        if self.grid is not None:
            return self.grid.tolist()
        return None
