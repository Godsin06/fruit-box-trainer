import pyautogui
import time

NUM_ROWS = 10
NUM_COLS = 17
SCALE = 1
SIZE = 66 * SCALE

#
# 1) 숫자 인식
#
def detect_numbers(region):
    """
    화면에서 1~9 이미지를 찾아 10×17 grid[][] 채우고,
    디버그 출력
    """
    grid = [[0]*NUM_COLS for _ in range(NUM_ROWS)]
    total_sum = 0

    for digit in range(1, 10):
        for loc in pyautogui.locateAllOnScreen(
            f'images/apple{digit}.png', region=region, confidence=0.99
        ):
            r = (loc.top  - region[1]) // SIZE
            c = (loc.left - region[0]) // SIZE
            if 0 <= r < NUM_ROWS and 0 <= c < NUM_COLS:
                if grid[r][c] == 0:
                    grid[r][c] = digit
                    total_sum += digit

    print("\n[DEBUG] 인식된 GRID:")
    for row in grid:
        print(" ".join(str(x) for x in row))
    print(f"[DEBUG] 인식된 사과 합: {total_sum}\n")
    return grid, total_sum

#
# 2) 재귀 로직에 필요한 클래스들
#
class BoxPy:
    def __init__(self, x, y, w, h):
        # x = 열 시작, y = 행 시작
        self.x = x
        self.y = y
        self.w = w
        self.h = h

class StrategyPy:
    def __init__(self):
        self.boxes = []  # BoxPy들을 순서대로
        self.score = 0   # 지울 칸(>0) 총합

def hash_grid(grid):
    """Rust 처럼 grid 해싱"""
    h = 0
    for row in grid:
        for val in row:
            h = h*11 + val
            h &= 0xFFFFFFFFFFFFFFFF
    return h

#
# 2D Prefix Sum 구하는 함수
#
def build_prefix_sum(grid):
    """prefix[r][c] = (0,0) ~ (r-1,c-1)까지의 합"""
    prefix = [[0]*(NUM_COLS+1) for _ in range(NUM_ROWS+1)]
    for r in range(NUM_ROWS):
        for c in range(NUM_COLS):
            prefix[r+1][c+1] = prefix[r+1][c] + prefix[r][c+1] - prefix[r][c] + grid[r][c]
    return prefix

def rect_sum(prefix, x, y, w, h):
    """
    prefix 이용하여 (y,x)부터 (y+h-1, x+w-1)까지의 합 구하기
    """
    # 아래 식에 주의: prefix는 r+1, c+1 인덱스로 누적
    r1, c1 = y, x
    r2, c2 = y+h, x+w
    return prefix[r2][c2] - prefix[r2][c1] - prefix[r1][c2] + prefix[r1][c1]

def find_strategy_recursive(grid):
    """실제 재귀 함수 => best_strategy 구함"""
    visited = set()
    best = StrategyPy()

    max_moves = (NUM_ROWS*NUM_COLS)//2 + 1
    # '해당 깊이에서의 최대 점수' 기록 (초기엔 -inf)
    best_intermediate_scores = [float('-inf')] * max_moves

    def recurse(g, current, num_moves):
        nonlocal best

        # 1) 현재 점수가 최고점이면 갱신
        if current.score > best.score:
            best.boxes = current.boxes[:]
            best.score = current.score

        # 2) 가지치기 로직 (점수 최대화)
        if current.score > best_intermediate_scores[num_moves]:
            best_intermediate_scores[num_moves] = current.score

        # 만약 현재점수가 '이 깊이에서의 최고점 - 5'보다 작으면 가지치기
        if current.score + 5 < best_intermediate_scores[num_moves]:
            return

        # 3) 방문 체크
        hval = hash_grid(g)
        if hval in visited:
            return
        visited.add(hval)

        if len(visited) > 100_000:
            return

        # 4) D=4 => 후보 4개
        D = 4
        candidates = []

        # ---- (중요) 2D Prefix Sum 사용 ----
        prefix = build_prefix_sum(g)

        # 전체 가능한 사각형 탐색
        for y in range(NUM_ROWS):
            for x in range(NUM_COLS):
                # h_, w_ 는 사각형 크기
                for h_ in range(1, NUM_ROWS - y + 1):
                    for w_ in range(1, NUM_COLS - x + 1):
                        sub_sum = rect_sum(prefix, x, y, w_, h_)
                        if sub_sum == 10:
                            # 내부 실제로 지워질 칸(>0) 개수
                            cnt = 0
                            for rr in range(y, y+h_):
                                for cc in range(x, x+w_):
                                    if g[rr][cc] > 0:
                                        cnt += 1
                            if cnt > 0:
                                candidates.append((cnt, x, y, w_, h_))
                        elif sub_sum > 10:
                            # 어차피 숫자(1~9)만 있으므로, 더 확장하면 sum이 줄어들 일 없음
                            # => 이 열(w_) 루프는 break 가능
                            break

        # count 큰 순 => 상위 4개
        candidates.sort(key=lambda x: x[0], reverse=True)
        moves = candidates[:D]

        for (cnt, sx, sy, w_, h_) in moves:
            newg = [row[:] for row in g]
            # 지우기 => 0
            for rr in range(sy, sy+h_):
                for cc in range(sx, sx+w_):
                    newg[rr][cc] = 0

            box_obj = BoxPy(sx, sy, w_, h_)
            current.boxes.append(box_obj)
            current.score += cnt

            recurse(newg, current, num_moves+1)

            current.boxes.pop()
            current.score -= cnt

    current = StrategyPy()
    recurse(grid, current, 0)
    return best

