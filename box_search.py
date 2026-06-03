import sys
import os
from PyQt6.QtCore import Qt, QPoint, QRect, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen, QGuiApplication, QFont, QIcon, QPixmap
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QFrame, QTextEdit, QLineEdit, QSizePolicy

# =====================================================================
# DYNAMIC HUD MENU DOCK WIDGET (Tool Window with explicit parent integration)
# =====================================================================
class HUDMenu(QWidget):
    def __init__(self, text, on_copy, on_search_image, on_search_text, parent=None):
        super().__init__(parent)
        self.text = text
        self.on_copy = on_copy
        self.on_search_image = on_search_image
        self.on_search_text = on_search_text
        
        # Tool window flags with stays-on-top, frameless (perfect for overlays)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        
        # Start fully transparent for smooth fade-in
        self.setWindowOpacity(0.0)
        
        self.init_ui()
        
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Elegant glassmorphic background container
        self.frame = QFrame(self)
        self.frame.setObjectName("HUDFrame")
        self.frame.setStyleSheet("""
            QFrame#HUDFrame {
                background-color: rgba(12, 12, 20, 245);
                border: 2px solid rgba(0, 255, 136, 200);
                border-radius: 12px;
            }
        """)
        
        self.frame_layout = QHBoxLayout(self.frame)
        self.frame_layout.setContentsMargins(12, 6, 12, 6)
        self.frame_layout.setSpacing(8)
        
        # SnapRoute tag
        title_label = QLabel("SNAPROUTE", self.frame)
        title_label.setStyleSheet("color: rgba(0, 255, 136, 200); font-weight: bold; font-size: 10px; letter-spacing: 1px;")
        self.frame_layout.addWidget(title_label)
        
        # Vertical divider
        sep = QFrame(self.frame)
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet("background-color: rgba(255, 255, 255, 30); max-width: 1px; min-height: 15px;")
        self.frame_layout.addWidget(sep)
        
        # Action Buttons
        self.btn_copy = QPushButton("📋 Copy", self.frame)
        self.btn_search_image = QPushButton("🖼️ Search Image", self.frame)
        self.btn_search_text = QPushButton("📝 Search Text", self.frame)
        
        button_style = """
            QPushButton {
                background-color: rgba(255, 255, 255, 12);
                color: #ECEFF4;
                border: 1px solid rgba(255, 255, 255, 30);
                border-radius: 6px;
                padding: 5px 10px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(0, 255, 136, 40);
                border: 1px solid rgba(0, 255, 136, 220);
                color: #FFFFFF;
            }
            QPushButton:disabled {
                background-color: rgba(255, 255, 255, 4);
                color: rgba(255, 255, 255, 40);
                border: 1px solid rgba(255, 255, 255, 10);
            }
        """
        self.btn_copy.setStyleSheet(button_style)
        self.btn_search_image.setStyleSheet(button_style)
        self.btn_search_text.setStyleSheet(button_style)
        
        self.btn_copy.clicked.connect(self.on_copy)
        self.btn_search_image.clicked.connect(self.on_search_image)
        self.btn_search_text.clicked.connect(self.on_search_text)
        
        self.frame_layout.addWidget(self.btn_copy)
        self.frame_layout.addWidget(self.btn_search_image)
        self.frame_layout.addWidget(self.btn_search_text)
        
        # Initially, the Search Text button is disabled until OCR completes
        self.btn_search_text.setEnabled(False)
        self.btn_search_text.setToolTip("Running OCR in background...")
        
        layout.addWidget(self.frame)
        
    def show_animated(self):
        self.show()
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(180) # 180ms smooth fade-in
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.anim.start()
        
    def close_animated(self, callback=None):
        self.anim_out = QPropertyAnimation(self, b"windowOpacity")
        self.anim_out.setDuration(150) # 150ms smooth fade-out
        self.anim_out.setStartValue(self.windowOpacity())
        self.anim_out.setEndValue(0.0)
        self.anim_out.setEasingCurve(QEasingCurve.Type.InCubic)
        if callback:
            self.anim_out.finished.connect(callback)
        else:
            self.anim_out.finished.connect(self.close)
        self.anim_out.start()
        
    def update_text_detected(self, text):
        clean_text = "".join(c for c in text if c.isalnum())
        if len(clean_text) >= 2:
            self.btn_copy.setText("📋 Copy Text")
            self.btn_search_text.setEnabled(True)
            self.btn_search_text.setToolTip("Search extracted text on Google")
        else:
            self.btn_copy.setText("📋 Copy Image")
            self.btn_search_text.setEnabled(False)
            self.btn_search_text.setToolTip("No text detected to search")
            
    def resize_to_fit(self):
        # Elegant fixed HUD size to avoid any jitter/jumps or sliding buttons
        hud_width = 440
        hud_height = 50
        
        parent = self.parent()
        if parent and hasattr(parent, 'last_selection_rect'):
            rect = parent.last_selection_rect
            x = rect.x() + (rect.width() - hud_width) // 2
            y = rect.y() + rect.height() + 10
            
            screen_rect = parent.rect()
            if x < 10: x = 10
            if x + hud_width > screen_rect.width() - 10: x = screen_rect.width() - hud_width - 10
            
            if y + hud_height > screen_rect.height() - 10:
                y = rect.y() - hud_height - 10
                if y < 10:
                    y = rect.y() + (rect.height() - hud_height) // 2
            self.setGeometry(x, y, hud_width, hud_height)

