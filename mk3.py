from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QPushButton, QLabel, QLineEdit, QScrollArea)
from PyQt6.QtCore import QTimer, Qt, QDateTime
import sys
import json
from datetime import datetime
from pathlib import Path


class StopwatchWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.minutes = 0
        self.precise_seconds = 0
        self.is_running = False
        self.last_started = None

        # Main layout for the widget
        main_layout = QVBoxLayout()

        # Top row layout (project name, chunked time, play button)
        top_row = QHBoxLayout()

        # Project name input
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Project Name")
        top_row.addWidget(self.name_input)

        # 15-minute chunked time display
        self.chunk_time_label = QLabel("00:00")
        self.chunk_time_label.setStyleSheet("font-family: monospace; font-size: 20px;")
        top_row.addWidget(self.chunk_time_label)

        # Play/Pause button
        self.toggle_button = QPushButton("▶")
        self.toggle_button.clicked.connect(self.toggle_timer)
        top_row.addWidget(self.toggle_button)

        main_layout.addLayout(top_row)

        # Bottom row layout (precise time and last started)
        bottom_row = QHBoxLayout()

        # Precise time display
        self.precise_time_label = QLabel("Precise time: 00:00:00")
        self.precise_time_label.setStyleSheet("font-family: monospace; font-size: 12px; color: gray;")
        bottom_row.addWidget(self.precise_time_label)

        # Last started time display
        self.last_started_label = QLabel("Last started: --:--:--")
        self.last_started_label.setStyleSheet("font-family: monospace; font-size: 12px; color: gray;")
        bottom_row.addWidget(self.last_started_label)

        main_layout.addLayout(bottom_row)

        self.setLayout(main_layout)

        # Chunked timer (15-minute intervals)
        self.chunk_timer = QTimer(self)
        self.chunk_timer.timeout.connect(self.update_chunk_time)
        self.chunk_timer.setInterval(60000)  # Update every minute

        # Precise timer (1-second intervals)
        self.precise_timer = QTimer(self)
        self.precise_timer.timeout.connect(self.update_precise_time)
        self.precise_timer.setInterval(1000)  # Update every second

    def toggle_timer(self):
        self.is_running = not self.is_running
        if self.is_running:
            self.toggle_button.setText("⏸")
            # Start with 15 minutes immediately for chunked time
            self.minutes = 15
            self.update_chunk_display()
            self.chunk_timer.start()

            # Start precise timer
            self.precise_timer.start()

            # Update last started time
            self.last_started = datetime.now()
            self.update_last_started()
        else:
            self.toggle_button.setText("▶")
            self.chunk_timer.stop()
            self.precise_timer.stop()
            # Round to nearest 15 when stopping
            self.minutes = ((self.minutes + 7) // 15) * 15
            self.update_chunk_display()

    def update_chunk_time(self):
        if self.is_running:
            self.minutes += 15
            self.update_chunk_display()

    def update_precise_time(self):
        if self.is_running:
            self.precise_seconds += 1
            self.update_precise_display()

    def update_chunk_display(self):
        hours = self.minutes // 60
        display_minutes = self.minutes % 60
        self.chunk_time_label.setText(f"{hours:02d}:{display_minutes:02d}")

    def update_precise_display(self):
        hours = self.precise_seconds // 3600
        minutes = (self.precise_seconds % 3600) // 60
        seconds = self.precise_seconds % 60
        self.precise_time_label.setText(f"Precise time: {hours:02d}:{minutes:02d}:{seconds:02d}")

    def update_last_started(self):
        if self.last_started:
            time_str = self.last_started.strftime("%H:%M:%S")
            self.last_started_label.setText(f"Last started: {time_str}")

class TimeTrackerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Trackey the Marvelous Time Tracker")
        self.setMinimumSize(600, 400)

        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)

        # Date navigation
        date_nav = QHBoxLayout()
        prev_button = QPushButton("←")
        prev_button.clicked.connect(self.previous_day)
        self.date_label = QLabel(QDateTime.currentDateTime().toString("yyyy-MM-dd"))
        next_button = QPushButton("→")
        next_button.clicked.connect(self.next_day)

        date_nav.addWidget(prev_button)
        date_nav.addWidget(self.date_label)
        date_nav.addWidget(next_button)
        main_layout.addLayout(date_nav)

        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Container widget for scroll area
        scroll_widget = QWidget()
        self.stopwatches_layout = QVBoxLayout(scroll_widget)
        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)

        # Add new stopwatch button
        self.add_button = QPushButton("Add New Timer")
        self.add_button.clicked.connect(self.add_stopwatch)
        main_layout.addWidget(self.add_button)

        # Initialize the current date's data
        self.current_date = QDateTime.currentDateTime().toString("yyyy-MM-dd")

        # Load saved state for current date
        self.load_state()

        # Save state when closing
        self.destroyed.connect(self.save_state)

    def get_save_path(self):
        """Get the path for saving app state"""
        home = str(Path.home())
        save_dir = Path(home) / ".trackey"
        save_dir.mkdir(exist_ok=True)
        return save_dir / "state.json"

    def save_state(self):
        """Save the current state of all stopwatches"""
        save_path = self.get_save_path()

        # Load existing data first
        all_data = {}
        if save_path.exists():
            with open(save_path) as f:
                try:
                    all_data = json.load(f)
                except json.JSONDecodeError:
                    all_data = {}

        # Only save non-empty stopwatches
        current_states = []
        for i in range(self.stopwatches_layout.count()):
            widget = self.stopwatches_layout.itemAt(i).widget()
            if isinstance(widget, StopwatchWidget):
                state = widget.get_state()
                # Only save if there's actual time recorded or a project name
                if state['minutes'] > 0 or state['precise_seconds'] > 0 or state['project_name'].strip():
                    current_states.append(state)

        # Only save the date if there are actual stopwatches
        if current_states:
            all_data[self.current_date] = current_states
        elif self.current_date in all_data:
            # Remove the date if it's empty
            del all_data[self.current_date]

        # Save all data
        with open(save_path, 'w') as f:
            json.dump(all_data, f)

    def load_state(self):
        """Load saved stopwatches for current date"""
        save_path = self.get_save_path()

        # Clear existing stopwatches
        while self.stopwatches_layout.count():
            child = self.stopwatches_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if save_path.exists():
            with open(save_path) as f:
                try:
                    all_data = json.load(f)
                    if self.current_date in all_data:
                        states = all_data[self.current_date]
                        for state in states:
                            stopwatch = self.add_stopwatch()
                            stopwatch.load_state(state)
                        return
                except json.JSONDecodeError:
                    pass

        # Add one empty stopwatch if no saved state
        self.add_stopwatch()

    def add_stopwatch(self):
        stopwatch = StopwatchWidget()
        self.stopwatches_layout.addWidget(stopwatch)
        return stopwatch

    def previous_day(self):
        self.save_state()
        current_date = QDateTime.fromString(self.date_label.text(), "yyyy-MM-dd")
        new_date = current_date.addDays(-1)
        self.date_label.setText(new_date.toString("yyyy-MM-dd"))
        self.current_date = new_date.toString("yyyy-MM-dd")
        self.load_state()

    def next_day(self):
        self.save_state()
        current_date = QDateTime.fromString(self.date_label.text(), "yyyy-MM-dd")
        new_date = current_date.addDays(1)
        self.date_label.setText(new_date.toString("yyyy-MM-dd"))
        self.current_date = new_date.toString("yyyy-MM-dd")
        self.load_state()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TimeTrackerApp()
    window.show()
    sys.exit(app.exec())


###1. Process finished with exit code -1073740791 (0xC0000409)
###2. Let Claude work on an export/report function
###3. Let Claude explain the full stack setup
