def get_stylesheet(dark_mode=False):

    if dark_mode:
        return """
            * {
                font-size: 13px;
            }
            QMainWindow {
                background-color: #1a1a2e;
            }
            QWidget#mainContent {
                background-color: #1a1a2e;
            }
            QWidget {
                background-color: transparent;
                color: #e0e0e0;
                font-size: 13px;
            }
            QLabel {
                color: #e0e0e0;
                font-size: 13px;
            }
            QLabel.field-label {
                font-size: 11px;
                color: #9ca3af;
                font-weight: 500;
                padding-bottom: 0px;
                margin-bottom: 0px;
            }
            .title {
                font-size: 18px;
                font-weight: bold;
                color: #ffffff;
            }
            .subtitle {
                font-size: 12px;
                color: #9ca3af;
            }
            .section-title {
                font-size: 16px;
                font-weight: 600;
                color: #ffffff;
            }
            .section-subtitle {
                font-size: 12px;
                color: #9ca3af;
            }
            .card-title {
                font-size: 15px;
                font-weight: 600;
                color: #ffffff;
            }
            .stat-value {
                font-size: 20px;
                font-weight: 600;
                color: #ffffff;
            }
            .stat-label {
                font-size: 12px;
                color: #9ca3af;
            }
            QPushButton {
                background-color: #2d2d44;
                border: 1px solid #404060;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 500;
                color: #e0e0e0;
            }
            QPushButton:hover {
                background-color: #3d3d5c;
                border-color: #6366f1;
            }
            QPushButton#primaryButton {
                background-color: #6366f1;
                color: white;
                border: none;
                font-size: 13px;
                font-weight: 600;
                padding: 10px 20px;
            }
            QPushButton#primaryButton:hover {
                background-color: #818cf8;
            }
            QPushButton#tabButton {
                background-color: transparent;
                border: none;
                border-bottom: 2px solid transparent;
                border-radius: 0px;
                padding: 10px 16px;
                font-size: 13px;
                font-weight: 500;
                color: #9ca3af;
            }
            QPushButton#tabButton:checked {
                border-bottom: 2px solid #6366f1;
                color: #ffffff;
            }
            QComboBox {
                background-color: #2d2d44;
                border: 1px solid #404060;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 13px;
                color: #e0e0e0;
                min-height: 22px;
            }
            QComboBox:hover, QComboBox:focus {
                border-color: #6366f1;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 28px;
                border-left: 1px solid #404060;
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
                background-color: #353550;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #c0c0d0;
            }
            QComboBox QAbstractItemView {
                background-color: #2d2d44;
                border: 1px solid #404060;
                selection-background-color: #6366f1;
                selection-color: #ffffff;
                color: #e0e0e0;
                padding: 4px;
                font-size: 13px;
            }
            QComboBox QAbstractItemView::item {
                padding: 6px 10px;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #6366f1;
                color: #ffffff;
            }
            QMenu, QListView {
                background-color: #2d2d44;
                border: 1px solid #404060;
                color: #e0e0e0;
                font-size: 13px;
            }
            QMenu::item, QListView::item {
                padding: 6px 12px;
                color: #e0e0e0;
            }
            QMenu::item:selected, QListView::item:selected {
                background-color: #6366f1;
                color: #ffffff;
            }
            QListWidget {
                background-color: #2d2d44;
                border: 1px solid #404060;
                border-radius: 6px;
                color: #e0e0e0;
            }
            QListWidget::item {
                padding: 6px 10px;
                color: #e0e0e0;
            }
            QListWidget::item:selected {
                background-color: #6366f1;
                color: #ffffff;
            }
            QDoubleSpinBox, QSpinBox {
                background-color: #2d2d44;
                border: 1px solid #404060;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
                color: #e0e0e0;
                min-height: 22px;
            }
            QDoubleSpinBox:hover, QSpinBox:hover,
            QDoubleSpinBox:focus, QSpinBox:focus {
                border-color: #6366f1;
            }
            QDoubleSpinBox::up-button, QSpinBox::up-button {
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 24px;
                border-left: 1px solid #404060;
                border-bottom: 1px solid #404060;
                border-top-right-radius: 6px;
                background-color: #353550;
            }
            QDoubleSpinBox::up-button:hover, QSpinBox::up-button:hover {
                background-color: #4d4d6a;
            }
            QDoubleSpinBox::down-button, QSpinBox::down-button {
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 24px;
                border-left: 1px solid #404060;
                border-top: 1px solid #404060;
                border-bottom-right-radius: 6px;
                background-color: #353550;
            }
            QDoubleSpinBox::down-button:hover, QSpinBox::down-button:hover {
                background-color: #4d4d6a;
            }
            QDoubleSpinBox::up-arrow, QSpinBox::up-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-bottom: 6px solid #c0c0d0;
                width: 0px;
                height: 0px;
            }
            QDoubleSpinBox::up-arrow:hover, QSpinBox::up-arrow:hover {
                border-bottom-color: #ffffff;
            }
            QDoubleSpinBox::down-arrow, QSpinBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #c0c0d0;
                width: 0px;
                height: 0px;
            }
            QDoubleSpinBox::down-arrow:hover, QSpinBox::down-arrow:hover {
                border-top-color: #ffffff;
            }
            QSlider::groove:horizontal {
                border: none;
                height: 6px;
                background: #404060;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #6366f1;
                border: none;
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
            QFrame#card {
                background-color: #2d2d44;
                border-radius: 12px;
                border: 1px solid #404060;
            }
            QScrollArea#card {
                background-color: #2d2d44;
                border-radius: 12px;
                border: 1px solid #404060;
            }
            QScrollArea#card::viewport {
                background-color: #2d2d44;
                border: none;
            }
            QGroupBox {
                background-color: #2d2d44;
                border: 1px solid #404060;
                border-radius: 6px;
                margin-top: 10px;
                padding: 8px;
                color: #e0e0e0;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
                color: #c0c0d0;
            }
            QFrame#infoBox {
                background-color: #1e1e3a;
                border: 1px solid #404060;
                border-radius: 8px;
                padding: 12px;
            }
            QCheckBox {
                spacing: 8px;
                font-size: 13px;
                color: #e0e0e0;
            }
            QCheckBox::indicator {
                width: 40px;
                height: 20px;
                border-radius: 10px;
                background-color: #404060;
            }
            QCheckBox::indicator:checked {
                background-color: #6366f1;
            }
            QTableWidget {
                background-color: #2d2d44;
                border: none;
                gridline-color: transparent;
                font-size: 13px;
                color: #e0e0e0;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #404060;
                border-right: none;
                color: #e0e0e0;
            }
            QHeaderView::section {
                background-color: #2d2d44;
                padding: 10px 8px;
                border: none;
                border-bottom: 1px solid #404060;
                font-weight: 600;
                font-size: 12px;
                color: #9ca3af;
            }
            .badge {
                border-radius: 12px;
                padding: 6px 14px;
                font-size: 13px;
                font-weight: 600;
            }
            .badge-black {
                background-color: #6366f1;
                color: white;
            }
            .badge-red {
                background-color: #ef4444;
                color: white;
            }
            QProgressBar {
                border: none;
                border-radius: 4px;
                background-color: #404060;
                height: 8px;
            }
            QProgressBar::chunk {
                background-color: #6366f1;
                border-radius: 4px;
            }
            QTabBar::tab {
                background: #2d2d44;
                color: #9ca3af;
                padding: 8px 16px;
                font-size: 13px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                border: 1px solid #404060;
                border-bottom: none;
            }
            QTabBar::tab:selected {
                background: #3d3d5c;
                color: #ffffff;
                border-bottom: 2px solid #6366f1;
            }
            QTabBar::tab:hover {
                background: #3d3d5c;
                color: #e0e0e0;
            }
            QTabWidget::pane {
                border: 1px solid #404060;
                background-color: #2d2d44;
                top: -1px;
            }
            QLineEdit {
                background-color: #2d2d44;
                border: 1px solid #404060;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 13px;
                color: #e0e0e0;
            }
            QLineEdit:focus {
                border-color: #6366f1;
            }
            QScrollBar:vertical {
                background: #1a1a2e;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #404060;
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #6366f1;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar:horizontal {
                background: #1a1a2e;
                height: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:horizontal {
                background: #404060;
                border-radius: 5px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #6366f1;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
            NavigationToolbar2QT {
                background-color: #2d2d44;
                border: none;
            }
            NavigationToolbar2QT QToolButton {
                background-color: transparent;
                border: none;
                padding: 4px;
                border-radius: 4px;
            }
            NavigationToolbar2QT QToolButton:hover {
                background-color: #404060;
            }
            QPushButton#themeToggle {
                background-color: transparent;
                border: 1px solid #404060;
                border-radius: 14px;
                padding: 5px 14px;
                font-size: 12px;
                color: #9ca3af;
            }
            QPushButton#themeToggle:hover {
                border-color: #6366f1;
                color: #e0e0e0;
                background-color: #2d2d44;
            }
        """
    else:
        return """
            * {
                font-size: 13px;
            }
            QMainWindow {
                background-color: #f5f5f5;
            }
            QLabel {
                color: #1f2937;
                font-size: 13px;
            }
            QLabel.field-label {
                font-size: 11px;
                color: #6b7280;
                font-weight: 500;
            }
            .title {
                font-size: 18px;
                font-weight: bold;
                color: #111827;
            }
            .subtitle {
                font-size: 12px;
                color: #6b7280;
            }
            .section-title {
                font-size: 16px;
                font-weight: 600;
                color: #111827;
            }
            .section-subtitle {
                font-size: 12px;
                color: #6b7280;
            }
            .card-title {
                font-size: 15px;
                font-weight: 600;
                color: #111827;
            }
            .stat-value {
                font-size: 20px;
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
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 500;
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
                font-size: 13px;
                font-weight: 600;
                padding: 10px 20px;
            }
            QPushButton#primaryButton:hover {
                background-color: #1f2937;
            }
            QPushButton#tabButton {
                background-color: white;
                border: none;
                border-bottom: 2px solid transparent;
                border-radius: 0px;
                padding: 10px 16px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton#tabButton:checked {
                border-bottom: 2px solid #111827;
                color: #111827;
            }
            QComboBox {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 13px;
                color: #111827;
                min-height: 22px;
            }
            QComboBox:hover, QComboBox:focus {
                border-color: #111827;
                background-color: #ffffff;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 28px;
                border-left: 1px solid #cbd5e1;
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
                background-color: #f3f4f6;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #6b7280;
            }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                selection-background-color: #111827;
                selection-color: #ffffff;
                color: #111827;
                padding: 4px;
                font-size: 13px;
            }
            QComboBox QAbstractItemView::item {
                padding: 6px 10px;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #111827;
                color: #ffffff;
            }
            QMenu, QListView {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                color: #111827;
                font-size: 13px;
            }
            QMenu::item, QListView::item {
                padding: 6px 12px;
                color: #111827;
            }
            QMenu::item:selected, QListView::item:selected {
                background-color: #111827;
                color: #ffffff;
            }
            QDoubleSpinBox, QSpinBox {
                background-color: white;
                border: 1px solid #e5e7eb;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
                color: #1f2937;
                min-height: 22px;
            }
            QDoubleSpinBox:hover, QSpinBox:hover,
            QDoubleSpinBox:focus, QSpinBox:focus {
                border-color: #111827;
            }
            QDoubleSpinBox::up-button, QSpinBox::up-button {
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 24px;
                border-left: 1px solid #e5e7eb;
                border-bottom: 1px solid #e5e7eb;
                border-top-right-radius: 6px;
                background-color: #f3f4f6;
            }
            QDoubleSpinBox::up-button:hover, QSpinBox::up-button:hover {
                background-color: #e5e7eb;
            }
            QDoubleSpinBox::down-button, QSpinBox::down-button {
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 24px;
                border-left: 1px solid #e5e7eb;
                border-top: 1px solid #e5e7eb;
                border-bottom-right-radius: 6px;
                background-color: #f3f4f6;
            }
            QDoubleSpinBox::down-button:hover, QSpinBox::down-button:hover {
                background-color: #e5e7eb;
            }
            QDoubleSpinBox::up-arrow, QSpinBox::up-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-bottom: 6px solid #6b7280;
                width: 0px;
                height: 0px;
            }
            QDoubleSpinBox::up-arrow:hover, QSpinBox::up-arrow:hover {
                border-bottom-color: #111827;
            }
            QDoubleSpinBox::down-arrow, QSpinBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #6b7280;
                width: 0px;
                height: 0px;
            }
            QDoubleSpinBox::down-arrow:hover, QSpinBox::down-arrow:hover {
                border-top-color: #111827;
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
                padding: 10px 8px;
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
            QProgressBar {
                border: none;
                border-radius: 4px;
                background-color: #e5e7eb;
                height: 8px;
            }
            QProgressBar::chunk {
                background-color: #111827;
                border-radius: 4px;
            }
            QTabBar::tab {
                background: #f0f0f0;
                color: #6b7280;
                padding: 8px 16px;
                font-size: 13px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #ffffff;
                color: #111827;
            }
            QTabWidget::pane {
                border: 1px solid #e5e7eb;
                top: -1px;
            }
            QPushButton#themeToggle {
                background-color: transparent;
                border: 1px solid #d1d5db;
                border-radius: 14px;
                padding: 5px 14px;
                font-size: 12px;
                color: #6b7280;
            }
            QPushButton#themeToggle:hover {
                border-color: #111827;
                color: #111827;
                background-color: #f3f4f6;
            }
        """
