import torch
import torch.nn as nn


class SimpleCNN(nn.Module):
    """1D CNN for signal classification with adaptive pooling."""
    def __init__(self, num_classes=2):
        super().__init__()
        self.conv1 = nn.Conv1d(1, 16, kernel_size=9, padding=4)
        self.pool1 = nn.MaxPool1d(2)
        self.conv2 = nn.Conv1d(16, 32, kernel_size=7, padding=3)
        self.pool2 = nn.MaxPool1d(2)
        self.adaptive_pool = nn.AdaptiveAvgPool1d(64)
        self.fc1 = nn.Linear(32 * 64, 64)
        self.fc2 = nn.Linear(64, num_classes)
        self.relu = nn.ReLU()

    def forward(self, x):
        x = self.relu(self.conv1(x))
        x = self.pool1(x)
        x = self.relu(self.conv2(x))
        x = self.pool2(x)
        x = self.adaptive_pool(x)
        x = x.view(x.size(0), -1)
        x = self.relu(self.fc1(x))
        x = self.fc2(x)
        return x


class TinyConv(nn.Module):
    """Minimal 1D CNN with adaptive pooling."""
    def __init__(self, num_classes=2):
        super().__init__()
        self.conv1 = nn.Conv1d(1, 8, kernel_size=5, padding=2)
        self.pool1 = nn.MaxPool1d(2)
        self.adaptive_pool = nn.AdaptiveAvgPool1d(32)
        self.fc1 = nn.Linear(8 * 32, num_classes)
        self.relu = nn.ReLU()

    def forward(self, x):
        x = self.relu(self.conv1(x))
        x = self.pool1(x)
        x = self.adaptive_pool(x)
        x = x.view(x.size(0), -1)
        x = self.fc1(x)
        return x


class MLP(nn.Module):
    """Multi-layer perceptron."""
    def __init__(self, input_size=256, num_classes=2):
        super().__init__()
        self.fc1 = nn.Linear(input_size, 256)
        self.fc2 = nn.Linear(256, 128)
        self.fc3 = nn.Linear(128, num_classes)
        self.relu = nn.ReLU()

    def forward(self, x):
        x = x.view(x.size(0), -1)
        x = self.relu(self.fc1(x))
        x = self.relu(self.fc2(x))
        x = self.fc3(x)
        return x


def get_num_groups(channels, max_groups=32):
    """Utility for GroupNorm in ResNet1D"""
    for g in range(max_groups, 0, -1):
        if channels % g == 0:
            return g
    return 1

class SEBlock1D(nn.Module):
    def __init__(self, channels, reduction=16):
        super().__init__()
        self.avg_pool = nn.AdaptiveAvgPool1d(1)
        self.fc = nn.Sequential(
            nn.Linear(channels, channels // reduction, bias=False),
            nn.ReLU(inplace=True),
            nn.Linear(channels // reduction, channels, bias=False),
            nn.Sigmoid()
        )

    def forward(self, x):
        b, c, _ = x.size()
        y = self.avg_pool(x).view(b, c)
        y = self.fc(y).view(b, c, 1)
        return x * y.expand_as(x)

class ResBlock1D(nn.Module):
    def __init__(self, in_ch, out_ch, kernel_size=16, stride=1, downsample=None, dropout=0.2):
        super().__init__()
        padding = (kernel_size - 1) // 2
        num_groups = get_num_groups(out_ch)
        
        self.conv1 = nn.Conv1d(in_ch, out_ch, kernel_size, stride, padding, bias=False)
        self.gn1 = nn.GroupNorm(num_groups, out_ch)
        self.conv2 = nn.Conv1d(out_ch, out_ch, kernel_size, 1, padding, bias=False)
        self.gn2 = nn.GroupNorm(num_groups, out_ch)
        self.relu = nn.ReLU(inplace=True)
        self.downsample = downsample
        self.se = SEBlock1D(out_ch)
        self.dropout = nn.Dropout(dropout) if dropout > 0 else None
        
    def forward(self, x):
        identity = x
        out = self.relu(self.gn1(self.conv1(x)))
        if self.dropout: out = self.dropout(out)
        out = self.gn2(self.conv2(out))
        out = self.se(out)
        if self.downsample:
            identity = self.downsample(x)
        if out.size(-1) != identity.size(-1):
            identity = nn.functional.adaptive_avg_pool1d(identity, out.size(-1))
        out += identity
        return self.relu(out)

class MultiScaleInput(nn.Module):
    def __init__(self, in_ch, out_ch):
        super().__init__()
        branch_ch = out_ch // 4
        ng = get_num_groups(branch_ch, max_groups=8)
        self.b1 = nn.Sequential(nn.Conv1d(in_ch, branch_ch, 3, padding=1), nn.GroupNorm(ng, branch_ch), nn.ReLU())
        self.b2 = nn.Sequential(nn.Conv1d(in_ch, branch_ch, 7, padding=3), nn.GroupNorm(ng, branch_ch), nn.ReLU())
        self.b3 = nn.Sequential(nn.Conv1d(in_ch, branch_ch, 15, padding=7), nn.GroupNorm(ng, branch_ch), nn.ReLU())
        self.b4 = nn.Sequential(nn.AvgPool1d(3, 1, 1), nn.Conv1d(in_ch, branch_ch, 1), nn.GroupNorm(ng, branch_ch), nn.ReLU())
        
    def forward(self, x):
        return torch.cat([self.b1(x), self.b2(x), self.b3(x), self.b4(x)], dim=1)

class ResNet1DOptimized(nn.Module):
    def __init__(self, in_ch=2, base_filters=64, n_classes=7, dropout=0.2):
        super().__init__()
        self.input_layer = MultiScaleInput(in_ch, base_filters)
        self.layers = nn.ModuleList()
        in_filters = base_filters
        for i in range(10): # n_block=10
            out_filters = min(base_filters * (2 ** (i // 3)), 256)
            block_stride = 2 if i < 6 else 1
            downsample = None
            if block_stride != 1 or in_filters != out_filters:
                downsample = nn.Sequential(
                    nn.Conv1d(in_filters, out_filters, 1, block_stride, bias=False),
                    nn.GroupNorm(get_num_groups(out_filters), out_filters)
                )
            self.layers.append(ResBlock1D(in_filters, out_filters, 16, block_stride, downsample, dropout))
            in_filters = out_filters
        self.gap = nn.AdaptiveAvgPool1d(1)
        self.classifier = nn.Sequential(
            nn.Flatten(), nn.Dropout(dropout), nn.Linear(in_filters, 128),
            nn.ReLU(inplace=True), nn.Dropout(dropout/2), nn.Linear(128, n_classes)
        )
        
    def forward(self, x):
        x = self.input_layer(x)
        for layer in self.layers: x = layer(x)
        return self.classifier(self.gap(x))




def get_model(name, num_classes=2, input_size=256):
    """Return a PyTorch model by name."""
    if name == 'SimpleCNN':
        return SimpleCNN(num_classes=num_classes)
    elif name == 'TinyConv':
        return TinyConv(num_classes=num_classes)
    elif name == 'MLP':
        return MLP(input_size=input_size, num_classes=num_classes)
    elif name == 'ResNet1DOptimized':
        # in_ch=2 for IQ signals 
        return ResNet1DOptimized(in_ch=2, n_classes=num_classes)
    else:
        return SimpleCNN(num_classes=num_classes)

