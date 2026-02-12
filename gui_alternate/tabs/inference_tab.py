from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QComboBox, QGridLayout, QFrame, QFileDialog, QTabWidget)
from PySide6.QtCore import Qt
import os
import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from sklearn.metrics import confusion_matrix, classification_report, roc_curve, auc, roc_auc_score
import torch

_DARK_BG = '#1e1e32'
_DARK_AXES = '#2d2d44'
_DARK_TEXT = '#e0e0e0'
_DARK_GRID = '#404060'


def _apply_dark_style(fig):
    """Apply dark theme colors to a matplotlib figure."""
    fig.patch.set_facecolor(_DARK_BG)
    for ax in fig.axes:
        ax.set_facecolor(_DARK_AXES)
        ax.tick_params(colors=_DARK_TEXT)
        ax.xaxis.label.set_color(_DARK_TEXT)
        ax.yaxis.label.set_color(_DARK_TEXT)
        ax.title.set_color(_DARK_TEXT)
        for spine in ax.spines.values():
            spine.set_color(_DARK_GRID)
        legend = ax.get_legend()
        if legend is not None:
            legend.get_frame().set_facecolor(_DARK_AXES)
            legend.get_frame().set_edgecolor(_DARK_GRID)
            for text in legend.get_texts():
                text.set_color(_DARK_TEXT)


# Models that expect 2-channel IQ input (must stay in sync with trainer.py)
IQ_MODELS = {'ResNet1DOptimized'}


