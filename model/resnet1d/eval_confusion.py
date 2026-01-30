# model/resnet1d/eval_confusion.py
import os, json, argparse
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Subset
import matplotlib.pyplot as plt

import os, sys
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if THIS_DIR not in sys.path:
    sys.path.insert(0, THIS_DIR)


from train_resnet1d import ResNet1D, RFMixedDataset, CLASSES

# we might need to add co-occurance confusion later

'''
example

python model\resnet1d\eval_confusion.py --data_dir out_dataset --ckpt_path model\resnet1d\runs\best_resnet1d.pt --out_dir model\resnet1d\runs --thresh 0.5


'''

@torch.no_grad()
def per_class_confusion(model, loader, device, thresh=0.5):
    """
    Returns confusion[c] = [[TN, FP],
                            [FN, TP]]  for each class c
    shape: (C, 2, 2)
    """
    model.eval()
    C = len(CLASSES)
    TN = np.zeros(C, dtype=np.int64)
    FP = np.zeros(C, dtype=np.int64)
    FN = np.zeros(C, dtype=np.int64)
    TP = np.zeros(C, dtype=np.int64)

    for X, y in loader:
        X = X.to(device, non_blocking=True)
        y = y.to(device, non_blocking=True)

        logits = model(X)
        probs = torch.sigmoid(logits)
        pred = (probs >= thresh).int()
        yt = y.int()

        TP += (pred & yt).sum(dim=0).cpu().numpy()
        FP += (pred & (1 - yt)).sum(dim=0).cpu().numpy()
        FN += ((1 - pred) & yt).sum(dim=0).cpu().numpy()
        TN += ((1 - pred) & (1 - yt)).sum(dim=0).cpu().numpy()

    confusion = np.zeros((C, 2, 2), dtype=np.int64)
    for c in range(C):
        confusion[c, 0, 0] = TN[c]
        confusion[c, 0, 1] = FP[c]
        confusion[c, 1, 0] = FN[c]
        confusion[c, 1, 1] = TP[c]
    return confusion


def plot_per_class_confusion(confusion, classes, save_path):
    """
    Plot each class's 2x2 confusion as a small grid.
    """
    C = len(classes)
    cols = 3
    rows = int(np.ceil(C / cols))

    plt.figure(figsize=(cols * 4, rows * 4))
    for i, cls in enumerate(classes):
        ax = plt.subplot(rows, cols, i + 1)
        mat = confusion[i]
        ax.imshow(mat, interpolation="nearest")
        ax.set_title(cls)
        ax.set_xticks([0, 1])
        ax.set_yticks([0, 1])
        ax.set_xticklabels(["Pred 0", "Pred 1"])
        ax.set_yticklabels(["True 0", "True 1"])

        # write numbers
        for r in range(2):
            for c in range(2):
                ax.text(c, r, str(mat[r, c]), ha="center", va="center")

    plt.tight_layout()
    plt.savefig(save_path, dpi=200)
    plt.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data_dir", type=str, required=True)         # out_dataset
    ap.add_argument("--ckpt_path", type=str, required=True)        # runs/.../best.pt
    ap.add_argument("--out_dir", type=str, required=True)          # runs/.../
    ap.add_argument("--batch_size", type=int, default=128)
    ap.add_argument("--num_workers", type=int, default=2)
    ap.add_argument("--n_expected", type=int, default=4096)
    ap.add_argument("--thresh", type=float, default=0.5)
    args = ap.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    ds = RFMixedDataset(args.data_dir, n_expected=args.n_expected, normalize_power=True)

    # 10% = test
    n = len(ds)
    test_idx = list(range(int(0.9 * n), n))
    test_loader = DataLoader(Subset(ds, test_idx), batch_size=args.batch_size,
                             shuffle=False, num_workers=args.num_workers, pin_memory=True)

    # load model
    ckpt = torch.load(args.ckpt_path, map_location=device)
    model = ResNet1D(in_ch=2, num_classes=len(CLASSES)).to(device)
    model.load_state_dict(ckpt["model"])

    confusion = per_class_confusion(model, test_loader, device, thresh=args.thresh)

    os.makedirs(args.out_dir, exist_ok=True)
    npy_path = os.path.join(args.out_dir, "confusion_per_class.npy")
    png_path = os.path.join(args.out_dir, "confusion_per_class.png")

    np.save(npy_path, confusion)
    plot_per_class_confusion(confusion, CLASSES, png_path)

    print("Saved:", npy_path)
    print("Saved:", png_path)


if __name__ == "__main__":
    main()
