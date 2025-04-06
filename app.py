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
from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt
from PySide6.QtCore import QFile, QTextStream
import os
from PySide6.QtGui import QIcon

STATIONS = {
    "Jazz": None,
    "TSF Jazz": "http://tsfjazz.ice.infomaniak.ch/tsfjazz-high.mp3",
    "FIP jazz": "https://icecast.radiofrance.fr/fipjazz-midfi.mp3?id=radiofrance",
    "Classic": None,
    "France Musique": "http://direct.francemusique.fr/live/francemusique-midfi.mp3",
    "Radio Classique": "http://radioclassique.ice.infomaniak.ch/radioclassique-high.mp3",
    "BBC 3": "http://as-hls-ww-live.akamaized.net/pool_23461179/live/ww/bbc_radio_three/bbc_radio_three.isml/bbc_radio_three-audio%3d96000.norewind.m3u8",
    "Electro": None,
    "Noods": "https://noods-radio.radiocult.fm/stream",
    "FIP electro": "https://icecast.radiofrance.fr/fipelectro-midfi.mp3?id=radiofrance",
    "Other": None,
    "FIP main": "http://direct.fipradio.fr/live/fip-midfi.mp3",
    "BBC 6 Music": "http://as-hls-ww-live.akamaized.net/pool_81827798/live/ww/bbc_6music/bbc_6music.isml/bbc_6music-audio%3d96000.norewind.m3u8",
    "-": None,
}


class RadioPlayer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("R/F")
        self.setMinimumSize(200, 200)
        self.always_on_top = False  # Track the state

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

        main_layout.addWidget(volume_container)  # Add the container to the main layout

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
        if hasattr(sys, "_MEIPASS"):
            # Use the temporary folder created by PyInstaller
            qss_path = os.path.join(sys._MEIPASS, "styles.qss")
        else:
            # Use the local path during development
            qss_path = "styles.qss"

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


if __name__ == "__main__":
    app = QApplication(sys.argv)

    app.setStyle("Fusion")

    win = RadioPlayer()
    win.show()
    sys.exit(app.exec())


# pyinstaller --clean --onefile --windowed --icon=radio.ico --name=RadioF --add-data "styles.qss;." app.py
# pyinstaller --clean --onefile --windowed --icon=radio.ico --name=RadioF --add-data "radio.ico;." --add-data "styles.qss;." app.py
# https://streamurl.link/
# https://gist.github.com/bpsib/67089b959e4fa898af69fea59ad74bc3
# https://community.roonlabs.com/t/new-fip-streaming-url/87335/7
