import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, QPushButton, QSlider, QComboBox,
                               QSpinBox, QFrame, QGridLayout, QStackedWidget, 
                               QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QIcon, QPainter, QColor, QPen
import random


class ConstellationWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 220)
        self.setMaximumSize(600, 220)
        self.modulation_type = "QPSK"
        self.update_points()
        
    def set_modulation(self, mod_type):
        self.modulation_type = mod_type
        self.update_points()
        self.update()
        
    def update_points(self):
        if self.modulation_type == "BPSK":
            self.points = [(-1, 0), (1, 0)]
        elif self.modulation_type == "QPSK":
            self.points = [(0.75, 0.75), (-0.75, 0.75), (-0.75, -0.75), (0.75, -0.75)]
        elif self.modulation_type == "8PSK":
            import math
            self.points = []
            for i in range(8):
                angle = 2 * math.pi * i / 8 + math.pi / 8
                self.points.append((0.75 * math.cos(angle), 0.75 * math.sin(angle)))
        elif self.modulation_type == "16QAM":
            self.points = []
            for i in [-0.75, -0.25, 0.25, 0.75]:
                for j in [-0.75, -0.25, 0.25, 0.75]:
                    self.points.append((i, j))
        elif self.modulation_type == "64QAM":
            self.points = []
            vals = [-0.857, -0.612, -0.367, -0.122, 0.122, 0.367, 0.612, 0.857]
            for i in vals:
                for j in vals:
                    self.points.append((i, j))
        else:
            self.points = [(0.75, 0.75), (-0.75, 0.75), (-0.75, -0.75), (0.75, -0.75)]
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        painter.fillRect(self.rect(), QColor(255, 255, 255))
        
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        mid_x = self.width() // 2
        mid_y = self.height() // 2
        painter.drawLine(0, mid_y, self.width(), mid_y)
        painter.drawLine(mid_x, 0, mid_x, self.height())
        
        painter.setPen(QPen(QColor(59, 130, 246), 8))
        scale = min(self.width(), self.height()) * 0.35
        for x, y in self.points:
            px = mid_x + int(x * scale)
            py = mid_y - int(y * scale)
            painter.drawPoint(px, py)

class PowerSpectrumWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(600, 200)
        self.symbol_rate = 10  # Msps
        self.signal_power = 0  # dBm
        self.bandwidth = 20  # MHz
        
    def set_parameters(self, symbol_rate, signal_power, bandwidth):
        self.symbol_rate = symbol_rate
        self.signal_power = signal_power
        self.bandwidth = bandwidth
        self.update()
        
    def paintEvent(self, event):
        import math
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        painter.fillRect(self.rect(), QColor(255, 255, 255))
        
        width = self.width()
        height = self.height()
        
        num_points = 500
        frequencies = []
        psd_values = []
        
        power_linear = 10 ** (self.signal_power / 10.0)
        
        T = 1.0 / self.symbol_rate
        
        f_min = -self.bandwidth / 2.0
        f_max = self.bandwidth / 2.0
        
        for i in range(num_points):
            f = f_min + (f_max - f_min) * i / num_points
            
            x = math.pi * f * T
            if abs(x) < 1e-6:
                sinc_val = 1.0
            else:
                sinc_val = math.sin(x) / x
            
            psd = power_linear * T * (sinc_val ** 2)
            
            frequencies.append(f)
            psd_values.append(psd)
        
        max_psd = max(psd_values) if psd_values else 1.0
        if max_psd == 0:
            max_psd = 1.0
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(16, 185, 129))
        
        bar_width = width / num_points
        
        for i, psd in enumerate(psd_values):
            normalized = psd / max_psd
            bar_height = int(height * 0.9 * normalized)
            
            x = i * bar_width
            painter.drawRect(int(x), height - bar_height, int(bar_width) + 1, bar_height)