# =====================================================================
# ASYNCHRONOUS BACKGROUND OCR WORKER (Prevents GUI lag / freezing)
# =====================================================================
class OCRWorker(QThread):
    finished_signal = pyqtSignal(str)
    
    def __init__(self, image_path):
        super().__init__()
        self.image_path = image_path
        
    def run(self):
        import pytesseract
        # Dynamic path resolution for standalone bundled EXE deployment
        tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            portable_path = os.path.join(sys._MEIPASS, 'tesseract', 'tesseract.exe')
            if os.path.exists(portable_path):
                tesseract_cmd = portable_path
                
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        try:
            # Blocking OCR call runs completely on a background thread!
            text = pytesseract.image_to_string(self.image_path).strip()
            self.finished_signal.emit(text)
        except Exception as e:
            print("[OCR Error]", e)
            self.finished_signal.emit("")

# =====================================================================
# ASYNCHRONOUS BACKGROUND IMAGE UPLOADER (Catbox API)
# =====================================================================
class UploadWorker(QThread):
    finished_signal = pyqtSignal(str)
    
    def __init__(self, image_path):
        super().__init__()
        self.image_path = image_path
        
    def run(self):
        # We will try multiple popular public anonymous hosts with User-Agent to bypass blocks
        uploaded_url = ""
        
        # 1. Try Uguu.se first (extremely reliable, direct PNG links, unblocked)
        try:
            uploaded_url = self.upload_uguu()
            if uploaded_url:
                self.finished_signal.emit(uploaded_url)
                return
        except Exception as e:
            print("[Uguu upload failed, trying fallback...]", e)
            
        # 2. Try Catbox.moe second
        try:
            uploaded_url = self.upload_catbox()
            if uploaded_url:
                self.finished_signal.emit(uploaded_url)
                return
        except Exception as e:
            print("[Catbox upload failed, trying fallback...]", e)
            
        # 3. Try Pixeldrain as third fallback
        try:
            uploaded_url = self.upload_pixeldrain()
            if uploaded_url:
                self.finished_signal.emit(uploaded_url)
                return
        except Exception as e:
            print("[Pixeldrain upload failed]", e)
            
        # If all failed, emit empty string
        self.finished_signal.emit("")

    def upload_uguu(self):
        import urllib.request
        import uuid
        import json
        url = "https://uguu.se/upload"
        boundary = "----WebKitFormBoundary" + str(uuid.uuid4()).replace("-", "")
        with open(self.image_path, "rb") as f:
            file_content = f.read()
            
        body = []
        body.append(f"--{boundary}".encode('utf-8'))
        body.append('Content-Disposition: form-data; name="files[]"; filename="crop.png"'.encode('utf-8'))
        body.append('Content-Type: image/png'.encode('utf-8'))
        body.append(''.encode('utf-8'))
        body.append(file_content)
        
        body.append(f"--{boundary}--".encode('utf-8'))
        body.append(''.encode('utf-8'))
        payload = b"\r\n".join(body)
        
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "Content-Length": str(len(payload)),
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as res:
            res_data = json.loads(res.read().decode('utf-8'))
            if res_data.get("success") and len(res_data.get("files", [])) > 0:
                return res_data["files"][0]["url"]
        return ""

    def upload_catbox(self):
        import urllib.request
        import uuid
        url = "https://catbox.moe/user/api.php"
        boundary = "----WebKitFormBoundary" + str(uuid.uuid4()).replace("-", "")
        with open(self.image_path, "rb") as f:
            file_content = f.read()
            
        body = []
        body.append(f"--{boundary}".encode('utf-8'))
        body.append('Content-Disposition: form-data; name="reqtype"'.encode('utf-8'))
        body.append(''.encode('utf-8'))
        body.append('fileupload'.encode('utf-8'))
        
        body.append(f"--{boundary}".encode('utf-8'))
        body.append('Content-Disposition: form-data; name="fileToUpload"; filename="crop.png"'.encode('utf-8'))
        body.append('Content-Type: image/png'.encode('utf-8'))
        body.append(''.encode('utf-8'))
        body.append(file_content)
        
        body.append(f"--{boundary}--".encode('utf-8'))
        body.append(''.encode('utf-8'))
        payload = b"\r\n".join(body)
        
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "Content-Length": str(len(payload)),
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as res:
            return res.read().decode('utf-8').strip()

    def upload_pixeldrain(self):
        import urllib.request
        import uuid
        import json
        url = "https://pixeldrain.com/api/file"
        boundary = "----WebKitFormBoundary" + str(uuid.uuid4()).replace("-", "")
        with open(self.image_path, "rb") as f:
            file_content = f.read()
            
        body = []
        body.append(f"--{boundary}".encode('utf-8'))
        body.append('Content-Disposition: form-data; name="file"; filename="crop.png"'.encode('utf-8'))
        body.append('Content-Type: image/png'.encode('utf-8'))
        body.append(''.encode('utf-8'))
        body.append(file_content)
        
        body.append(f"--{boundary}--".encode('utf-8'))
        body.append(''.encode('utf-8'))
        payload = b"\r\n".join(body)
        
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "Content-Length": str(len(payload)),
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as res:
            res_data = json.loads(res.read().decode('utf-8'))
            if res_data.get("success"):
                file_id = res_data.get("id")
                return f"https://pixeldrain.com/api/file/{file_id}"
            return ""

