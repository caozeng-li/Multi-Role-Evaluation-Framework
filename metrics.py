import argparse
import os
from typing import List, Tuple

import numpy as np
import pandas as pd

from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    classification_report,
)
from scipy.stats import spearmanr


LABELS = [1, 2, 3]  # 三类优先级（数字越小优先级越高）


def fmt4(x: float) -> str:
    """统一 4 位小数格式（含尾随 0）。"""
    return f"{x:.4f}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        default=None,
        help="输入 Excel 路径；不填则默认取脚本所在目录的 OSDR_studies_with_preds.xlsx",
    )
    parser.add_argument(
        "--true-col",
        default="True_label",
        help="真实标签列名（默认 True_label）",
    )
    parser.add_argument(
        "--pred-col",
        default="Pred_label",
        help="预测标签列名（默认 Pred_label）",
    )
    parser.add_argument(
        "--drop-na",
        action="store_true",
        help="是否丢弃 True/Pred 任一为空的行（建议开启，用于过滤调用失败样本）",
    )
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = args.input or os.path.join(script_dir, "OSDR_studies_with_preds.xlsx")

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"找不到输入文件：{input_path}")

    df = pd.read_excel(input_path)

    if args.true_col not in df.columns or args.pred_col not in df.columns:
        raise ValueError(
            f"缺少列：{args.true_col} 或 {args.pred_col}。当前列：{list(df.columns)}"
        )

    work = df[[args.true_col, args.pred_col]].copy()

    # 转为数值，处理可能的字符串/空值
    work[args.true_col] = pd.to_numeric(work[args.true_col], errors="coerce")
    work[args.pred_col] = pd.to_numeric(work[args.pred_col], errors="coerce")

    if args.drop_na:
        work = work.dropna(subset=[args.true_col, args.pred_col])

    # 转 int（drop_na=False 且存在 NaN 会报错，所以建议用 --drop-na）
    try:
        y_true = work[args.true_col].astype(int).to_numpy()
        y_pred = work[args.pred_col].astype(int).to_numpy()
    except Exception as e:
        raise ValueError(
            "True/Pred 存在空值或无法转为整数。建议加参数 --drop-na，"
            "或先检查 Pred_label 是否都生成成功。"
        ) from e

    # 若存在非 1/2/3 的值，给出提醒（但仍计算，label 集合按 LABELS 固定）
    bad_true = sorted(set(y_true.tolist()) - set(LABELS))
    bad_pred = sorted(set(y_pred.tolist()) - set(LABELS))
    if bad_true or bad_pred:
        print("WARNING: 检测到非 {1,2,3} 的标签值：")
        if bad_true:
            print("  True_label 异常值：", bad_true)
        if bad_pred:
            print("  Pred_label 异常值：", bad_pred)
        print("  指标仍按 labels=[1,2,3] 计算（其余值会被忽略在 per-class 统计中）。\n")

    # ===== Overall Metrics =====
    acc = accuracy_score(y_true, y_pred)

    p_macro, r_macro, f1_macro, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=LABELS, average="macro", zero_division=0
    )
    p_w, r_w, f1_w, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=LABELS, average="weighted", zero_division=0
    )

    # ===== Ordinal-aware Metrics =====
    mae = float(np.mean(np.abs(y_true - y_pred)))

    # Spearman：若全是常数会返回 nan，这里做保护
    rho, _p = spearmanr(y_true, y_pred)
    if np.isnan(rho):
        rho = 0.0

    # ===== Per-class Metrics =====
    p_c, r_c, f1_c, support = precision_recall_fscore_support(
        y_true, y_pred, labels=LABELS, average=None, zero_division=0
    )

    # ===== Print =====
    print("=== Overall Metrics ===")
    print(f"Accuracy:  {fmt4(acc)}")
    print(f"Macro P/R/F1:     {fmt4(p_macro)} / {fmt4(r_macro)} / {fmt4(f1_macro)}")
    print(f"Weighted P/R/F1:  {fmt4(p_w)} / {fmt4(r_w)} / {fmt4(f1_w)}")
    print()

    print("=== Ordinal-aware Metrics ===")
    print(f"MAE (|true-pred| mean): {fmt4(mae)}")
    print(f"Spearman correlation:   {fmt4(rho)}")
    print()

    print("=== Per-class Metrics ===")
    for idx, lab in enumerate(LABELS):
        print(
            f"Label {lab}: Precision={fmt4(p_c[idx])}, Recall={fmt4(r_c[idx])}, "
            f"F1={fmt4(f1_c[idx])}, Support={int(support[idx])}"
        )
    print()

    print("=== Classification Report ===")
    report = classification_report(
        y_true,
        y_pred,
        labels=LABELS,
        digits=4,
        zero_division=0,
    )
    print(report)


if __name__ == "__main__":
    main()