class ToggleSwitch(QCheckBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(44, 24)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        if self.isChecked():
            painter.setBrush(QColor(17, 24, 39))
        else:
            painter.setBrush(QColor(209, 213, 219))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, 44, 24, 12, 12)
        
        painter.setBrush(QColor(255, 255, 255))
        if self.isChecked():
            painter.drawEllipse(22, 2, 20, 20)
        else:
            painter.drawEllipse(2, 2, 20, 20)


class NoiseSpectrumWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(800, 250)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        painter.fillRect(self.rect(), QColor(255, 255, 255))
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(139, 92, 246))
        
        width = self.width()
        height = self.height()
        
        bands = [
            (0.05, 0.15, 12),
            (0.15, 0.30, 25),
            (0.30, 0.50, 38),
            (0.50, 0.70, 50),
            (0.70, 0.85, 30),
            (0.85, 0.95, 18)
        ]
        
        for start, end, bar_height_pct in bands:
            x_start = int(width * start)
            x_end = int(width * end)
            bar_width = x_end - x_start
            bar_height = int(height * bar_height_pct / 100)
            painter.drawRect(x_start, height - bar_height, bar_width, bar_height)

class SignalDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Signal Generation & Classification")
        self.setMinimumSize(1400, 900)
        
        # Apply stylesheet
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QLabel {
                color: #1f2937;
            }
            .title {
                font-size: 20px;
                font-weight: bold;
                color: #111827;
            }
            .subtitle {
                font-size: 13px;
                color: #6b7280;
            }
            .section-title {
                font-size: 15px;
                font-weight: 600;
                color: #111827;
            }
            .section-subtitle {
                font-size: 12px;
                color: #6b7280;
            }
            .card-title {
                font-size: 14px;
                font-weight: 600;
                color: #111827;
            }
            .stat-value {
                font-size: 18px;
                font-weight: 600;
                color: #111827;
            }
            .stat-label {
                font-size: 12px;
                color: #6b7280;
            }
            QPushButton {
                background-color: white;
                border: 1px solid #e5e7eb;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 13px;
                color: #374151;
            }
            QPushButton:hover {
                background-color: #f9fafb;
                border-color: #d1d5db;
            }
            QPushButton#primaryButton {
                background-color: #111827;
                color: white;
                border: none;
            }
            QPushButton#primaryButton:hover {
                background-color: #1f2937;
            }
            QPushButton#tabButton {
                background-color: white;
                border: none;
                border-bottom: 2px solid transparent;
                border-radius: 0px;
                padding: 12px 24px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton#tabButton:checked {
                border-bottom: 2px solid #111827;
                color: #111827;
            }
            QComboBox {
                background-color: white;
                border: 1px solid #e5e7eb;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
                color: #1f2937;
                min-height: 20px;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid #6b7280;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                border: 1px solid #e5e7eb;
                selection-background-color: #f3f4f6;
                selection-color: #111827;
            }
            QSpinBox {
                background-color: white;
                border: 1px solid #e5e7eb;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
                color: #1f2937;
                min-height: 20px;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 16px;
                border: none;
                background-color: transparent;
            }
            QSpinBox::up-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-bottom: 5px solid #6b7280;
            }
            QSpinBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #6b7280;
            }
            QSlider::groove:horizontal {
                border: none;
                height: 6px;
                background: #e5e7eb;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #111827;
                border: none;
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
            QFrame#card {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #e5e7eb;
            }
            QFrame#infoBox {
                background-color: #eff6ff;
                border: 1px solid #bfdbfe;
                border-radius: 8px;
                padding: 12px;
            }
            QCheckBox {
                spacing: 8px;
                font-size: 13px;
            }
            QCheckBox::indicator {
                width: 40px;
                height: 20px;
                border-radius: 10px;
                background-color: #d1d5db;
            }
            QCheckBox::indicator:checked {
                background-color: #111827;
            }
            QTableWidget {
                background-color: white;
                border: none;
                gridline-color: transparent;
                font-size: 13px;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f3f4f6;
                border-right: none;
            }
            QHeaderView::section {
                background-color: white;
                padding: 12px 8px;
                border: none;
                border-bottom: 1px solid #e5e7eb;
                font-weight: 600;
                font-size: 12px;
                color: #6b7280;
            }
            .badge {
                border-radius: 12px;
                padding: 6px 14px;
                font-size: 13px;
                font-weight: 600;
            }
            .badge-black {
                background-color: #111827;
                color: white;
            }
            .badge-red {
                background-color: #ef4444;
                color: white;
            }
        """)
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        header_layout = QHBoxLayout()
        
        title_layout = QVBoxLayout()
        title = QLabel("📈 Signal Generation & Classification")
        title.setProperty("class", "title")
        subtitle = QLabel("Configure waveforms, channels, train ML models, and analyze classification results")
        subtitle.setProperty("class", "subtitle")
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        title_layout.setSpacing(4)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        main_layout.addLayout(header_layout)
        
        tab_layout = QHBoxLayout()
        tab_layout.setSpacing(0)
        
        self.tab_buttons = []
        tabs = ["Waveform Selection", "Channel & Noise", "ML Training", "Inference Results"]
        for i, tab_name in enumerate(tabs):
            tab_btn = QPushButton(tab_name)
            tab_btn.setObjectName("tabButton")
            tab_btn.setCheckable(True)
            if i == 0:
                tab_btn.setChecked(True)
            tab_btn.clicked.connect(lambda checked, idx=i: self.switch_tab(idx))
            self.tab_buttons.append(tab_btn)
            tab_layout.addWidget(tab_btn)
        
        tab_layout.addStretch()
        main_layout.addLayout(tab_layout)
        
        from PySide6.QtWidgets import QStackedWidget
        self.content_stack = QStackedWidget()
        
        # Tab 0: Waveform Selection
        waveform_widget = QWidget()
        waveform_layout = QHBoxLayout(waveform_widget)
        waveform_layout.setSpacing(20)
        waveform_layout.setContentsMargins(0, 0, 0, 0)
        left_panel = self.create_left_panel()
        waveform_layout.addWidget(left_panel, 1)
        right_panel = self.create_right_panel()
        waveform_layout.addWidget(right_panel, 2)
        self.content_stack.addWidget(waveform_widget)
        
        # Tab 1: Channel & Noise
        channel_widget = self.create_channel_noise_tab()
        self.content_stack.addWidget(channel_widget)
        
        # Tab 2: ML Training (placeholder for now)
        ml_widget = QLabel("ML Training - TODO")
        ml_widget.setAlignment(Qt.AlignCenter)
        self.content_stack.addWidget(ml_widget)
        
        # Tab 3: Inference Results (placeholder for now)
        inference_widget = QLabel("Inference Results - TODO")
        inference_widget.setAlignment(Qt.AlignCenter)
        self.content_stack.addWidget(inference_widget)
        
        main_layout.addWidget(self.content_stack, 1)
    
    def create_left_panel(self):
        panel = QFrame()
        panel.setObjectName("card")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        title_layout = QVBoxLayout()
        title = QLabel("📡 RF Signal Configuration")
        title.setProperty("class", "section-title")
        subtitle = QLabel("Configure signal generation parameters")
        subtitle.setProperty("class", "section-subtitle")
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        title_layout.setSpacing(4)
        layout.addLayout(title_layout)
        
        mod_label = QLabel("Signal Type / Modulation")
        layout.addWidget(mod_label)
        self.modulation_combo = QComboBox()
        self.modulation_combo.addItems(["QPSK (Quadrature PSK)", "BPSK", "8PSK", "16QAM", "64QAM"])
        self.modulation_combo.setCurrentIndex(0)
        self.current_bits_per_symbol = 2.0
        self.modulation_combo.currentIndexChanged.connect(self.update_constellation)
        layout.addWidget(self.modulation_combo)
        
        self.carrier_freq_value = 2400
        carrier_slider_layout = self.create_slider_control_with_value_store("Carrier Frequency", 2400, "MHz", 400, 6000, "carrier_freq_value")
        layout.addLayout(carrier_slider_layout)
        range_label = QLabel("Range: 400 MHz - 6 GHz")
        range_label.setProperty("class", "section-subtitle")
        layout.addWidget(range_label)
        
        self.bandwidth_value = 20
        self.bandwidth_slider_layout = self.create_slider_control_with_value_store("Bandwidth", 20, "MHz", 1, 100, "bandwidth_value")
        layout.addLayout(self.bandwidth_slider_layout)
        
        self.symbol_rate_value = 10
        layout.addLayout(self.create_slider_control_with_value_store("Symbol Rate", 10, "Msps", 1, 50, "symbol_rate_value"))
        
        self.signal_power_value = 0
        layout.addLayout(self.create_slider_control_with_value_store("Signal Power", 0, "dBm", -30, 10, "signal_power_value"))
        
        sample_layout = QVBoxLayout()
        sample_layout.setSpacing(8)
        sample_header = QHBoxLayout()
        sample_label = QLabel("Samples per Symbol")
        sample_header.addWidget(sample_label)
        sample_header.addStretch()
        sample_layout.addLayout(sample_header)
        sample_spin = QSpinBox()
        sample_spin.setValue(8)
        sample_spin.setMinimum(2)
        sample_spin.setMaximum(32)
        sample_layout.addWidget(sample_spin)
        layout.addLayout(sample_layout)
        
        layout.addStretch()
        
        generate_btn = QPushButton("▶  Generate Dataset")
        generate_btn.setObjectName("primaryButton")
        layout.addWidget(generate_btn)
        
        save_btn = QPushButton("💾  Save Configuration")
        layout.addWidget(save_btn)
        
        export_btn = QPushButton("⬇  Export Samples")
        layout.addWidget(export_btn)
        
        return panel
    
    def switch_tab(self, index):
        for i, btn in enumerate(self.tab_buttons):
            btn.setChecked(i == index)
        self.content_stack.setCurrentIndex(index)
    
    def create_channel_noise_tab(self):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setSpacing(20)
        layout.setContentsMargins(0, 0, 0, 0)
        
        left_panel = QFrame()
        left_panel.setObjectName("card")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(24, 24, 24, 24)
        left_layout.setSpacing(20)
        
        title = QLabel("📡 Channel Configuration")
        title.setProperty("class", "section-title")
        subtitle = QLabel("Configure individual channel parameters")
        subtitle.setProperty("class", "section-subtitle")
        left_layout.addWidget(title)
        left_layout.addWidget(subtitle)
        
        table = QTableWidget(4, 4)
        table.setHorizontalHeaderLabels(["Channel", "Status", "Gain (dB)", "SNR (dB)"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(50)
        table.setSelectionMode(QTableWidget.NoSelection)
        table.setMaximumHeight(280)
        table.setShowGrid(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        channels_data = [
            ("Channel 1", True, "80 dB", "25.5 dB", False),
            ("Channel 2", True, "75 dB", "28.3 dB", False),
            ("Channel 3", False, "60 dB", "22.1 dB", True),
            ("Channel 4", True, "85 dB", "30.2 dB", False)
        ]
        
        for row, (channel, enabled, gain, snr, is_low_snr) in enumerate(channels_data):
            channel_widget = QWidget()
            channel_layout = QHBoxLayout(channel_widget)
            channel_layout.setContentsMargins(12, 0, 8, 0)
            channel_layout.setAlignment(Qt.AlignLeft)
            channel_label = QLabel(channel)
            channel_label.setStyleSheet("font-size: 13px; color: #1f2937; font-weight: 500;")
            channel_layout.addWidget(channel_label)
            channel_layout.addStretch()
            table.setCellWidget(row, 0, channel_widget)
            
            status_widget = QWidget()
            status_layout = QHBoxLayout(status_widget)
            status_layout.setContentsMargins(8, 0, 8, 0)
            status_layout.setAlignment(Qt.AlignLeft)
            toggle = ToggleSwitch()
            toggle.setChecked(enabled)
            status_layout.addWidget(toggle)
            status_layout.addStretch()
            table.setCellWidget(row, 1, status_widget)
            
            gain_widget = QWidget()
            gain_layout = QHBoxLayout(gain_widget)
            gain_layout.setContentsMargins(8, 0, 8, 0)
            gain_layout.setAlignment(Qt.AlignLeft)
            gain_label = QLabel(gain)
            gain_label.setProperty("class", "badge badge-black")
            gain_label.setAlignment(Qt.AlignCenter)
            gain_label.setStyleSheet("background-color: #111827; color: white; border-radius: 12px; padding: 6px 14px; font-size: 13px; font-weight: 600;")
            gain_layout.addWidget(gain_label)
            gain_layout.addStretch()
            table.setCellWidget(row, 2, gain_widget)
            
            snr_widget = QWidget()
            snr_layout = QHBoxLayout(snr_widget)
            snr_layout.setContentsMargins(8, 0, 8, 0)
            snr_layout.setAlignment(Qt.AlignLeft)
            snr_label = QLabel(snr)
            if is_low_snr:
                snr_label.setStyleSheet("background-color: #ef4444; color: white; border-radius: 12px; padding: 6px 14px; font-size: 13px; font-weight: 600;")
            else:
                snr_label.setStyleSheet("background-color: #111827; color: white; border-radius: 12px; padding: 6px 14px; font-size: 13px; font-weight: 600;")
            snr_label.setAlignment(Qt.AlignCenter)
            snr_layout.addWidget(snr_label)
            snr_layout.addStretch()
            table.setCellWidget(row, 3, snr_widget)
        
        left_layout.addWidget(table)
        
        info_box = QFrame()
        info_box.setObjectName("infoBox")
        info_layout = QHBoxLayout(info_box)
        info_icon = QLabel("ⓘ")
        info_icon.setStyleSheet("font-size: 16px; color: #3b82f6;")
        info_text = QLabel("<b>Active Channels</b><br/>3 of 4 channels enabled")
        info_text.setProperty("class", "section-subtitle")
        info_layout.addWidget(info_icon)
        info_layout.addWidget(info_text)
        info_layout.addStretch()
        left_layout.addWidget(info_box)
        
        left_layout.addStretch()
        
        layout.addWidget(left_panel, 1)
        
        right_side = QWidget()
        right_layout = QVBoxLayout(right_side)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(20)
        
        noise_card = QFrame()
        noise_card.setObjectName("card")
        noise_layout = QVBoxLayout(noise_card)
        noise_layout.setContentsMargins(24, 24, 24, 24)
        noise_layout.setSpacing(16)
        
        noise_header = QHBoxLayout()
        noise_title_layout = QVBoxLayout()
        noise_title = QLabel("🔊 Noise Configuration")
        noise_title.setProperty("class", "card-title")
        noise_subtitle = QLabel("Configure noise and interference parameters")
        noise_subtitle.setProperty("class", "section-subtitle")
        noise_title_layout.addWidget(noise_title)
        noise_title_layout.addWidget(noise_subtitle)
        noise_title_layout.setSpacing(2)
        noise_header.addLayout(noise_title_layout)
        noise_layout.addLayout(noise_header)
        
        noise_slider_layout = self.create_slider_control("Noise Level", 30, "dBm", -50, 0)
        noise_layout.addLayout(noise_slider_layout)
        
        awgn_layout = QHBoxLayout()
        awgn_left = QVBoxLayout()
        awgn_title = QLabel("AWGN (Additive White Gaussian Noise)")
        awgn_title.setProperty("class", "section-title")
        awgn_desc = QLabel("Enable white noise generation")
        awgn_desc.setProperty("class", "section-subtitle")
        awgn_left.addWidget(awgn_title)
        awgn_left.addWidget(awgn_desc)
        awgn_layout.addLayout(awgn_left)
        awgn_layout.addStretch()
        awgn_toggle = ToggleSwitch()
        awgn_toggle.setChecked(True)
        awgn_layout.addWidget(awgn_toggle)
        noise_layout.addLayout(awgn_layout)
        
        multipath_layout = QHBoxLayout()
        multipath_left = QVBoxLayout()
        multipath_title = QLabel("Multipath Fading")
        multipath_title.setProperty("class", "section-title")
        multipath_desc = QLabel("Simulate multipath interference")
        multipath_desc.setProperty("class", "section-subtitle")
        multipath_left.addWidget(multipath_title)
        multipath_left.addWidget(multipath_desc)
        multipath_layout.addLayout(multipath_left)
        multipath_layout.addStretch()
        multipath_toggle = ToggleSwitch()
        multipath_toggle.setChecked(False)
        multipath_layout.addWidget(multipath_toggle)
        noise_layout.addLayout(multipath_layout)
        
        apply_btn = QPushButton("Apply Noise Settings")
        apply_btn.setObjectName("primaryButton")
        noise_layout.addWidget(apply_btn)
        
        right_layout.addWidget(noise_card)
        
        spectrum_card = QFrame()
        spectrum_card.setObjectName("card")
        spectrum_layout = QVBoxLayout(spectrum_card)
        spectrum_layout.setContentsMargins(24, 24, 24, 24)
        spectrum_layout.setSpacing(16)
        
        spectrum_title = QLabel("Noise Power Spectrum")
        spectrum_title.setProperty("class", "card-title")
        spectrum_subtitle = QLabel("Frequency distribution of noise components")
        spectrum_subtitle.setProperty("class", "section-subtitle")
        spectrum_layout.addWidget(spectrum_title)
        spectrum_layout.addWidget(spectrum_subtitle)
        
        spectrum_widget = NoiseSpectrumWidget()
        spectrum_layout.addWidget(spectrum_widget)
        
        stats_layout = QGridLayout()
        stats_layout.setSpacing(20)
        
        stats = [
            ("Total Noise Power", "170 dBm"),
            ("Bandwidth", "60 Hz"),
            ("Noise Figure", "5.2 dB")
        ]
        
        for i, (label, value) in enumerate(stats):
            stat_container = QVBoxLayout()
            stat_label = QLabel(label)
            stat_label.setProperty("class", "stat-label")
            stat_value = QLabel(value)
            stat_value.setProperty("class", "stat-value")
            stat_container.addWidget(stat_label)
            stat_container.addWidget(stat_value)
            stats_layout.addLayout(stat_container, 0, i)
        
        spectrum_layout.addLayout(stats_layout)
        
        right_layout.addWidget(spectrum_card)
        
        layout.addWidget(right_side, 1)
        
        return widget
    
    def update_constellation(self, index):
        modulation_types = ["QPSK", "BPSK", "8PSK", "16QAM", "64QAM"]
        bits_per_symbol = [2.0, 1.0, 3.0, 4.0, 6.0]
        symbol_counts = [4, 2, 8, 16, 64]
        
        if hasattr(self, 'constellation'):
            self.constellation.set_modulation(modulation_types[index])
            
        self.current_bits_per_symbol = bits_per_symbol[index]
            
        if hasattr(self, 'bits_per_symbol_label'):
            self.bits_per_symbol_label.setText(f"{bits_per_symbol[index]}")
        if hasattr(self, 'symbol_count_label'):
            self.symbol_count_label.setText(f"{symbol_counts[index]}")
        
        self.update_spectral_efficiency()
    
    def update_spectral_efficiency(self):
        if hasattr(self, 'spectral_efficiency_label'):
            if hasattr(self, 'bandwidth_value') and self.bandwidth_value > 0:
                efficiency = (self.current_bits_per_symbol * self.symbol_rate_value) / self.bandwidth_value
                self.spectral_efficiency_label.setText(f"{efficiency:.2f} bps/Hz")
    
    def create_slider_control(self, label, value, unit, min_val, max_val):
        container = QVBoxLayout()
        container.setSpacing(8)
        
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        label_widget = QLabel(label)
        value_label = QLabel(f"{value} {unit}")
        value_label.setProperty("class", "stat-value")
        value_label.setMinimumHeight(24)
        header.addWidget(label_widget)
        header.addStretch()
        header.addWidget(value_label)
        container.addLayout(header)
        
        container.addSpacing(4)
        
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(min_val)
        slider.setMaximum(max_val)
        slider.setValue(value)
        slider.valueChanged.connect(lambda v, lbl=value_label, u=unit: lbl.setText(f"{v} {u}"))
        container.addWidget(slider)
        
        container.addSpacing(8)
        
        return container
    
    def create_slider_control_with_value_store(self, label, value, unit, min_val, max_val, attr_name):
        container = QVBoxLayout()
        container.setSpacing(8)
        
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        label_widget = QLabel(label)
        value_label = QLabel(f"{value} {unit}")
        value_label.setProperty("class", "stat-value")
        value_label.setMinimumHeight(24)
        header.addWidget(label_widget)
        header.addStretch()
        header.addWidget(value_label)
        container.addLayout(header)
        
        container.addSpacing(4)
        
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(min_val)
        slider.setMaximum(max_val)
        slider.setValue(value)
        
        def update_value(v):
            value_label.setText(f"{v} {unit}")
            setattr(self, attr_name, v)
            self.update_power_spectrum_params()
            if attr_name in ['bandwidth_value', 'symbol_rate_value']:
                self.update_spectral_efficiency()
        
        slider.valueChanged.connect(update_value)
        container.addWidget(slider)
        
        container.addSpacing(8)
        
        return container
    
    def update_power_spectrum_params(self):
        if hasattr(self, 'power_spectrum'):
            self.power_spectrum.set_parameters(
                self.symbol_rate_value,
                self.signal_power_value,
                self.bandwidth_value
            )
    
    def create_slider_control_with_callback(self, label, value, unit, min_val, max_val, callback):
        container = QVBoxLayout()
        container.setSpacing(8)
        
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        label_widget = QLabel(label)
        value_label = QLabel(f"{value} {unit}")
        value_label.setProperty("class", "stat-value")
        value_label.setMinimumHeight(24)
        header.addWidget(label_widget)
        header.addStretch()
        header.addWidget(value_label)
        container.addLayout(header)
        
        container.addSpacing(4)
        
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(min_val)
        slider.setMaximum(max_val)
        slider.setValue(value)
        slider.valueChanged.connect(lambda v, lbl=value_label, u=unit: lbl.setText(f"{v} {u}"))
        slider.valueChanged.connect(callback)
        container.addWidget(slider)
        
        container.addSpacing(8)
        
        return container
    
    def update_power_spectrum(self, value):
        if hasattr(self, 'power_spectrum'):
            self.power_spectrum.update()
    
    def create_right_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)
        
        const_card = QFrame()
        const_card.setObjectName("card")
        const_layout = QVBoxLayout(const_card)
        const_layout.setContentsMargins(24, 24, 24, 24)
        const_layout.setSpacing(0)
        
        const_header = QHBoxLayout()
        const_title_layout = QVBoxLayout()
        const_title = QLabel("Constellation Diagram")
        const_title.setProperty("class", "card-title")
        const_subtitle = QLabel("I/Q symbol mapping for QPSK")
        const_subtitle.setProperty("class", "section-subtitle")
        const_title_layout.addWidget(const_title)
        const_title_layout.addWidget(const_subtitle)
        const_title_layout.setSpacing(2)
        
        symbols_label = QLabel("4 Symbols")
        symbols_label.setProperty("class", "stat-value")
        
        const_header.addLayout(const_title_layout)
        const_header.addStretch()
        const_header.addWidget(symbols_label)
        const_layout.addLayout(const_header)
        
        self.constellation = ConstellationWidget()
        const_layout.addWidget(self.constellation, 0, Qt.AlignTop)
        
        stats_layout = QGridLayout()
        stats_layout.setSpacing(10)
        stats_layout.setContentsMargins(100, 0, 10, 0)
        
        self.bits_per_symbol_label = QLabel("2.0")
        self.bits_per_symbol_label.setProperty("class", "stat-value")
        self.symbol_count_label = QLabel("4")
        self.symbol_count_label.setProperty("class", "stat-value")
        self.spectral_efficiency_label = QLabel("1.00 bps/Hz")
        self.spectral_efficiency_label.setProperty("class", "stat-value")
        
        stats = [
            ("Bits per Symbol", self.bits_per_symbol_label),
            ("Symbol Count", self.symbol_count_label),
            ("Spectral Efficiency", self.spectral_efficiency_label)
        ]
        
        for i, (label_text, value_label) in enumerate(stats):
            stat_container = QVBoxLayout()
            stat_label = QLabel(label_text)
            stat_label.setProperty("class", "stat-label")
            stat_container.addWidget(value_label)
            stat_container.addWidget(stat_label)
            stats_layout.addLayout(stat_container, 0, i)
        
        const_layout.addLayout(stats_layout)
        
        layout.addWidget(const_card)
        
        psd_card = QFrame()
        psd_card.setObjectName("card")
        psd_layout = QVBoxLayout(psd_card)
        psd_layout.setContentsMargins(24, 24, 24, 24)
        psd_layout.setSpacing(16)
        
        psd_header = QHBoxLayout()
        psd_title_layout = QVBoxLayout()
        psd_title = QLabel("📊 Power Spectral Density")
        psd_title.setProperty("class", "card-title")
        psd_subtitle = QLabel("Frequency domain representation")
        psd_subtitle.setProperty("class", "section-subtitle")
        psd_title_layout.addWidget(psd_title)
        psd_title_layout.addWidget(psd_subtitle)
        psd_title_layout.setSpacing(2)
        
        freq_label = QLabel("2400 MHz ± 10 MHz")
        freq_label.setProperty("class", "stat-value")
        
        psd_header.addLayout(psd_title_layout)
        psd_header.addStretch()
        psd_header.addWidget(freq_label)
        psd_layout.addLayout(psd_header)
        
        self.power_spectrum = PowerSpectrumWidget()
        psd_layout.addWidget(self.power_spectrum)
        
        psd_stats_layout = QGridLayout()
        psd_stats_layout.setSpacing(20)
        
        psd_stats = [
            ("Center Frequency", "2400 MHz"),
            ("Occupied BW", "20 MHz"),
            ("Data Rate", "20.0 Mbps"),
            ("Sample Rate", "80.0 Msps")
        ]
        
        for i, (label, value) in enumerate(psd_stats):
            stat_container = QVBoxLayout()
            stat_label = QLabel(label)
            stat_label.setProperty("class", "stat-label")
            stat_value = QLabel(value)
            stat_value.setProperty("class", "stat-value")
            stat_container.addWidget(stat_label)
            stat_container.addWidget(stat_value)
            psd_stats_layout.addLayout(stat_container, 0, i)
        
        psd_layout.addLayout(psd_stats_layout)
        
        layout.addWidget(psd_card)
        
        return panel


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    window = SignalDashboard()
    window.show()
    sys.exit(app.exec())