class InferenceResultsTab(QWidget):
    """Model inference and evaluation tab"""
    
    def __init__(self):
        super().__init__()
        self.model = None
        self.model_path = None
        self.model_metadata = None  # loaded from companion .json
        self.eval_data = None
        self.eval_labels = None
        self.class_labels = []  # human-readable class names
        self.setup_ui()
    
    def setup_ui(self):
        """Initialize the UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header
        title = QLabel("📊 Model Evaluation")
        title.setProperty("class", "section-title")
        subtitle = QLabel("Load a trained model and evaluate on test data")
        subtitle.setProperty("class", "section-subtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)
        
        # Control panel
        control_layout = QHBoxLayout()
        
        self.load_model_btn = QPushButton("Load Model (.pth)")
        self.load_model_btn.clicked.connect(self.load_model)
        control_layout.addWidget(self.load_model_btn)
        
        self.model_label = QLabel("No model loaded")
        self.model_label.setProperty("class", "stat-label")
        control_layout.addWidget(self.model_label)
        
        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        # Data panel
        data_layout = QHBoxLayout()
        
        self.load_data_btn = QPushButton("Load Test Data Folder")
        self.load_data_btn.clicked.connect(self.load_test_data)
        self.load_data_btn.setEnabled(False)
        data_layout.addWidget(self.load_data_btn)
        
        self.quick_load_test_btn = QPushButton("📦 Quick Load Test Data")
        self.quick_load_test_btn.setToolTip("Load class folders from waveform_data/ for evaluation")
        self.quick_load_test_btn.clicked.connect(self.quick_load_test_data)
        self.quick_load_test_btn.setEnabled(False)
        data_layout.addWidget(self.quick_load_test_btn)
        
        self.data_label = QLabel("No test data loaded")
        self.data_label.setProperty("class", "stat-label")
        data_layout.addWidget(self.data_label)
        
        data_layout.addStretch()
        layout.addLayout(data_layout)
        
        # Evaluation tabs
        self.eval_tabs = QTabWidget()
        
        # Confusion Matrix tab
        cm_widget = self.create_confusion_matrix_widget()
        self.eval_tabs.addTab(cm_widget, "Confusion Matrix")
        
        # Classification Report tab
        report_widget = self.create_report_widget()
        self.eval_tabs.addTab(report_widget, "Classification Report")
        
        # ROC Curve tab
        roc_widget = self.create_roc_widget()
        self.eval_tabs.addTab(roc_widget, "ROC Curve")
        
        self.eval_tabs.setEnabled(False)
        layout.addWidget(self.eval_tabs)
    
    def create_confusion_matrix_widget(self):
        """Create confusion matrix visualization widget"""
        widget = QFrame()
        widget.setObjectName("card")
        layout = QVBoxLayout(widget)
        
        self.cm_figure = Figure(figsize=(6, 5), dpi=100, facecolor=_DARK_BG)
        self.cm_canvas = FigureCanvas(self.cm_figure)
        layout.addWidget(self.cm_canvas)
        
        eval_btn_layout = QHBoxLayout()
        self.eval_cm_btn = QPushButton("Evaluate Confusion Matrix")
        self.eval_cm_btn.clicked.connect(self.evaluate_confusion_matrix)
        self.eval_cm_btn.setEnabled(False)
        eval_btn_layout.addWidget(self.eval_cm_btn)
        eval_btn_layout.addStretch()
        layout.addLayout(eval_btn_layout)
        
        return widget
    
    def create_report_widget(self):
        """Create classification report widget"""
        widget = QFrame()
        widget.setObjectName("card")
        layout = QVBoxLayout(widget)
        
        self.report_label = QLabel("Run evaluation to see classification report")
        self.report_label.setProperty("class", "stat-label")
        self.report_label.setWordWrap(True)
        layout.addWidget(self.report_label)
        
        eval_btn_layout = QHBoxLayout()
        self.eval_report_btn = QPushButton("Generate Report")
        self.eval_report_btn.clicked.connect(self.evaluate_report)
        self.eval_report_btn.setEnabled(False)
        eval_btn_layout.addWidget(self.eval_report_btn)
        eval_btn_layout.addStretch()
        layout.addLayout(eval_btn_layout)
        
        return widget
    
    def create_roc_widget(self):
        """Create ROC curve visualization widget"""
        widget = QFrame()
        widget.setObjectName("card")
        layout = QVBoxLayout(widget)
        
        self.roc_figure = Figure(figsize=(6, 5), dpi=100, facecolor=_DARK_BG)
        self.roc_canvas = FigureCanvas(self.roc_figure)
        layout.addWidget(self.roc_canvas)
        
        eval_btn_layout = QHBoxLayout()
        self.eval_roc_btn = QPushButton("Evaluate ROC Curve")
        self.eval_roc_btn.clicked.connect(self.evaluate_roc)
        self.eval_roc_btn.setEnabled(False)
        eval_btn_layout.addWidget(self.eval_roc_btn)
        eval_btn_layout.addStretch()
        layout.addLayout(eval_btn_layout)
        
        return widget

    # ------------------------------------------------------------------
    # Model loading — now metadata-aware
    # ------------------------------------------------------------------

    def _load_metadata(self, pth_path):
        """Try to load companion .json metadata for a .pth model file."""
        meta_path = pth_path.rsplit('.', 1)[0] + '.json'
        if os.path.isfile(meta_path):
            try:
                with open(meta_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: could not read metadata {meta_path}: {e}")
        return None

    def load_model(self):
        """Load a trained PyTorch model, auto-detecting architecture from metadata."""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Select Model File", os.path.join(os.getcwd(), 'models'),
            "PyTorch Models (*.pth);;All Files (*)"
        )
        if not filepath:
            return
        self._do_load_model(filepath)

    def receive_trained_model(self, model_path, labels):
        """Slot connected from MLTrainingTab.trained_model_ready signal."""
        self.class_labels = list(labels) if labels else []
        self._do_load_model(model_path)

    def _do_load_model(self, filepath):
        """Internal: load model from filepath, using metadata if available."""
        try:
            from backend.torch_models import get_model

            meta = self._load_metadata(filepath)
            self.model_metadata = meta

            if meta:
                model_name = meta.get('model_name', 'SimpleCNN')
                num_classes = meta.get('num_classes', 2)
                signal_length = meta.get('signal_length', 256)
                if meta.get('class_labels'):
                    self.class_labels = meta['class_labels']
            else:
                model_name = 'SimpleCNN'
                num_classes = 2
                signal_length = 256

            state_dict = torch.load(filepath, map_location='cpu', weights_only=True)
            model = get_model(model_name, num_classes=num_classes, input_size=signal_length)
            model.load_state_dict(state_dict)
            model.eval()

            self.model = model
            self.model_path = filepath

            info = f"Loaded: {os.path.basename(filepath)} ({model_name}, {num_classes} classes)"
            self.model_label.setText(info)
            self.load_data_btn.setEnabled(True)
            self.quick_load_test_btn.setEnabled(True)
        except Exception as e:
            self.model_label.setText(f"Failed to load: {e}")
            print(f"Error loading model: {e}")

    # ------------------------------------------------------------------
    # Test data loading — now supports class-folder structure
    # ------------------------------------------------------------------

    def load_test_data(self):
        """Load test data from a folder.
        
        If the folder contains subfolders, each subfolder is treated as a class
        (same structure as training data).  Otherwise flat files are loaded.
        """
        folder = QFileDialog.getExistingDirectory(self, "Select Test Data Folder",
                                                   os.path.join(os.getcwd(), 'waveform_data'))
        if not folder:
            return
        self._load_data_from_dir(folder)

    def quick_load_test_data(self):
        """Load test data from waveform_data/ directory (same as training Quick Load)."""
        waveform_dir = os.path.join(os.getcwd(), 'waveform_data')
        if not os.path.isdir(waveform_dir):
            self.data_label.setText("No waveform_data/ directory found")
            return
        self._load_data_from_dir(waveform_dir)

    def _load_data_from_dir(self, folder):
        """Load test data from *folder*.  Auto-detect class-folder vs flat layout."""
        try:
            subdirs = [d for d in sorted(os.listdir(folder))
                       if os.path.isdir(os.path.join(folder, d))]

            if subdirs:
                # class-folder layout
                X_list, y_list = [], []
                class_names = []
                for idx, sub in enumerate(subdirs):
                    sub_path = os.path.join(folder, sub)
                    files = self._gather_files(sub_path)
                    for fp in files:
                        arr = self._load_array(fp)
                        if arr is not None:
                            X_list.append(np.asarray(arr).ravel())
                            y_list.append(idx)
                    class_names.append(sub)
                if not self.class_labels:
                    self.class_labels = class_names
            else:
                # flat files
                files = self._gather_files(folder)
                X_list, y_list = [], []
                for i, fp in enumerate(files):
                    arr = self._load_array(fp)
                    if arr is not None:
                        X_list.append(np.asarray(arr).ravel())
                        y_list.append(i % max(len(self.class_labels), 2))

            if not X_list:
                self.data_label.setText("Failed to load any files")
                return

            max_len = max(a.size for a in X_list)
            X = np.zeros((len(X_list), max_len), dtype=np.float32)
            for i, a in enumerate(X_list):
                L = min(len(a), max_len)
                X[i, :L] = a[:L]

            # Determine input shape from metadata
            is_iq = (self.model_metadata or {}).get('model_name', '') in IQ_MODELS
            if is_iq:
                X = self._prepare_iq_data(X)
                X = self._normalize_iq(X)
            else:
                X = X[:, np.newaxis, :]

            self.eval_data = torch.from_numpy(X)
            self.eval_labels = np.asarray(y_list, dtype=np.int64)

            self.data_label.setText(f"Loaded {len(X_list)} samples ({len(set(y_list))} classes)")
            self.eval_cm_btn.setEnabled(True)
            self.eval_report_btn.setEnabled(True)
            self.eval_roc_btn.setEnabled(True)
            self.eval_tabs.setEnabled(True)
        except Exception as e:
            self.data_label.setText(f"Error loading data: {e}")
            print(f"Error: {e}")

    # ------------------------------------------------------------------
    # IQ helpers (mirrored from trainer.py)
    # ------------------------------------------------------------------

    @staticmethod
    def _prepare_iq_data(X_flat):
        if np.iscomplexobj(X_flat):
            return np.stack([X_flat.real, X_flat.imag], axis=1)
        L = X_flat.shape[1]
        if L % 2 != 0:
            X_flat = X_flat[:, :L - 1]
            L -= 1
        return np.stack([X_flat[:, 0::2], X_flat[:, 1::2]], axis=1)

    @staticmethod
    def _normalize_iq(X_iq):
        power = np.mean(X_iq[:, 0, :] ** 2 + X_iq[:, 1, :] ** 2, axis=1, keepdims=True)
        power = np.maximum(power, 1e-10)
        scale = np.sqrt(power)[:, np.newaxis, :]
        return X_iq / scale

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _gather_files(folder):
        exts = ('.npy', '.npz', '.csv')
        files = []
        for entry in sorted(os.listdir(folder)):
            path = os.path.join(folder, entry)
            if os.path.isfile(path) and entry.lower().endswith(exts):
                files.append(path)
        return files

    @staticmethod
    def _load_array(path):
        try:
            if path.lower().endswith(('.npy', '.npz')):
                arr = np.load(path, allow_pickle=True)
                if isinstance(arr, np.lib.npyio.NpzFile):
                    keys = list(arr.keys())
                    arr = arr[keys[0]] if keys else None
                return np.asarray(arr, dtype=np.float32)
            if path.lower().endswith('.csv'):
                return np.loadtxt(path, delimiter=',').astype(np.float32)
        except Exception as e:
            print(f"Failed to load {path}: {e}")
        return None

    # ------------------------------------------------------------------
    # Evaluation methods
    # ------------------------------------------------------------------

    def evaluate_confusion_matrix(self):
        """Compute and display confusion matrix"""
        if self.model is None or self.eval_data is None:
            return
        
        try:
            with torch.no_grad():
                outputs = self.model(self.eval_data)
                _, predictions = outputs.max(1)
            
            y_pred = predictions.cpu().numpy()
            labels_list = self.class_labels if self.class_labels else None
            cm = confusion_matrix(self.eval_labels, y_pred)
            
            self.cm_figure.clear()
            ax = self.cm_figure.add_subplot(111)
            im = ax.imshow(cm, cmap='Blues', interpolation='nearest')
            ax.set_xlabel('Predicted')
            ax.set_ylabel('True')
            ax.set_title('Confusion Matrix')

            if labels_list:
                ax.set_xticks(range(len(labels_list)))
                ax.set_xticklabels(labels_list, rotation=45, ha='right')
                ax.set_yticks(range(len(labels_list)))
                ax.set_yticklabels(labels_list)
            
            # Add text annotations
            for i in range(cm.shape[0]):
                for j in range(cm.shape[1]):
                    ax.text(j, i, str(cm[i, j]), ha='center', va='center', color='white')
            
            self.cm_figure.colorbar(im, ax=ax)
            self.cm_figure.tight_layout()
            _apply_dark_style(self.cm_figure)
            self.cm_canvas.draw()
        except Exception as e:
            print(f"Error computing confusion matrix: {e}")
    
    def evaluate_report(self):
        """Compute and display classification report"""
        if self.model is None or self.eval_data is None:
            return
        
        try:
            with torch.no_grad():
                outputs = self.model(self.eval_data)
                _, predictions = outputs.max(1)
            
            y_pred = predictions.cpu().numpy()
            target_names = self.class_labels if self.class_labels else None
            report = classification_report(self.eval_labels, y_pred,
                                           target_names=target_names, zero_division=0)
            accuracy = (y_pred == self.eval_labels).mean()
            
            text = f"Accuracy: {accuracy:.4f}\n\n{report}"
            self.report_label.setText(text)
        except Exception as e:
            self.report_label.setText(f"Error: {e}")
            print(f"Error: {e}")
    
    def evaluate_roc(self):
        """Compute and display ROC curve (binary classification only)"""
        if self.model is None or self.eval_data is None:
            return
        
        try:
            with torch.no_grad():
                outputs = self.model(self.eval_data)
                # Get probabilities for class 1
                if outputs.shape[1] == 2:
                    probs = torch.nn.functional.softmax(outputs, dim=1)[:, 1].cpu().numpy()
                else:
                    probs = outputs[:, 0].cpu().numpy()
            
            fpr, tpr, _ = roc_curve(self.eval_labels, probs)
            roc_auc = auc(fpr, tpr)
            
            self.roc_figure.clear()
            ax = self.roc_figure.add_subplot(111)
            ax.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (AUC = {roc_auc:.2f})')
            ax.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--', label='Random')
            ax.set_xlim([0.0, 1.0])
            ax.set_ylim([0.0, 1.05])
            ax.set_xlabel('False Positive Rate')
            ax.set_ylabel('True Positive Rate')
            ax.set_title('ROC Curve')
            ax.legend(loc="lower right")

            _apply_dark_style(self.roc_figure)
            self.roc_canvas.draw()
        except Exception as e:
            print(f"Error computing ROC curve: {e}")