def find_strategy(grid):
    """외부에서 호출 => (x1,y1,x2,y2) 튜플 리스트 반환"""
    best = find_strategy_recursive(grid)
    moves = []
    for b in best.boxes:
        x1 = b.x
        y1 = b.y
        x2 = x1 + b.w - 1
        y2 = y1 + b.h - 1
        moves.append((x1, y1, x2, y2))
    return moves

#
# 3) 드래그시 디버그 => 실제 grid도 0으로 변경
#
def debug_subgrid(grid, x1, y1, x2, y2):
    print("사각형 내부 숫자:")
    for rr in range(y1, y2+1):
        rowvals = grid[rr][x1:x2+1]
        print(" ".join(str(v) for v in rowvals))

def remove_subgrid(grid, x1, y1, x2, y2):
    """실제 grid도 0으로"""
    for rr in range(y1, y2+1):
        for cc in range(x1, x2+1):
            grid[rr][cc] = 0

#
# 4) 메인 로직
#
def play_game():
    import math

    print("[INFO] 게임 화면 분석 중...")
    # 1) reset 버튼 찾아서 region
    left, top, w_, h_ = pyautogui.locateOnScreen('images/reset.png', confidence=0.99)
    left += 20*SCALE
    top  -= 730*SCALE
    region = (left, top, SIZE*NUM_COLS, SIZE*NUM_ROWS)

    # 2) reset / play
    pyautogui.leftClick(left/SCALE, top/SCALE)
    pyautogui.leftClick((left-3)/SCALE, (top+760)/SCALE)
    pyautogui.leftClick((left+300)/SCALE, (top+400)/SCALE)

    # 3) grid 인식
    grid, total_ = detect_numbers(region)

    # 4) 재귀 => 최적 사각형 목록(순서)
    moves = find_strategy(grid)
    print(f"[INFO] 최적 사각형 개수= {len(moves)}")

    # 5) 실제로 드래그 동작
    for i, (x1, y1, x2, y2) in enumerate(moves, start=1):
        print(f"\n[{i}/{len(moves)}] 사각형: (행 {y1}~{y2}, 열 {x1}~{x2})")
        debug_subgrid(grid, x1, y1, x2, y2)

        # 픽셀 좌표
        start_x = left + x1*SIZE
        start_y = top  + y1*SIZE
        end_x   = left + (x2+1)*SIZE
        end_y   = top  + (y2+1)*SIZE

        print(f"🖱 드래그 시작=({start_x},{start_y}), 끝=({end_x},{end_y})")

        pyautogui.moveTo(start_x/SCALE, start_y/SCALE)
        time.sleep(0.3)
        pyautogui.mouseDown()
        time.sleep(0.2)
        pyautogui.moveTo(end_x/SCALE, end_y/SCALE, duration=0.5)
        time.sleep(0.2)
        pyautogui.mouseUp()

        # grid에서도 제거
        remove_subgrid(grid, x1, y1, x2, y2)

if __name__ == "__main__":
    play_game()
