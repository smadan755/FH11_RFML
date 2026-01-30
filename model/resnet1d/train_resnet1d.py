# scripts/train_resnet1d.py
import os, json, glob, argparse, random
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader, Subset

# use gpu if available
'''

How to run: 

python model\resnet1d\train_resnet1d.py --data_dir out_dataset --epochs 25 --batch_size 64 --use_pos_weight


'''

# -----------------------------

# 0) Class list (coarse families)
# -----------------------------
CLASSES = ["PSK", "QAM", "GFSK", "OFDM", "DSSS_OQPSK", "CSS_LORA"]
C2I = {c: i for i, c in enumerate(CLASSES)}


# -----------------------------
# 1) Dataset: loads (x from npz) + (labels from json)
# -----------------------------
class RFMixedDataset(Dataset):
    """
    Expects files:
      data_dir/00000000.npz  contains 'x' (complex baseband)
      data_dir/00000000.json contains metadata with labels
    """
    def __init__(self, data_dir: str, n_expected: int | None = None, normalize_power: bool = True):
        self.data_dir = data_dir
        self.normalize_power = normalize_power

        npz_files = sorted(glob.glob(os.path.join(data_dir, "*.npz")))
        if len(npz_files) == 0:
            raise FileNotFoundError(f"No .npz files found in: {data_dir}")

        # keep only those with matching json
        pairs = []
        for npz_path in npz_files:
            base = os.path.splitext(npz_path)[0]
            json_path = base + ".json"
            if os.path.exists(json_path):
                pairs.append((npz_path, json_path))
        if len(pairs) == 0:
            raise FileNotFoundError(f"Found .npz but no matching .json in: {data_dir}")

        self.pairs = pairs
        self.n_expected = n_expected  # optional: enforce length

    def __len__(self):
        return len(self.pairs)

    def _load_label_vector(self, meta: Dict[str, Any]) -> torch.Tensor:
        """
        Multi-label vector of length len(CLASSES).
        Supports:
          - meta["label_multilabel"] = ["OFDM", "GFSK"]
          - or meta["signals"] list containing per-signal meta with "label" fields
        """
        y = np.zeros((len(CLASSES),), dtype=np.float32)

        labels = None
        if "label_multilabel" in meta and meta["label_multilabel"] is not None:
            labels = meta["label_multilabel"]
        elif "signals" in meta and meta["signals"] is not None:
            # meta["signals"] might be list of dicts with "label" keys
            labels = [s.get("label") for s in meta["signals"] if isinstance(s, dict)]

        if labels is None:
            raise KeyError("Metadata missing label_multilabel or signals[].label")

        for lab in labels:
            if lab in C2I:
                y[C2I[lab]] = 1.0
            else:
                # if you stored subtype labels like {"label":"DSSS_OQPSK"} etc, ensure matches CLASSES
                # ignore unknown labels
                pass

        return torch.from_numpy(y)

    def __getitem__(self, idx: int):
        npz_path, json_path = self.pairs[idx]

        with np.load(npz_path) as z:
            x = z["x"]  # complex array, shape (n,)
        with open(json_path, "r") as f:
            meta = json.load(f)

        # enforce length if desired
        if self.n_expected is not None and x.shape[0] != self.n_expected:
            # pad or truncate to n_expected
            n = self.n_expected
            if x.shape[0] < n:
                pad = np.zeros((n - x.shape[0],), dtype=x.dtype)
                x = np.concatenate([x, pad], axis=0)
            else:
                x = x[:n]

        # convert complex -> 2-channel (I, Q)
        I = np.real(x).astype(np.float32)
        Q = np.imag(x).astype(np.float32)
        X = np.stack([I, Q], axis=0)  # (2, n)

        # per-sample power normalization (optional but recommended)
        if self.normalize_power:
            p = np.mean(X[0] ** 2 + X[1] ** 2) + 1e-12
            X = X / np.sqrt(p)

        y = self._load_label_vector(meta)

        return torch.from_numpy(X), y


