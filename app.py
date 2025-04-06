import sys
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QSlider,
    QScrollArea,
    QHBoxLayout,
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextBrowser, QLabel
from PySide6.QtCore import Qt
from PySide6.QtCore import QFile, QTextStream
import os
from PySide6.QtGui import QIcon
import json
from PySide6.QtWidgets import QMessageBox
from markdown import markdown


def get_resource_path(filename):
    """Get the absolute path to a resource file."""
    if hasattr(sys, "_MEIPASS"):
        # For bundled files inside the PyInstaller package
        return os.path.join(sys._MEIPASS, filename)
    else:
        # For development mode
        return os.path.join(os.path.dirname(__file__), filename)


def get_external_file_path(filename):
    """Get the absolute path to an external file (e.g., stations.json)."""
    # Look for the file in the same directory as the executable
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(os.path.dirname(sys.executable), filename)
    else:
        # In development mode, look in the script's directory
        return os.path.join(os.path.dirname(__file__), filename)


class RadioPlayer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("R/F")
        self.setMinimumSize(200, 200)
        self.always_on_top = False

        STATIONS = self.load_stations()

        if hasattr(sys, "_MEIPASS"):
            icon_path = os.path.join(sys._MEIPASS, "radio.ico")
        else:
            icon_path = "radio.ico"

        self.setWindowIcon(QIcon(icon_path))
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        self.load_styles()

        self.audio_output = QAudioOutput()
        self.player = QMediaPlayer()
        self.player.setAudioOutput(self.audio_output)

        self.player.errorOccurred.connect(self.update_now_playing_on_error)

        self.now_playing_label = QLabel("🎵 Hi")
        self.now_playing_label.setObjectName("now_playing_label")

        main_layout.addWidget(self.now_playing_label)

        # Scroll Area for Radio Buttons
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

        self.buttons = []

        for name, url in STATIONS.items():
            if url is None:  # Check if it's a separator
                group_title = QLabel(name)  # Create a label for the group title
                group_title.setAlignment(Qt.AlignCenter)  # Center-align the text
                group_title.setObjectName(
                    "group_title"
                )  # Set the object name for styling

                scroll_layout.addWidget(group_title)
                continue

            btn = QPushButton(name)
            btn.clicked.connect(
                lambda _, u=url, n=name, b=btn: self.play_station(u, n, b)
            )
            scroll_layout.addWidget(btn)
            self.buttons.append(btn)

        volume_container = QWidget()
        volume_layout = QHBoxLayout()  # Use QHBoxLayout for horizontal alignment
        volume_layout.setContentsMargins(0, 10, 0, 10)
        volume_container.setLayout(volume_layout)

        volume_slider = QSlider(Qt.Horizontal)
        volume_slider.setRange(0, 100)
        volume_slider.setValue(50)
        volume_slider.valueChanged.connect(
            lambda value: self.audio_output.setVolume(value / 100)
        )

        pause_btn = QPushButton("■")
        pause_btn.setObjectName("stop_btn")
        pause_btn.clicked.connect(self.pause_playback)
        volume_layout.addWidget(pause_btn)  # Add the pause button to the layout
        volume_layout.addWidget(volume_slider)  # Add the volume slider to the layout

        # Add a toggle button for "Always on Top"
        self.toggle_button = QPushButton("↑")
        self.toggle_button.setObjectName("toggle_btn_off")
        self.toggle_button.clicked.connect(self.toggle_always_on_top)
        volume_layout.addWidget(self.toggle_button)

        # Add a button to open the README file
        readme_btn = QPushButton("?")
        readme_btn.setObjectName("readme_btn")
        readme_btn.clicked.connect(self.open_readme)
        volume_layout.addWidget(readme_btn)

        main_layout.addWidget(volume_container)  # Add the container to the main layout

    # Load STATIONS from an external JSON file
    def load_stations(self):
        stations_file = get_external_file_path("stations.json")
        try:
            with open(stations_file, "r", encoding="utf-8") as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"Error: {stations_file} not found.")
            return {}
        except json.JSONDecodeError:
            print(f"Error: Failed to parse {stations_file}.")
            return {}

    def play_station(self, url, name, button):
        for btn in self.buttons:
            btn.setObjectName("")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        button.setObjectName("on_btn")
        button.style().unpolish(button)
        button.style().polish(button)

        self.player.setSource(QUrl(url))
        self.player.play()
        self.now_playing_label.setText(f"🎵 Now Playing: {name} ")

    def load_styles(self):
        # Determine the path to the QSS file
        qss_path = get_resource_path("styles.qss")

        # Load the QSS file
        file = QFile(qss_path)
        if file.open(QFile.ReadOnly | QFile.Text):
            stream = QTextStream(file)
            self.setStyleSheet(stream.readAll())

    def update_now_playing_on_error(self, error):
        if error:
            self.now_playing_label.setText("❌ Unable to play")

    def pause_playback(self):
        self.player.stop()

        for btn in self.buttons:
            btn.setObjectName("")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        self.now_playing_label.setText("🎵 Hi")

    def toggle_always_on_top(self):
        self.always_on_top = not self.always_on_top
        self.setWindowFlag(Qt.WindowStaysOnTopHint, self.always_on_top)
        self.show()  # Reapply the window flags

        # Update the button style based on the state
        if self.always_on_top:
            self.toggle_button.setObjectName("toggle_btn_on")
        else:
            self.toggle_button.setObjectName("toggle_btn_off")

        # Force style update
        self.toggle_button.style().unpolish(self.toggle_button)
        self.toggle_button.style().polish(self.toggle_button)

    def open_readme(self):
        readme_path = get_resource_path("README.md")
        if os.path.exists(readme_path):
            with open(readme_path, "r", encoding="utf-8") as file:
                readme_content = file.read()

            # Convert Markdown to HTML
            html_content = markdown(readme_content)

            # Create a dialog to display the README
            dialog = QDialog(self)
            dialog.setWindowTitle("README")
            dialog.setMinimumSize(600, 400)

            layout = QVBoxLayout(dialog)
            text_browser = QTextBrowser(dialog)
            text_browser.setHtml(html_content)  # Set the HTML content
            layout.addWidget(text_browser)

            dialog.setLayout(layout)
            dialog.exec()
        else:
            msg = QMessageBox(self)
            msg.setWindowTitle("Error")
            msg.setText("README.md file not found.")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    app.setStyle("Fusion")

    win = RadioPlayer()
    win.show()
    sys.exit(app.exec())


# pyinstaller --clean --onefile --windowed --icon=radio.ico --name=RadioF --add-data "radio.ico;." --add-data "styles.qss;." --add-data "README.md;." app.py
