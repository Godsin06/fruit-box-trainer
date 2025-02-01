import pyautogui
import time

SCALE = 1
NUM_COLS = 17
NUM_ROWS = 10
SIZE = 33 * SCALE

def debug_region_print():
    left, top, w, h = pyautogui.locateOnScreen('images/reset.png', confidence=0.99)
    
    # 보정
    left  = int(left + 8 * SCALE)
    top   = int(top  - 363 * SCALE)
    width  = int(SIZE * NUM_COLS)
    height = int(SIZE * NUM_ROWS)

    region = (left, top, width, height)  # 모두 int여야 함

    # 모서리 좌표 계산
    left_edge   = left
    top_edge    = top
    right_edge  = left + width
    bottom_edge = top  + height

    print(f"[DEBUG] 게임 인식 영역(region): {region}")
    print(f"        Left   = {left_edge}")
    print(f"        Top    = {top_edge}")
    print(f"        Right  = {right_edge}")
    print(f"        Bottom = {bottom_edge}")

    # region 스크린샷
    screenshot = pyautogui.screenshot(region=region)
    screenshot.save("debug_region_screenshot.png")
    print("[DEBUG] debug_region_screenshot.png 파일로 저장 완료")

def main():
    debug_region_print()

if __name__ == "__main__":
    main()