# -----------------------------
# 2) ResNet1D model (BasicBlock)
# -----------------------------
class BasicBlock1D(nn.Module):
    expansion = 1
    def __init__(self, in_ch: int, out_ch: int, stride: int = 1):
        super().__init__()
        self.conv1 = nn.Conv1d(in_ch, out_ch, kernel_size=7, stride=stride, padding=3, bias=False)
        self.bn1 = nn.BatchNorm1d(out_ch)
        self.relu = nn.ReLU(inplace=True)

        self.conv2 = nn.Conv1d(out_ch, out_ch, kernel_size=7, stride=1, padding=3, bias=False)
        self.bn2 = nn.BatchNorm1d(out_ch)

        self.downsample = None
        if stride != 1 or in_ch != out_ch:
            self.downsample = nn.Sequential(
                nn.Conv1d(in_ch, out_ch, kernel_size=1, stride=stride, bias=False),
                nn.BatchNorm1d(out_ch),
            )

    def forward(self, x):
        identity = x

        out = self.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))

        if self.downsample is not None:
            identity = self.downsample(identity)

        out = self.relu(out + identity)
        return out


class ResNet1D(nn.Module):
    def __init__(self, in_ch: int = 2, num_classes: int = 6, layers=(2, 2, 2, 2), base_width: int = 64):
        super().__init__()
        self.stem = nn.Sequential(
            nn.Conv1d(in_ch, base_width, kernel_size=15, stride=2, padding=7, bias=False),
            nn.BatchNorm1d(base_width),
            nn.ReLU(inplace=True),
            nn.MaxPool1d(kernel_size=3, stride=2, padding=1),
        )

        ch = base_width
        self.layer1 = self._make_layer(ch, ch, blocks=layers[0], stride=1)
        self.layer2 = self._make_layer(ch, ch*2, blocks=layers[1], stride=2); ch *= 2
        self.layer3 = self._make_layer(ch, ch*2, blocks=layers[2], stride=2); ch *= 2
        self.layer4 = self._make_layer(ch, ch*2, blocks=layers[3], stride=2); ch *= 2

        self.pool = nn.AdaptiveAvgPool1d(1)
        self.fc = nn.Linear(ch, num_classes)

    def _make_layer(self, in_ch, out_ch, blocks: int, stride: int):
        layers = [BasicBlock1D(in_ch, out_ch, stride=stride)]
        for _ in range(1, blocks):
            layers.append(BasicBlock1D(out_ch, out_ch, stride=1))
        return nn.Sequential(*layers)

    def forward(self, x):
        x = self.stem(x)
        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)
        x = self.pool(x).squeeze(-1)
        logits = self.fc(x)  # (B, num_classes)
        return logits


# -----------------------------
# 3) Metrics (multi-label F1)
# -----------------------------
@torch.no_grad()
def multilabel_f1(logits: torch.Tensor, y_true: torch.Tensor, thresh: float = 0.5):
    """
    logits: (B, C), y_true: (B, C) in {0,1}
    """
    probs = torch.sigmoid(logits)
    y_pred = (probs >= thresh).float()

    tp = (y_pred * y_true).sum(dim=0)
    fp = (y_pred * (1 - y_true)).sum(dim=0)
    fn = ((1 - y_pred) * y_true).sum(dim=0)

    # per-class F1 (macro)
    f1_per = (2 * tp) / (2 * tp + fp + fn + 1e-12)
    macro_f1 = f1_per.mean().item()

    # micro F1
    TP = tp.sum()
    FP = fp.sum()
    FN = fn.sum()
    micro_f1 = (2 * TP / (2 * TP + FP + FN + 1e-12)).item()

    return micro_f1, macro_f1, f1_per.cpu().numpy()


# -----------------------------
# 4) Train / Eval loops
# -----------------------------
def run_epoch(model, loader, optimizer, criterion, device, train: bool):
    if train:
        model.train()
    else:
        model.eval()

    total_loss = 0.0
    all_logits = []
    all_y = []

    for X, y in loader:
        X = X.to(device)
        y = y.to(device)

        logits = model(X)
        loss = criterion(logits, y)

        if train:
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            optimizer.step()

        total_loss += loss.item() * X.size(0)
        all_logits.append(logits.detach().cpu())
        all_y.append(y.detach().cpu())

    total_loss /= len(loader.dataset)
    all_logits = torch.cat(all_logits, dim=0)
    all_y = torch.cat(all_y, dim=0)

    micro_f1, macro_f1, f1_per = multilabel_f1(all_logits, all_y)
    return total_loss, micro_f1, macro_f1, f1_per


