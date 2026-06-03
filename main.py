import sys
import os
import queue
import keyboard
from PyQt6.QtCore import Qt, QTimer, QObject
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QPen, QAction
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from box_search import ScreenOverlay

# Thread-safe queue to pass hotkey triggers from background listener thread to main GUI thread
trigger_queue = queue.Queue()
overlay_window = None

def hotkey_callback():
    """Callback triggered by keyboard listener on a background thread."""
    trigger_queue.put(True)

def ignite_sequence():
    """Main GUI thread trigger for the screen overlay."""
    global overlay_window, welcome
    print("\n[SnapRoute] Time Freeze activated. Draw your box...")
    
    # Close welcome splash window instantly if it's still active to avoid stay-on-top conflicts
    try:
        if 'welcome' in globals() and welcome is not None:
            welcome.close()
    except Exception:
        pass
        
    # Remove older crops
    if os.path.exists("temp_crop.png"):
        try:
            os.remove("temp_crop.png")
        except Exception:
            pass

    # Safe initialization of the widget on the main GUI thread
    if overlay_window is not None:
        overlay_window.close()
        
    # Instantiate the overlay window without the Assistant launcher
    overlay_window = ScreenOverlay(on_close_callback=None)
    overlay_window.show()

class HotkeyPollingManager(QObject):
    def __init__(self):
        super().__init__()
        # High-frequency polling timer (runs entirely on the main GUI thread)
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_trigger)
        self.timer.start(50) # Check every 50ms (instantly responsive, 0% CPU overhead)

    def check_trigger(self):
        if not trigger_queue.empty():
            # Clear all pending triggers in the queue
            while not trigger_queue.empty():
                trigger_queue.get()
            
            # Start the screen crop overlay on the main thread
            ignite_sequence()

def create_dynamic_icon():
    """Dynamically creates a high-res circular neon-emerald target icon."""
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.GlobalColor.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    # Draw sleek dark navy circular background
    painter.setBrush(QColor(10, 10, 15))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(4, 4, 56, 56)
    
    # Draw neon emerald outer target ring
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.setPen(QPen(QColor(0, 255, 136), 4))
    painter.drawEllipse(10, 10, 44, 44)
    
    # Draw neon emerald center crosshair dot
    painter.setBrush(QColor(0, 255, 136))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(26, 26, 12, 12)
    
    painter.end()
    return QIcon(pixmap)

from PyQt6.QtWidgets import QWidget, QFrame, QVBoxLayout, QLabel
from PyQt6.QtGui import QGuiApplication

class WelcomeWindow(QWidget):
    def __init__(self):
        super().__init__()
        # Frameless, transparent, stays-on-top window
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        
        self.resize(360, 160)
        self.center_window()
        self.init_ui()
        
        # Smooth fade-out animation parameters
        self.opacity = 1.0
        self.fade_timer = QTimer(self)
        self.fade_timer.timeout.connect(self.fade_step)
        
        # Display for 2.5 seconds, then begin fading out
        QTimer.singleShot(2500, self.start_fade)
        
    def center_window(self):
        screen = QGuiApplication.primaryScreen().geometry()
        self.setGeometry(
            (screen.width() - self.width()) // 2,
            (screen.height() - self.height()) // 2,
            self.width(),
            self.height()
        )
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Dark glassmorphic frame with glowing neon emerald border
        self.frame = QFrame(self)
        self.frame.setStyleSheet("""
            QFrame {
                background-color: rgba(12, 12, 20, 245);
                border: 2px solid rgba(0, 255, 136, 220);
                border-radius: 16px;
            }
        """)
        
        frame_layout = QVBoxLayout(self.frame)
        frame_layout.setContentsMargins(20, 20, 20, 20)
        frame_layout.setSpacing(10)
        
        # Title text
        title = QLabel("🚀 SNAPROUTE ACTIVE", self.frame)
        title.setStyleSheet("color: #FFFFFF; font-weight: bold; font-size: 16px; letter-spacing: 2px; border: none; background: transparent;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        frame_layout.addWidget(title)
        
        # Shortcut text
        shortcut = QLabel("Press Ctrl + Shift + S to Crop", self.frame)
        shortcut.setStyleSheet("color: rgba(0, 255, 136, 255); font-weight: bold; font-size: 13px; border: none; background: transparent;")
        shortcut.setAlignment(Qt.AlignmentFlag.AlignCenter)
        frame_layout.addWidget(shortcut)
        
        # Description text
        desc = QLabel("Copy images/text or search Google Lens instantly", self.frame)
        desc.setStyleSheet("color: rgba(255, 255, 255, 150); font-size: 10px; border: none; background: transparent;")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        frame_layout.addWidget(desc)
        
        layout.addWidget(self.frame)
        
    def start_fade(self):
        self.fade_timer.start(30) # 30ms step
        
    def fade_step(self):
        self.opacity -= 0.05
        if self.opacity <= 0:
            self.fade_timer.stop()
            self.close()
        else:
            self.setWindowOpacity(self.opacity)

if __name__ == "__main__":
    print("="*60)
    print("      SNAPROUTE SCREEN CROP OCR & SMART ROUTER")
    print("="*60)
    print("• Capture Trigger: Press 'Ctrl + Shift + S' anywhere on your PC")
    print("• Bounding Box   : Click & drag to draw a box; release to capture")
    print("• HUD Actions    : Select 'Copy' or 'Search'")
    print("• Exit Server    : Use System Tray -> Quit, or close terminal")
    print("="*60)

    # 1. Initialize QApplication
    app = QApplication(sys.argv)
    
    # Show the beautiful Welcome splash screen!
    welcome = WelcomeWindow()
    welcome.show()
    
    # Prevent Qt from quitting the event loop when individual screens close
    app.setQuitOnLastWindowClosed(False)

    # 2. Setup the dynamic system tray integration
    if QSystemTrayIcon.isSystemTrayAvailable():
        tray_icon = QSystemTrayIcon(create_dynamic_icon(), app)
        tray_menu = QMenu()
        
        # Add actions
        capture_action = QAction("Trigger Capture (Ctrl+Shift+S)", app)
        capture_action.triggered.connect(ignite_sequence)
        tray_menu.addAction(capture_action)
        
        tray_menu.addSeparator()
        
        quit_action = QAction("Quit SnapRoute", app)
        quit_action.triggered.connect(app.quit)
        tray_menu.addAction(quit_action)
        
        tray_icon.setContextMenu(tray_menu)
        tray_icon.setToolTip("SnapRoute OCR")
        tray_icon.show()
        
        # Beautiful startup message
        tray_icon.showMessage(
            "SnapRoute",
            "Armed & hovering. Press Ctrl + Shift + S to crop screen!",
            QSystemTrayIcon.MessageIcon.Information,
            3000
        )
    else:
        print("[Warning] System Tray is not available on this desktop environment.")

    # 3. Start the Hotkey polling manager
    manager = HotkeyPollingManager()

    # 4. Register global keyboard hotkey on the background thread
    keyboard.add_hotkey('ctrl+shift+s', hotkey_callback)

    # 5. Start main Qt event loop
    sys.exit(app.exec())
