import cv2
import numpy as np
import pyautogui
import easyocr
import keyboard
import time
import tkinter as tk
from tkinter import Label, Button, Toplevel
from PIL import Image, ImageTk
from pynput.mouse import Listener

# EasyOCR 로드
reader = easyocr.Reader(['en'])

# 저장할 영역 정보
selected_region = None

# Tkinter GUI 클래스
class NumberCounterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("숫자 개수 인식기 (최적화 버전)")
        self.root.geometry("500x450")

        # 레이블
        self.label_title = Label(root, text="숫자 개수 인식기", font=("Arial", 16, "bold"))
        self.label_title.pack(pady=10)

        self.label_info = Label(root, text="F9: 영역 선택 | F10: 숫자 인식", font=("Arial", 12))
        self.label_info.pack(pady=5)

        # 버튼
        self.btn_select_area = Button(root, text="영역 선택 (F9)", command=self.select_screen_area, font=("Arial", 12))
        self.btn_select_area.pack(pady=10)

        self.btn_recognize = Button(root, text="숫자 인식 (F10)", command=self.capture_and_analyze, font=("Arial", 12))
        self.btn_recognize.pack(pady=10)

        self.label_result = Label(root, text="", font=("Arial", 14, "bold"), fg="blue")
        self.label_result.pack(pady=10)

        # 단축키 설정
        keyboard.add_hotkey("F9", self.select_screen_area)
        keyboard.add_hotkey("F10", self.capture_and_analyze)

        self.preview_window = None  # 미리보기 창

    # 마우스로 드래그하여 영역 선택
    def select_screen_area(self):
        global selected_region
        self.label_info.config(text="F9를 누른 후, 화면에서 마우스로 드래그하세요...")

        time.sleep(1)  # 사용자 준비 시간
        x1, y1, x2, y2 = self.get_mouse_drag_region()

        if x1 is None:
            self.label_info.config(text="영역 선택이 취소되었습니다.")
            return

        selected_region = (x1, y1, x2 - x1, y2 - y1)
        self.label_info.config(text=f"선택된 영역: {selected_region}")
        self.show_preview()

    # 마우스로 드래그하여 좌표 획득
    def get_mouse_drag_region(self):
        print("화면에서 마우스로 드래그하여 영역을 선택하세요...")
        start = None
        end = None

        def on_click(x, y, button, pressed):
            nonlocal start, end
            if pressed:
                start = (x, y)
            else:
                end = (x, y)
                return False  # 리스너 종료

        with Listener(on_click=on_click) as listener:
            listener.join()

        if start and end:
            x1, y1 = start
            x2, y2 = end
            return (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
        return None, None, None, None

    # 미리보기 창 표시
    def show_preview(self):
        global selected_region
        if selected_region is None:
            return

        # 기존 미리보기 창 닫기
        if self.preview_window is not None:
            self.preview_window.destroy()

        # 새로운 미리보기 창 생성
        self.preview_window = Toplevel(self.root)
        self.preview_window.title("선택한 영역 미리보기")

        x, y, w, h = selected_region
        screenshot = pyautogui.screenshot(region=(x, y, w, h))
        screenshot = screenshot.resize((200, 150))  # 미리보기 크기 조정

        img = ImageTk.PhotoImage(screenshot)
        label = Label(self.preview_window, image=img)
        label.image = img
        label.pack()

    # OCR 중복 필터링 (좌표 기반)
    def filter_duplicates(self, ocr_results):
        filtered_results = []
        threshold_distance = 15  # 중복 감지를 위한 최소 거리

        for result in ocr_results:
            try:
                if len(result) != 3:  # OCR 데이터 구조 확인
                    continue

                text, bbox, _ = result
                if not bbox or len(bbox) < 2:  # bbox가 없는 경우 무시
                    continue

                x_min, y_min = bbox[0]  # 좌상단 좌표
                is_duplicate = False

                for _, prev_bbox in filtered_results:
                    prev_x, prev_y = prev_bbox[0]
                    if abs(x_min - prev_x) < threshold_distance and abs(y_min - prev_y) < threshold_distance:
                        is_duplicate = True
                        break

                if not is_duplicate:
                    filtered_results.append((text, bbox))

            except Exception as e:
                print(f"OCR 데이터 처리 중 오류 발생: {e}")
                continue

        return filtered_results

    # 숫자 개수 분석 (OCR + 중복 제거)
    def count_numbers(self, image):
        try:
            # OCR 실행
            ocr_results = reader.readtext(np.array(image))

            # 중복 제거 적용
            filtered_results = self.filter_duplicates(ocr_results)

            count_dict = {str(i): 0 for i in range(1, 10)}
            for text, _ in filtered_results:
                for char in text:
                    if char in count_dict:
                        count_dict[char] += 1

            return count_dict
        except Exception as e:
            print(f"OCR 분석 중 오류 발생: {e}")
            return {str(i): 0 for i in range(1, 10)}

    # 캡처 및 숫자 분석 실행
    def capture_and_analyze(self):
        global selected_region
        if selected_region is None:
            self.label_info.config(text="먼저 영역을 선택하세요! (F9)")
            return

        x, y, w, h = selected_region
        screenshot = pyautogui.screenshot(region=(x, y, w, h))
        image = np.array(screenshot)

        # 숫자 개수 분석
        count_result = self.count_numbers(screenshot)

        # 총합 계산
        total_sum = sum(int(num) * count for num, count in count_result.items())

        # 결과 표시
        result_text = "현재 화면의 숫자 개수:\n"
        result_text += "\n".join([f"{num}: {count}개" for num, count in count_result.items()])
        result_text += f"\n\n총합: {total_sum}"

        self.label_result.config(text=result_text)

# GUI 실행
if __name__ == "__main__":
    root = tk.Tk()
    app = NumberCounterApp(root)
    root.mainloop()
