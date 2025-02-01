import cv2
import numpy as np
import pyautogui
import time
from itertools import product

# 게임 설정 값
NUM_ROWS = 10
NUM_COLS = 17
SCALE = 1  # 이미지 크기 배율 (Retina 디스플레이 대응)
SIZE = 66 * SCALE  # 한 블록의 크기

def detect_numbers(region):
    """
    화면에서 숫자(사과)를 인식하여 10×17 grid에 저장
    인식 결과를 grid에 채운 후, grid 전체를 디버그 출력
    """
    grid = [[0 for _ in range(NUM_COLS)] for _ in range(NUM_ROWS)]
    total_sum = 0
    
    # (선택) 중복 체크용 리스트
    seen_positions = []

    for digit in range(1, 10):  # 숫자 1~9까지 탐색
        for loc in pyautogui.locateAllOnScreen(
            f'images/apple{digit}.png', region=region, confidence=0.99
        ):
            # (선택) 중복 필터: 중심점 기준으로 근접 좌표 중복 방지
            center_x = loc.left + loc.width // 2
            center_y = loc.top + loc.height // 2
            if any(abs(center_x - sx) < 5 and abs(center_y - sy) < 5 for sx, sy in seen_positions):
                continue
            seen_positions.append((center_x, center_y))

            # grid에 숫자 세팅
            row = (loc.top - region[1]) // SIZE
            col = (loc.left - region[0]) // SIZE

            # 이미 다른 숫자가 들어있지 않은 경우에만 값 세팅
            if grid[row][col] == 0:
                grid[row][col] = digit
                total_sum += digit

    # 디버깅용 출력
    print("\n[DEBUG] 현재 인식된 grid:")
    for r in range(NUM_ROWS):
        row_str = " ".join(str(grid[r][c]) for c in range(NUM_COLS))
        print(row_str)
    print(f"[DEBUG] 인식된 사과 합: {total_sum}\n")

    return grid, total_sum

def find_strategy(grid):
    """ 합이 10이 되는 블록 찾기 """
    best_score = 0
    best_moves = []
    
    for x1, y1, x2, y2 in product(range(NUM_COLS), range(NUM_ROWS), repeat=2):
        if x1 > x2 or y1 > y2:
            continue

        # 선택한 블록 내 숫자들의 합 계산
        subgrid = [grid[y][x1:x2+1] for y in range(y1, y2+1)]
        block_sum = sum(sum(row) for row in subgrid)

        if block_sum == 10:
            count = sum(1 for row in subgrid for num in row if num > 0)
            if count > best_score:
                best_score = count
                best_moves = [(x1, y1, x2, y2)]

    return best_moves

def play_game():
    """게임 자동 실행"""
    print("🔍 게임 화면 분석 중...")

    # (1) 게임 영역 찾기
    left, top, _, _ = pyautogui.locateOnScreen('images/reset.png', confidence=0.99)
    left += 8 * SCALE
    top -= 740 * SCALE
    region = (left, top, SIZE * NUM_COLS, SIZE * NUM_ROWS)

    # (2) 게임 시작
    pyautogui.leftClick(x=left, y=top)
    pyautogui.leftClick(x=left - 3, y=top + 760)  # "Reset"
    pyautogui.leftClick(x=left + 300, y=top + 400)      # "Play"

    # (3) 숫자 감지
    grid, total_sum = detect_numbers(region)

    # (4) 합이 10인 사각형 찾기
    moves = find_strategy(grid)
    print(f"🍎 인식된 총 합: {total_sum}, 찾은 사각형 개수: {len(moves)}")

    # (5) 드래그 동작
    for (x1, y1, x2, y2) in moves:
        start_x, start_y = left + x1 * SIZE, top + y1 * SIZE
        end_x, end_y = left + x2 * SIZE, top + y2 * SIZE

        print(f"🖱 드래그 시작: 행 {y1}, 열 {x1} → ({start_x}, {start_y})")
        print(f"🖱 드래그 끝  : 행 {y2}, 열 {x2} → ({end_x}, {end_y})")

        pyautogui.moveTo(start_x, start_y)
        time.sleep(0.5)
        pyautogui.mouseDown()
        time.sleep(0.2)
        pyautogui.moveTo(end_x, end_y, duration=0.5)
        time.sleep(0.2)
        pyautogui.mouseUp()

if __name__ == "__main__":
    play_game()
