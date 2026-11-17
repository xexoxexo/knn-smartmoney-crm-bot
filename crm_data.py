"""Skema data CRM keuangan (Tabel 5 naskah), generator data sintetis, rekayasa fitur,
dan definisi target (termasuk operasionalisasi 'smart money')."""
from __future__ import annotations

import numpy as np
import pandas as pd

import config

# ---- Kolom mentah di basis data CRM (satuan uang: juta Rupiah per tahun) ----------
RAW_COLS = [
    "total_revenue", "total_profit", "profit_prev_year",
    "num_invest_proposals", "invest_proposals_value",
    "debt_equity_ratio", "vol_graph",
    "invest_gold", "invest_bitcoin", "invest_stock_bbca",
    "emergency_fund_balance",
    "annual_budget", "annual_budget_prev",
    "monthly_expenses", "monthly_expenses_std",
    "annual_expenses", "total_salaries",
]

# ---- Fitur hasil transformasi (kolom "Transformasi Fitur" Tabel 5) -----------------
FEATURES = [
    "profit_margin", "profit_growth",
    "num_invest_proposals", "invest_proposals_avg",
    "debt_equity_ratio", "vol_graph",
    "total_invested_value", "commodity_share",
    "emergency_fund_ratio",
    "budget_growth", "budget_utilization",
    "monthly_spend_ratio", "expense_variation",
    "cost_income_ratio", "salary_ratio",
]

# ---- Target prediksi (kolom "Target Prediksi" Tabel 5 + smart money) ---------------
TARGETS = {
    "smart_money": "Smart money (pengelolaan dana cerdas)",
    "high_profit_client": "Laba tinggi",
    "high_invest_opportunity": "Peluang investasi tinggi",
    "high_budget_risk": "Risiko anggaran tinggi",
    "prefers_commodity_investment": "Condong investasi komoditas",
    "has_emergency_fund": "Dana darurat memadai",
    "on_budget": "Sesuai anggaran",
    "high_monthly_spending": "Pengeluaran bulanan tinggi",
    "cost_control_alert": "Peringatan kontrol biaya",
    "high_salary_expense": "Beban gaji tinggi",
}
TARGET_ORDER = list(TARGETS)
NEGATIVE_TARGETS = {"high_budget_risk", "high_monthly_spending", "cost_control_alert", "high_salary_expense"}

# Tabel 5 naskah: (Fitur CRM, Kolom Data, Transformasi, Target)
TABLE5 = [
    ("Total Profit (Laba)", "total_revenue, total_profit, profit_prev_year", "profit_margin, profit_growth", "high_profit_client"),
    ("Peluang Investasi", "num_invest_proposals, invest_proposals_value", "invest_proposals_avg", "high_invest_opportunity"),
    ("Risiko Anggaran", "debt_equity_ratio, vol_graph", "volatilitas pendapatan", "high_budget_risk"),
    ("Investasi Emas/Bitcoin/BBCA", "invest_gold, invest_bitcoin, invest_stock_bbca", "total_invested_value, commodity_share", "prefers_commodity_investment"),
    ("Dana Darurat", "emergency_fund_balance", "emergency_fund_ratio", "has_emergency_fund"),
    ("Anggaran Tahunan", "annual_budget, annual_budget_prev", "budget_growth, budget_utilization", "on_budget"),
    ("Pengeluaran Bulanan", "monthly_expenses, monthly_expenses_std", "monthly_spend_ratio, expense_variation", "high_monthly_spending"),
    ("Total Pengeluaran Tahun", "annual_expenses", "cost_income_ratio", "cost_control_alert"),
    ("Gaji Karyawan", "total_salaries", "salary_ratio", "high_salary_expense"),
]

# Ambang batas aturan bisnis untuk label (dapat disesuaikan dengan kebijakan perusahaan)
TH = dict(
    profit_margin=0.25, min_proposals=3, min_avg_proposal=200.0,
    der=2.0, vol=0.40, commodity_share=0.50, emergency_ratio=0.10,
    budget_util=1.0, monthly_spend=0.70, expense_var=0.30,
    cost_income=0.75, salary_ratio=0.35,
    smart_min_score=6,   # smart money = minimal 6 dari 7 indikator sehat terpenuhi
)


