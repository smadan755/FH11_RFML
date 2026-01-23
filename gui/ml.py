"""
ML Training Widget for Modulation Classification
Integrates CWT-based ResNet18 classifier training from Spectrum-Scrapers project
"""

from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, QThread, Signal
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torchvision import models
from pathlib import Path
from scipy.ndimage import zoom
import matlab.engine
from tqdm import tqdm


# ============================================
# Dataset Generation Thread
# ============================================
class DatasetGeneratorThread(QThread):
    """Background thread for generating CWT dataset"""
    progress = Signal(str)  # Progress message
    finished = Signal(np.ndarray, np.ndarray)  # images, labels
    error = Signal(str)

    def __init__(self, config, modulation_types):
        super().__init__()
        self.config = config
        self.modulation_types = modulation_types

    def run(self):
        try:
            self.progress.emit("Starting MATLAB engine...")
            eng = matlab.engine.start_matlab()

            images = []
            labels = []

            total_samples = len(self.modulation_types) * self.config['num_samples_per_class']
            current = 0

            for label_idx, mod_type in enumerate(self.modulation_types):
                self.progress.emit(f"Generating {mod_type} samples...")

                for i in range(self.config['num_samples_per_class']):
                    # Random SNR
                    snr = np.random.uniform(*self.config['snr_range'])

                    # Generate signal in MATLAB
                    self._generate_matlab_signal(eng, mod_type, snr)

                    # Compute CWT
                    cwt_matrix = self._compute_cwt(eng)

                    # Resize to target size
                    cwt_resized = zoom(cwt_matrix, (
                        self.config['image_size'][0] / cwt_matrix.shape[0],
                        self.config['image_size'][1] / cwt_matrix.shape[1]
                    ))

                    images.append(cwt_resized)
                    labels.append(label_idx)

                    current += 1
                    if current % 10 == 0:
                        self.progress.emit(f"Generated {current}/{total_samples} samples...")

            eng.quit()

            images = np.array(images, dtype=np.float32)
            labels = np.array(labels, dtype=np.int64)

            self.finished.emit(images, labels)

        except Exception as e:
            self.error.emit(f"Error generating dataset: {str(e)}")

    def _generate_matlab_signal(self, eng, mod_type, snr, num_symbols=1000):
        """Generate modulated signal in MATLAB workspace"""
        if mod_type == 'BPSK':
            eng.eval(f"data = randi([0 1], {num_symbols}, 1);", nargout=0)
            eng.eval("tx = pskmod(data, 2);", nargout=0)
        elif mod_type == 'QPSK':
            eng.eval(f"data = randi([0 3], {num_symbols}, 1);", nargout=0)
            eng.eval("tx = pskmod(data, 4, pi/4);", nargout=0)
        elif mod_type == '8PSK':
            eng.eval(f"data = randi([0 7], {num_symbols}, 1);", nargout=0)
            eng.eval("tx = pskmod(data, 8);", nargout=0)
        elif mod_type == '16QAM':
            eng.eval(f"data = randi([0 15], {num_symbols}, 1);", nargout=0)
            eng.eval("tx = qammod(data, 16, 'UnitAveragePower', true);", nargout=0)
        elif mod_type == '64QAM':
            eng.eval(f"data = randi([0 63], {num_symbols}, 1);", nargout=0)
            eng.eval("tx = qammod(data, 64, 'UnitAveragePower', true);", nargout=0)
        elif mod_type == '4FSK':
            eng.eval("M = 4; nsamp = 16; freq_sep = 50; Fs_fsk = 1000;", nargout=0)
            eng.eval(f"data = randi([0 M-1], {num_symbols//16}, 1);", nargout=0)
            eng.eval("tx = fskmod(data, M, freq_sep, nsamp, Fs_fsk);", nargout=0)
        elif mod_type == 'OFDM':
            eng.eval("ofdm_mod = comm.OFDMModulator('FFTLength', 64, 'CyclicPrefixLength', 16);", nargout=0)
            eng.eval("ofdm_info = info(ofdm_mod);", nargout=0)
            eng.eval("num_carriers = ofdm_info.DataInputSize(1);", nargout=0)
            eng.eval(f"num_symbols = {num_symbols // 80};", nargout=0)
            eng.eval("tx = [];", nargout=0)
            eng.eval("for k = 1:num_symbols; d = pskmod(randi([0 3], num_carriers, 1), 4, pi/4); tx = [tx; ofdm_mod(d)]; end", nargout=0)

        # Add noise
        eng.eval(f"rx = awgn(tx, {snr}, 'measured');", nargout=0)

    def _compute_cwt(self, eng, fs=1.0):
        """Compute CWT scalogram from MATLAB workspace signal"""
        eng.eval(f"[cfs, frq] = cwt(real(rx), {fs});", nargout=0)
        eng.eval("P = abs(cfs).^2;", nargout=0)
        eng.eval("P = flipud(P);", nargout=0)
        eng.eval("P = (P - min(P(:))) / (max(P(:)) - min(P(:)) + 1e-10);", nargout=0)

        P = np.array(eng.workspace['P'])
        return P