# =====================================================================
# MAIN GRAPHICAL SCREEN CROP OVERLAY
# =====================================================================
class ScreenOverlay(QWidget):
    def __init__(self, on_close_callback=None):
        super().__init__()
        self.on_close_callback = on_close_callback
        self.hud = None
        self.extracted_text = ""
        
        # Capture the current screen state instantly before displaying overlay
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            print("[Error] No primary screen found.")
            self.close()
            return
            
        self.screenshot = screen.grabWindow(0)
        self.setGeometry(screen.geometry())
        
        # Set frameless, transparent, stays-on-top window
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.SubWindow
        )
        
        # Draw custom large, high-visibility neon-emerald crosshair cursor (10% larger: 36x36)
        cursor_pixmap = QPixmap(36, 36)
        cursor_pixmap.fill(Qt.GlobalColor.transparent)
        
        cursor_painter = QPainter(cursor_pixmap)
        cursor_painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 1. Draw high-contrast dark drop shadow lines (3px wide) for light backgrounds
        shadow_pen = QPen(QColor(10, 10, 15, 200), 3, Qt.PenStyle.SolidLine)
        cursor_painter.setPen(shadow_pen)
        # Horizontal shadow line
        cursor_painter.drawLine(4, 18, 32, 18)
        # Vertical shadow line
        cursor_painter.drawLine(18, 4, 18, 32)
        
        # 2. Draw neon emerald core lines (1.5px wide)
        neon_pen = QPen(QColor(0, 255, 136, 255), 1, Qt.PenStyle.SolidLine)
        cursor_painter.setPen(neon_pen)
        # Horizontal core line
        cursor_painter.drawLine(5, 18, 31, 18)
        # Vertical core line
        cursor_painter.drawLine(18, 5, 18, 31)
        
        # 3. Draw sharp center target dot
        cursor_painter.setPen(Qt.PenStyle.NoPen)
        cursor_painter.setBrush(QColor(0, 255, 136, 255))
        cursor_painter.drawEllipse(17, 17, 3, 3)
        
        cursor_painter.end()
        
        from PyQt6.QtGui import QCursor
        self.setCursor(QCursor(cursor_pixmap, 18, 18))
        
        self.start_point = QPoint()
        self.end_point = QPoint()
        self.is_drawing = False
        
        # Cinematic dark screen dim fade-in animation
        self.overlay_alpha = 0
        self.fade_timer = QTimer(self)
        self.fade_timer.timeout.connect(self.overlay_fade_step)
        self.fade_timer.start(12) # Butter-smooth 80 FPS step

    def overlay_fade_step(self):
        self.overlay_alpha += 12
        if self.overlay_alpha >= 140:
            self.overlay_alpha = 140
            self.fade_timer.stop()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        
        # Draw base screenshot (Qt automatically handles logical-to-physical scale here)
        painter.drawPixmap(self.rect(), self.screenshot)
        
        # Darken the screen dynamically using animated alpha
        self.overlay_color = QColor(10, 10, 15, self.overlay_alpha)
        painter.fillRect(self.rect(), self.overlay_color)
        
        if self.is_drawing:
            selection_rect = QRect(self.start_point, self.end_point).normalized()
            
            # Punch a hole in the overlay to highlight the selected crop area in full clarity
            ratio = self.devicePixelRatioF()
            physical_rect = QRect(
                int(selection_rect.x() * ratio),
                int(selection_rect.y() * ratio),
                int(selection_rect.width() * ratio),
                int(selection_rect.height() * ratio)
            )
            
            # Draw physical area of screenshot into logical screen coordinates (removes zoom effect)
            painter.drawPixmap(selection_rect, self.screenshot, physical_rect)
            
            # Highly visible, futuristic multi-layered neon-emerald glow effect
            # Layer 1: Soft wide neon glow (width 8px, alpha 45)
            glow_pen_wide = QPen(QColor(0, 255, 136, 45), 8, Qt.PenStyle.SolidLine)
            painter.setPen(glow_pen_wide)
            painter.drawRect(selection_rect)
            
            # Layer 2: Medium glowing accent (width 4px, alpha 120)
            glow_pen_mid = QPen(QColor(0, 255, 136, 120), 4, Qt.PenStyle.SolidLine)
            painter.setPen(glow_pen_mid)
            painter.drawRect(selection_rect)
            
            # Layer 3: Solid ultra-bright core (width 2px, alpha 255)
            core_pen = QPen(QColor(0, 255, 136, 255), 2, Qt.PenStyle.SolidLine)
            painter.setPen(core_pen)
            painter.drawRect(selection_rect)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # If HUD exists and is active, let them click it
            if self.hud is not None:
                return
            self.start_point = event.position().toPoint()
            self.end_point = self.start_point
            self.is_drawing = True
            self.update()

    def mouseMoveEvent(self, event):
        if self.is_drawing:
            self.end_point = event.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.is_drawing:
            self.is_drawing = False
            self.end_point = event.position().toPoint()
            
            selection_rect = QRect(self.start_point, self.end_point).normalized()
            
            # Crop only if the area is large enough to contain characters
            if selection_rect.width() > 5 and selection_rect.height() > 5:
                # Calculate physical rectangle based on screen scaling
                ratio = self.devicePixelRatioF()
                physical_rect = QRect(
                    int(selection_rect.x() * ratio),
                    int(selection_rect.y() * ratio),
                    int(selection_rect.width() * ratio),
                    int(selection_rect.height() * ratio)
                )
                
                # Copy from physical bounds
                cropped = self.screenshot.copy(physical_rect)
                cropped.save("temp_crop.png")
                
                # Show the choices HUD INSTANTLY with zero delay!
                self.show_hud_menu(selection_rect)
                
                # Start OCR asynchronously in the background so main thread never freezes
                self.ocr_thread = OCRWorker("temp_crop.png")
                self.ocr_thread.finished_signal.connect(self.on_ocr_finished)
                self.ocr_thread.start()
            else:
                self.close()
                if self.on_close_callback:
                    self.on_close_callback()

    def show_hud_menu(self, selection_rect):
        self.last_selection_rect = selection_rect
        self.hud = HUDMenu(
            text=self.extracted_text,
            on_copy=self.hud_copy,
            on_search_image=self.hud_search_image,
            on_search_text=self.hud_search_text,
            parent=self # Pass self as parent so it renders inside the overlay coordinates
        )
        
        self.hud.resize_to_fit()
        self.hud.show_animated()

    def on_ocr_finished(self, text):
        self.extracted_text = text
        if self.hud:
            self.hud.update_text_detected(text)

    def hud_copy(self):
        import pyperclip
        from PyQt6.QtWidgets import QApplication
        
        # Alphanumeric heuristic to filter out OCR noise (lines, dots, symbols)
        clean_text = "".join(c for c in self.extracted_text if c.isalnum())
        
        if len(clean_text) >= 2:
            pyperclip.copy(self.extracted_text)
            print("\n" + "="*40)
            print("--- COPIED TEXT VIA HUD ---")
            print(self.extracted_text)
            print("="*40)
            self.cleanup_and_close()
        else:
            # Copy the cropped QPixmap to clipboard (perfect for images/drawings)
            ratio = self.devicePixelRatioF()
            selection_rect = self.last_selection_rect
            physical_rect = QRect(
                int(selection_rect.x() * ratio),
                int(selection_rect.y() * ratio),
                int(selection_rect.width() * ratio),
                int(selection_rect.height() * ratio)
            )
            cropped = self.screenshot.copy(physical_rect)
            QApplication.clipboard().setPixmap(cropped)
            
            print("\n" + "="*40)
            print("--- COPIED IMAGE CROP TO CLIPBOARD ---")
            print("========================================")
            self.cleanup_and_close()

    def hud_search_text(self):
        import pyperclip, webbrowser, urllib.parse
        pyperclip.copy(self.extracted_text)
        print("\n" + "="*40)
        print("--- COPIED & ROUTED VIA HUD (TEXT SEARCH) ---")
        print(self.extracted_text)
        print("="*40)
        
        search_query = urllib.parse.quote(self.extracted_text)
        webbrowser.open(f"https://www.google.com/search?q={search_query}")
        self.cleanup_and_close()

    def hud_search_image(self):
        # Draw physical crop and save for upload
        ratio = self.devicePixelRatioF()
        selection_rect = self.last_selection_rect
        physical_rect = QRect(
            int(selection_rect.x() * ratio),
            int(selection_rect.y() * ratio),
            int(selection_rect.width() * ratio),
            int(selection_rect.height() * ratio)
        )
        cropped = self.screenshot.copy(physical_rect)
        cropped.save("temp_upload.png")
        
        print("\n[SnapRoute] Uploading crop for Reverse Image Search...")
        
        # Start background upload thread (prevents UI freezing)
        self.upload_thread = UploadWorker("temp_upload.png")
        self.upload_thread.finished_signal.connect(self.on_upload_finished)
        self.upload_thread.start()
        
        # Hide overlay instantly so user sees it closed while uploading in background
        self.hide()

    def on_upload_finished(self, uploaded_url):
        import webbrowser, urllib.parse
        if uploaded_url:
            print("[SnapRoute] Upload complete! Opening Google Lens...")
            lens_query = urllib.parse.quote(uploaded_url)
            webbrowser.open(f"https://lens.google.com/uploadbyurl?url={lens_query}")
        else:
            print("[Upload Error] Reverse Image Search failed.")
            webbrowser.open("https://images.google.com")
            
        # Clean up temporary upload crop
        if os.path.exists("temp_upload.png"):
            try:
                os.remove("temp_upload.png")
            except Exception:
                pass
                
        self.cleanup_and_close()

    def cleanup_and_close(self):
        if os.path.exists("temp_crop.png"):
            try:
                os.remove("temp_crop.png")
            except Exception:
                pass
                
        if self.hud:
            # Fade out the HUD smoothly, then close this window
            self.hud.close_animated(self.close)
            self.hud = None
        else:
            self.close()
            
        if self.on_close_callback:
            self.on_close_callback()

    def keyPressEvent(self, event):
        # Escape closes HUD or cancel drawing
        if event.key() == Qt.Key.Key_Escape:
            self.cleanup_and_close()