def _ratios(df: pd.DataFrame) -> pd.DataFrame:
    rev = df.total_revenue.replace(0, np.nan)
    invested = df.invest_gold + df.invest_bitcoin + df.invest_stock_bbca
    r = pd.DataFrame(index=df.index)
    r["profit_margin"] = df.total_profit / rev
    r["profit_growth"] = (df.total_profit - df.profit_prev_year) / df.profit_prev_year.abs().replace(0, np.nan)
    r["num_invest_proposals"] = df.num_invest_proposals
    r["invest_proposals_avg"] = df.invest_proposals_value / df.num_invest_proposals.clip(lower=1)
    r["debt_equity_ratio"] = df.debt_equity_ratio
    r["vol_graph"] = df.vol_graph
    r["total_invested_value"] = invested
    r["commodity_share"] = (df.invest_gold + df.invest_bitcoin) / invested.replace(0, np.nan)
    r["emergency_fund_ratio"] = df.emergency_fund_balance / rev
    r["budget_growth"] = (df.annual_budget - df.annual_budget_prev) / df.annual_budget_prev.replace(0, np.nan)
    r["budget_utilization"] = df.annual_expenses / df.annual_budget.replace(0, np.nan)
    r["monthly_spend_ratio"] = df.monthly_expenses * 12 / rev
    r["expense_variation"] = df.monthly_expenses_std / df.monthly_expenses.replace(0, np.nan)
    r["cost_income_ratio"] = df.annual_expenses / rev
    r["salary_ratio"] = df.total_salaries / rev
    return r.replace([np.inf, -np.inf], np.nan)


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Kolom mentah CRM -> fitur model (rasio, pertumbuhan, volatilitas, log untuk nilai uang)."""
    f = _ratios(df)
    f["invest_proposals_avg"] = np.log1p(f["invest_proposals_avg"])
    f["total_invested_value"] = np.log1p(f["total_invested_value"])
    return f[FEATURES]


def derive_targets(df: pd.DataFrame) -> pd.DataFrame:
    """Label berbasis aturan bisnis (dipakai bila CSV belum berisi kolom target)."""
    r = _ratios(df)
    t = pd.DataFrame(index=df.index)
    t["high_profit_client"] = r.profit_margin >= TH["profit_margin"]
    t["high_invest_opportunity"] = (r.num_invest_proposals >= TH["min_proposals"]) & (r.invest_proposals_avg >= TH["min_avg_proposal"])
    t["high_budget_risk"] = (r.debt_equity_ratio >= TH["der"]) | (r.vol_graph >= TH["vol"])
    t["prefers_commodity_investment"] = r.commodity_share >= TH["commodity_share"]
    t["has_emergency_fund"] = r.emergency_fund_ratio >= TH["emergency_ratio"]
    t["on_budget"] = r.budget_utilization <= TH["budget_util"]
    t["high_monthly_spending"] = (r.monthly_spend_ratio >= TH["monthly_spend"]) | (r.expense_variation >= TH["expense_var"])
    t["cost_control_alert"] = r.cost_income_ratio >= TH["cost_income"]
    t["high_salary_expense"] = r.salary_ratio >= TH["salary_ratio"]
    t = t.astype(int)
    score = (t.high_profit_client + t.has_emergency_fund + t.on_budget + t.high_invest_opportunity
             + (1 - t.cost_control_alert) + (1 - t.high_budget_risk) + (1 - t.high_salary_expense))
    t["smart_money"] = (score >= TH["smart_min_score"]).astype(int)
    return t[TARGET_ORDER]


def make_synthetic_crm(n: int = 1500, seed: int = 42, label_noise: float = 0.05) -> pd.DataFrame:
    """Data CRM simulasi mengikuti skema Tabel 5. Satu variabel laten 'kesehatan finansial'
    membuat kolom saling berkorelasi; label diberi derau agar tidak terpisah sempurna
    (meniru penilaian bisnis yang tidak selalu konsisten)."""
    rng = np.random.default_rng(seed)
    h = rng.beta(2.2, 2.8, n)
    rev = rng.lognormal(np.log(4000), 0.8, n)
    margin = np.clip(0.02 + 0.38 * h + rng.normal(0, 0.06, n), -0.15, 0.6)
    profit = rev * margin
    growth = np.clip(rng.normal(0.2 * (h - 0.5), 0.12, n), -0.5, 1.0)
    n_prop = rng.poisson(0.5 + 4 * h)
    invested = rev * 0.25 * rng.beta(2, 3, n) * (0.4 + h)
    comm = rng.beta(2, 3, n)
    ann_exp = rev * np.clip(0.90 - 0.55 * h + rng.normal(0, 0.08, n), 0.2, 1.3)
    budget = ann_exp / np.clip(1.08 - 0.30 * h + rng.normal(0, 0.10, n), 0.6, 1.6)
    m_exp = ann_exp / 12 * rng.uniform(0.85, 1.15, n)
    df = pd.DataFrame({
        "total_revenue": rev, "total_profit": profit, "profit_prev_year": profit / (1 + growth),
        "num_invest_proposals": n_prop, "invest_proposals_value": n_prop * rev * rng.uniform(0.02, 0.15, n),
        "debt_equity_ratio": np.clip(rng.normal(1.9 - 1.5 * h, 0.5), 0.1, 5),
        "vol_graph": np.clip(rng.normal(0.40 - 0.30 * h, 0.08), 0.02, 1.0),
        "invest_gold": invested * comm * 0.6, "invest_bitcoin": invested * comm * 0.4,
        "invest_stock_bbca": invested * (1 - comm),
        "emergency_fund_balance": rev * np.clip(0.01 + 0.25 * h + rng.normal(0, 0.05, n), 0, 0.6),
        "annual_budget": budget, "annual_budget_prev": budget / (1 + rng.normal(0.05, 0.08, n)),
        "monthly_expenses": m_exp,
        "monthly_expenses_std": m_exp * np.clip(rng.normal(0.22 - 0.10 * h, 0.07, n), 0.03, 0.6),
        "annual_expenses": ann_exp,
        "total_salaries": rev * np.clip(0.38 - 0.18 * h + rng.normal(0, 0.07, n), 0.05, 0.7),
    }).round(2)[RAW_COLS]
    t = derive_targets(df)
    flip = rng.random(t.shape) < label_noise
    t = t.where(~flip, 1 - t)
    out = pd.concat([df, t], axis=1)
    out.insert(0, "client_id", [f"C{i + 1:04d}" for i in range(n)])
    return out


def load_dataset() -> pd.DataFrame:
    """Dataset CRM + target. synthetic -> generator; csv -> data sendiri (kolom = RAW_COLS + client_id;
    kolom target opsional, jika kosong dihitung dari aturan bisnis TH)."""
    if config.DATA_SOURCE == "csv":
        df = pd.read_csv(config.CSV_PATH)
        missing = [c for c in ["client_id"] + RAW_COLS if c not in df.columns]
        if missing:
            raise ValueError(f"Kolom CSV belum lengkap: {missing}")
        derived = derive_targets(df)
        for c in TARGET_ORDER:
            if c not in df.columns:
                df[c] = derived[c]
        return df
    return make_synthetic_crm(config.N_CLIENTS, config.RANDOM_STATE, config.LABEL_NOISE)