# ============================================
# Training Thread
# ============================================
class TrainingThread(QThread):
    """Background thread for training the model"""
    progress = Signal(str)  # Progress message
    epoch_complete = Signal(int, float, float, float, float)  # epoch, train_loss, train_acc, val_loss, val_acc
    finished = Signal(object)  # trained model
    error = Signal(str)

    def __init__(self, model, train_loader, val_loader, config):
        super().__init__()
        self.model = model
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.config = config
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    def run(self):
        try:
            self.model = self.model.to(self.device)
            criterion = nn.CrossEntropyLoss(label_smoothing=0.1)
            optimizer = optim.AdamW(self.model.parameters(),
                                   lr=self.config['learning_rate'],
                                   weight_decay=self.config['weight_decay'])
            scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=5)

            best_val_loss = float('inf')
            patience_counter = 0

            for epoch in range(self.config['epochs']):
                self.progress.emit(f"Epoch {epoch+1}/{self.config['epochs']}")

                # Training phase
                self.model.train()
                train_loss = 0.0
                train_correct = 0
                train_total = 0

                for inputs, labels in self.train_loader:
                    inputs = inputs.to(self.device)
                    labels = labels.to(self.device)

                    optimizer.zero_grad()
                    outputs = self.model(inputs)
                    _, preds = torch.max(outputs, 1)
                    loss = criterion(outputs, labels)

                    loss.backward()
                    optimizer.step()

                    train_loss += loss.item() * inputs.size(0)
                    train_correct += torch.sum(preds == labels.data)
                    train_total += labels.size(0)

                epoch_train_loss = train_loss / train_total
                epoch_train_acc = train_correct.double() / train_total

                # Validation phase
                self.model.eval()
                val_loss = 0.0
                val_correct = 0
                val_total = 0

                with torch.no_grad():
                    for inputs, labels in self.val_loader:
                        inputs = inputs.to(self.device)
                        labels = labels.to(self.device)

                        outputs = self.model(inputs)
                        _, preds = torch.max(outputs, 1)
                        loss = criterion(outputs, labels)

                        val_loss += loss.item() * inputs.size(0)
                        val_correct += torch.sum(preds == labels.data)
                        val_total += labels.size(0)

                epoch_val_loss = val_loss / val_total
                epoch_val_acc = val_correct.double() / val_total

                # Emit progress
                self.epoch_complete.emit(
                    epoch + 1,
                    epoch_train_loss,
                    epoch_train_acc.item(),
                    epoch_val_loss,
                    epoch_val_acc.item()
                )

                # Early stopping check
                if epoch_val_loss < best_val_loss:
                    best_val_loss = epoch_val_loss
                    patience_counter = 0
                    # Save model
                    torch.save(self.model.state_dict(), self.config['model_save_path'])
                else:
                    patience_counter += 1
                    if patience_counter >= self.config['patience']:
                        self.progress.emit(f"Early stopping triggered at epoch {epoch+1}")
                        break

                scheduler.step(epoch_val_loss)

            # Load best model
            self.model.load_state_dict(torch.load(self.config['model_save_path']))
            self.finished.emit(self.model)

        except Exception as e:
            self.error.emit(f"Training error: {str(e)}")