def compute_pos_weight(dataset: Dataset, indices: List[int]) -> torch.Tensor:
    """
    For BCEWithLogitsLoss(pos_weight=...), to handle class imbalance.
    pos_weight[c] = (neg/pos)
    """
    counts = np.zeros((len(CLASSES),), dtype=np.float64)
    for idx in indices:
        _, y = dataset[idx]
        counts += y.numpy()
    pos = counts
    neg = len(indices) - pos
    pos_weight = (neg / (pos + 1e-12)).astype(np.float32)
    return torch.from_numpy(pos_weight)


# -----------------------------
# 5) Main
# -----------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data_dir", type=str, required=True)
    ap.add_argument("--epochs", type=int, default=20)
    ap.add_argument("--batch_size", type=int, default=64)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--weight_decay", type=float, default=1e-4)
    ap.add_argument("--num_workers", type=int, default=2)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--n_expected", type=int, default=4096)
    ap.add_argument("--use_pos_weight", action="store_true")
    ap.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu")
    args = ap.parse_args()

    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)

    ds = RFMixedDataset(args.data_dir, n_expected=args.n_expected, normalize_power=True)

    # split indices (80/10/10)
    n = len(ds)
    idxs = np.arange(n)
    np.random.default_rng(args.seed).shuffle(idxs)
    n_train = int(0.8 * n)
    n_val = int(0.1 * n)
    train_idx = idxs[:n_train].tolist()
    val_idx = idxs[n_train:n_train + n_val].tolist()
    test_idx = idxs[n_train + n_val:].tolist()

    train_loader = DataLoader(Subset(ds, train_idx), batch_size=args.batch_size, shuffle=True,
                              num_workers=args.num_workers, pin_memory=True)
    val_loader = DataLoader(Subset(ds, val_idx), batch_size=args.batch_size, shuffle=False,
                            num_workers=args.num_workers, pin_memory=True)
    test_loader = DataLoader(Subset(ds, test_idx), batch_size=args.batch_size, shuffle=False,
                             num_workers=args.num_workers, pin_memory=True)

    device = torch.device(args.device)

    model = ResNet1D(in_ch=2, num_classes=len(CLASSES), layers=(2,2,2,2), base_width=64).to(device)

    # loss
    if args.use_pos_weight:
        pw = compute_pos_weight(ds, train_idx).to(device)
        criterion = nn.BCEWithLogitsLoss(pos_weight=pw)
        print("Using pos_weight:", pw.detach().cpu().numpy())
    else:
        criterion = nn.BCEWithLogitsLoss()

    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)

    best_val = -1.0
    # where to save best model
    run_dir = os.path.join("model", "resnet1d", "runs")
    os.makedirs(run_dir, exist_ok=True)
    best_path = os.path.join(run_dir, "best_resnet1d.pt")


    for epoch in range(1, args.epochs + 1):
        tr_loss, tr_micro, tr_macro, _ = run_epoch(model, train_loader, optimizer, criterion, device, train=True)
        va_loss, va_micro, va_macro, f1_per = run_epoch(model, val_loader, optimizer, criterion, device, train=False)

        print(f"[{epoch:02d}] "
              f"train loss={tr_loss:.4f} microF1={tr_micro:.3f} macroF1={tr_macro:.3f} | "
              f"val loss={va_loss:.4f} microF1={va_micro:.3f} macroF1={va_macro:.3f}")

        # save best by macro-F1 (you can change to micro)
        if va_macro > best_val:
            best_val = va_macro
            torch.save({"model": model.state_dict(), "classes": CLASSES}, best_path)
            print("  saved best ->", best_path)
            print("  per-class F1:", dict(zip(CLASSES, np.round(f1_per, 3))))

    # test with best checkpoint
    ckpt = torch.load(best_path, map_location=device)
    model.load_state_dict(ckpt["model"])
    te_loss, te_micro, te_macro, f1_per = run_epoch(model, test_loader, optimizer, criterion, device, train=False)
    print(f"[TEST] loss={te_loss:.4f} microF1={te_micro:.3f} macroF1={te_macro:.3f}")
    print("per-class F1:", dict(zip(CLASSES, np.round(f1_per, 3))))


if __name__ == "__main__":
    main()