# ============================================
# PyTorch Dataset
# ============================================
class ModulationDataset(Dataset):
    def __init__(self, images, labels, augment=False):
        self.images = images
        self.labels = labels
        self.augment = augment

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        image = self.images[idx].copy()
        label = self.labels[idx]

        if self.augment:
            # Random horizontal flip
            if np.random.random() > 0.5:
                image = np.fliplr(image).copy()
            # Random time shift
            shift = np.random.randint(-20, 20)
            image = np.roll(image, shift, axis=1)
            # Random noise
            if np.random.random() > 0.5:
                noise = np.random.normal(0, 0.02, image.shape)
                image = image + noise
                image = np.clip(image, 0, 1)

        # Convert to 3-channel RGB
        image = np.stack([image, image, image], axis=0)
        image = torch.tensor(image, dtype=torch.float32)

        return image, label


# ============================================
# Main ML Widget
# ============================================
class MLWidget(QWidget):
    def __init__(self):
        super().__init__()

        # Configuration
        self.config = {
            'num_samples_per_class': 200,  # Start with smaller dataset
            'snr_range': (-5, 20),
            'image_size': (224, 224),
            'batch_size': 16,
            'epochs': 30,
            'learning_rate': 0.0001,
            'weight_decay': 1e-4,
            'train_split': 0.8,
            'patience': 7,
            'model_save_path': 'modulation_classifier.pth'
        }

        self.modulation_types = ['BPSK', 'QPSK', '8PSK', '16QAM', '64QAM', '4FSK', 'OFDM']
        self.images = None
        self.labels = None
        self.model = None

        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)

        # Left panel - controls
        left_panel = self.create_left_panel()
        main_layout.addWidget(left_panel, 1)

        # Right panel - visualization
        right_panel = self.create_right_panel()
        main_layout.addWidget(right_panel, 2)

    def create_left_panel(self):
        panel = QFrame()
        panel.setFrameStyle(QFrame.StyledPanel)
        layout = QVBoxLayout(panel)

        # Title
        title = QLabel("ML Training Configuration")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        # Dataset section
        dataset_group = QGroupBox("Dataset Generation")
        dataset_layout = QVBoxLayout()

        # Samples per class
        samples_layout = QHBoxLayout()
        samples_layout.addWidget(QLabel("Samples per class:"))
        self.samples_spin = QSpinBox()
        self.samples_spin.setRange(10, 2000)
        self.samples_spin.setValue(200)
        samples_layout.addWidget(self.samples_spin)
        dataset_layout.addLayout(samples_layout)

        # SNR range
        snr_layout = QHBoxLayout()
        snr_layout.addWidget(QLabel("SNR Range (dB):"))
        self.snr_min_spin = QSpinBox()
        self.snr_min_spin.setRange(-20, 20)
        self.snr_min_spin.setValue(-5)
        snr_layout.addWidget(self.snr_min_spin)
        snr_layout.addWidget(QLabel("to"))
        self.snr_max_spin = QSpinBox()
        self.snr_max_spin.setRange(-20, 30)
        self.snr_max_spin.setValue(20)
        snr_layout.addWidget(self.snr_max_spin)
        dataset_layout.addLayout(snr_layout)

        # Generate button
        self.generate_btn = QPushButton("Generate Dataset")
        self.generate_btn.clicked.connect(self.generate_dataset)
        dataset_layout.addWidget(self.generate_btn)

        dataset_group.setLayout(dataset_layout)
        layout.addWidget(dataset_group)

        # Training section
        training_group = QGroupBox("Training Configuration")
        training_layout = QVBoxLayout()

        # Batch size
        batch_layout = QHBoxLayout()
        batch_layout.addWidget(QLabel("Batch Size:"))
        self.batch_spin = QSpinBox()
        self.batch_spin.setRange(4, 128)
        self.batch_spin.setValue(16)
        batch_layout.addWidget(self.batch_spin)
        training_layout.addLayout(batch_layout)

        # Epochs
        epochs_layout = QHBoxLayout()
        epochs_layout.addWidget(QLabel("Max Epochs:"))
        self.epochs_spin = QSpinBox()
        self.epochs_spin.setRange(1, 200)
        self.epochs_spin.setValue(30)
        epochs_layout.addWidget(self.epochs_spin)
        training_layout.addLayout(epochs_layout)

        # Learning rate
        lr_layout = QHBoxLayout()
        lr_layout.addWidget(QLabel("Learning Rate:"))
        self.lr_combo = QComboBox()
        self.lr_combo.addItems(["0.001", "0.0001", "0.00001"])
        self.lr_combo.setCurrentIndex(1)
        lr_layout.addWidget(self.lr_combo)
        training_layout.addLayout(lr_layout)

        # Train button
        self.train_btn = QPushButton("Start Training")
        self.train_btn.clicked.connect(self.start_training)
        self.train_btn.setEnabled(False)
        training_layout.addWidget(self.train_btn)

        training_group.setLayout(training_layout)
        layout.addWidget(training_group)

        # Status section
        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout()

        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMaximumHeight(200)
        status_layout.addWidget(self.status_text)

        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        layout.addStretch()

        # Export button
        self.export_btn = QPushButton("Export Model")
        self.export_btn.setEnabled(False)
        layout.addWidget(self.export_btn)

        return panel

    def create_right_panel(self):
        panel = QFrame()
        panel.setFrameStyle(QFrame.StyledPanel)
        layout = QVBoxLayout(panel)

        # Title
        title = QLabel("Training Progress")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        # Matplotlib canvas for training curves
        self.figure = Figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        # Initialize plot
        self.ax_loss = self.figure.add_subplot(211)
        self.ax_acc = self.figure.add_subplot(212)

        self.train_loss_data = []
        self.val_loss_data = []
        self.train_acc_data = []
        self.val_acc_data = []

        self.update_plots()

        return panel

    def update_plots(self):
        """Update training progress plots"""
        self.ax_loss.clear()
        self.ax_acc.clear()

        if len(self.train_loss_data) > 0:
            epochs = range(1, len(self.train_loss_data) + 1)
            self.ax_loss.plot(epochs, self.train_loss_data, 'b-', label='Train')
            self.ax_loss.plot(epochs, self.val_loss_data, 'r-', label='Validation')
            self.ax_loss.set_ylabel('Loss')
            self.ax_loss.set_title('Training Loss')
            self.ax_loss.legend()
            self.ax_loss.grid(True)

            self.ax_acc.plot(epochs, self.train_acc_data, 'b-', label='Train')
            self.ax_acc.plot(epochs, self.val_acc_data, 'r-', label='Validation')
            self.ax_acc.set_xlabel('Epoch')
            self.ax_acc.set_ylabel('Accuracy')
            self.ax_acc.set_title('Training Accuracy')
            self.ax_acc.legend()
            self.ax_acc.grid(True)
        else:
            self.ax_loss.text(0.5, 0.5, 'No training data yet',
                            ha='center', va='center', fontsize=12)
            self.ax_acc.text(0.5, 0.5, 'Start training to see results',
                           ha='center', va='center', fontsize=12)

        self.figure.tight_layout()
        self.canvas.draw()

    def log_status(self, message):
        """Add message to status log"""
        self.status_text.append(message)

    def generate_dataset(self):
        """Generate CWT dataset in background thread"""
        self.config['num_samples_per_class'] = self.samples_spin.value()
        self.config['snr_range'] = (self.snr_min_spin.value(), self.snr_max_spin.value())

        self.generate_btn.setEnabled(False)
        self.log_status("Starting dataset generation...")

        self.dataset_thread = DatasetGeneratorThread(self.config, self.modulation_types)
        self.dataset_thread.progress.connect(self.log_status)
        self.dataset_thread.finished.connect(self.on_dataset_generated)
        self.dataset_thread.error.connect(self.on_error)
        self.dataset_thread.start()

    def on_dataset_generated(self, images, labels):
        """Handle completed dataset generation"""
        self.images = images
        self.labels = labels
        self.log_status(f"Dataset generated: {len(labels)} samples")
        self.log_status(f"Images shape: {images.shape}")

        self.generate_btn.setEnabled(True)
        self.train_btn.setEnabled(True)

    def start_training(self):
        """Start training in background thread"""
        if self.images is None or self.labels is None:
            self.log_status("Error: Generate dataset first!")
            return

        # Update config from UI
        self.config['batch_size'] = self.batch_spin.value()
        self.config['epochs'] = self.epochs_spin.value()
        self.config['learning_rate'] = float(self.lr_combo.currentText())

        # Create train/val split
        num_samples = len(self.labels)
        indices = np.random.permutation(num_samples)
        train_size = int(self.config['train_split'] * num_samples)

        train_indices = indices[:train_size]
        val_indices = indices[train_size:]

        # Create datasets
        train_dataset = ModulationDataset(
            self.images[train_indices],
            self.labels[train_indices],
            augment=True
        )
        val_dataset = ModulationDataset(
            self.images[val_indices],
            self.labels[val_indices],
            augment=False
        )

        train_loader = DataLoader(train_dataset, batch_size=self.config['batch_size'], shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=self.config['batch_size'], shuffle=False)

        self.log_status(f"Training set: {len(train_dataset)} samples")
        self.log_status(f"Validation set: {len(val_dataset)} samples")

        # Create model
        self.model = self.create_model(len(self.modulation_types))
        self.log_status("Created ResNet18 model")

        # Reset training curves
        self.train_loss_data = []
        self.val_loss_data = []
        self.train_acc_data = []
        self.val_acc_data = []

        # Start training thread
        self.train_btn.setEnabled(False)
        self.training_thread = TrainingThread(self.model, train_loader, val_loader, self.config)
        self.training_thread.progress.connect(self.log_status)
        self.training_thread.epoch_complete.connect(self.on_epoch_complete)
        self.training_thread.finished.connect(self.on_training_complete)
        self.training_thread.error.connect(self.on_error)
        self.training_thread.start()

    def create_model(self, num_classes):
        """Create ResNet18 with transfer learning"""
        model = models.resnet18(weights='IMAGENET1K_V1')

        num_features = model.fc.in_features
        model.fc = nn.Sequential(
            nn.Dropout(0.5),
            nn.Linear(num_features, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(128, num_classes)
        )

        return model

    def on_epoch_complete(self, epoch, train_loss, train_acc, val_loss, val_acc):
        """Handle epoch completion"""
        self.log_status(
            f"Epoch {epoch}: Train Loss={train_loss:.4f}, Train Acc={train_acc:.4f}, "
            f"Val Loss={val_loss:.4f}, Val Acc={val_acc:.4f}"
        )

        self.train_loss_data.append(train_loss)
        self.val_loss_data.append(val_loss)
        self.train_acc_data.append(train_acc)
        self.val_acc_data.append(val_acc)

        self.update_plots()

    def on_training_complete(self, model):
        """Handle training completion"""
        self.model = model
        self.log_status("Training complete!")
        self.log_status(f"Model saved to {self.config['model_save_path']}")

        self.train_btn.setEnabled(True)
        self.export_btn.setEnabled(True)

    def on_error(self, error_msg):
        """Handle errors"""
        self.log_status(f"ERROR: {error_msg}")
        self.generate_btn.setEnabled(True)
        self.train_btn.setEnabled(True)
