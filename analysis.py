"""Analisis algoritma KNN sesuai bagian "Rekomendasi Dataset dan Evaluasi" naskah:
k-fold cross validation, normalisasi, SMOTE, grid search nilai k (+ metrik jarak & pembobotan),
metrik akurasi/presisi/recall/F1/AUC-ROC, dan pembanding Naive Bayes & Random Forest.

Jalankan:  python analysis.py
"""
import itertools
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (ConfusionMatrixDisplay, RocCurveDisplay, accuracy_score, f1_score,
                             make_scorer, precision_score, recall_score, roc_auc_score)
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split
from sklearn.naive_bayes import GaussianNB

import config
import crm_data
import model
import nlp

FULL_GRID = dict(k=[1, 3, 5, 7, 9, 11, 15, 21, 31], metric=["euclidean", "manhattan", "chebyshev"],
                 weights=["uniform", "distance"], scaler=["minmax", "standard"], smote=[False, True])
SMALL_GRID = dict(k=[3, 5, 7, 11, 15], metric=["euclidean", "manhattan"],
                  weights=["uniform", "distance"], scaler=["minmax"], smote=[True])
SCORING = {"accuracy": "accuracy",
           "precision": make_scorer(precision_score, zero_division=0),
           "recall": make_scorer(recall_score, zero_division=0),
           "f1": make_scorer(f1_score, zero_division=0),
           "roc_auc": "roc_auc"}


def grid_search(X, y, grid) -> pd.DataFrame:
    skf = StratifiedKFold(config.CV_FOLDS, shuffle=True, random_state=config.RANDOM_STATE)
    rows = []
    for k, metric, weights, scaler, smote in itertools.product(
            grid["k"], grid["metric"], grid["weights"], grid["scaler"], grid["smote"]):
        pipe = model.build_pipeline(model.make_knn(k, metric, weights), scaler, smote)
        cv = cross_validate(pipe, X, y, cv=skf, scoring=SCORING, n_jobs=-1)
        rows.append(dict(k=k, metric=metric, weights=weights, scaler=scaler, smote=smote,
                         **{f"cv_{m}": float(cv[f"test_{m}"].mean()) for m in SCORING},
                         cv_f1_std=float(cv["test_f1"].std())))
    return pd.DataFrame(rows).sort_values(["cv_f1", "cv_roc_auc"], ascending=False).reset_index(drop=True)


def evaluate(pipe, X, y) -> dict:
    pred, proba = pipe.predict(X), pipe.predict_proba(X)[:, 1]
    return {"accuracy": float(accuracy_score(y, pred)),
            "precision": float(precision_score(y, pred, zero_division=0)),
            "recall": float(recall_score(y, pred, zero_division=0)),
            "f1": float(f1_score(y, pred, zero_division=0)),
            "roc_auc": float(roc_auc_score(y, proba))}


def plot_k_curves(grid):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), sharey=True)
    for metric, g in grid.groupby("metric"):
        b = g.groupby("k")["cv_f1"].max()
        axes[0].plot(b.index, b.values, marker="o", label=metric)
    axes[0].set_title("Pengaruh K dan metrik jarak")
    for flag, g in grid.groupby("smote"):
        b = g.groupby("k")["cv_f1"].max()
        axes[1].plot(b.index, b.values, marker="o", label="dengan SMOTE" if flag else "tanpa SMOTE")
    axes[1].set_title("Pengaruh SMOTE")
    for ax in axes:
        ax.set_xlabel("K (jumlah tetangga)"); ax.grid(alpha=.3); ax.legend()
    axes[0].set_ylabel(f"F1-score (CV {config.CV_FOLDS}-fold)")
    fig.tight_layout(); fig.savefig(config.REPORT_DIR / "k_vs_f1.png", dpi=150); plt.close(fig)


def run():
    df = crm_data.load_dataset()
    X, ids = crm_data.engineer_features(df), df["client_id"]
    print(f"Data: {config.DATA_SOURCE} | {len(df)} klien | CV {config.CV_FOLDS}-fold")

    summary, main = [], {}
    for target in crm_data.TARGET_ORDER:
        y = df[target]
        X_tr, X_te, y_tr, y_te, id_tr, _ = train_test_split(
            X, y, ids, test_size=0.2, stratify=y, random_state=config.RANDOM_STATE)
        is_main = target == "smart_money"
        grid = grid_search(X_tr, y_tr, FULL_GRID if is_main else SMALL_GRID)
        best = grid.iloc[0]
        params = dict(k=int(best["k"]), metric=str(best["metric"]), weights=str(best["weights"]),
                      scaler=str(best["scaler"]), smote=bool(best["smote"]))
        knn_pipe = model.build_pipeline(model.make_knn(params["k"], params["metric"], params["weights"]),
                                        params["scaler"], params["smote"]).fit(X_tr, y_tr)
        test = evaluate(knn_pipe, X_te, y_te)
        model.fit_bundle(target, params, X_tr, y_tr, id_tr,
                         {"cv_f1": float(best["cv_f1"]), **{f"test_{k}": v for k, v in test.items()}})
        summary.append({"target": target, "prevalence": float(y.mean()), **params,
                        "cv_f1": float(best["cv_f1"]), **{f"test_{k}": v for k, v in test.items()}})
        print(f"[{target:30s}] K={params['k']:>2} {params['metric']:<9} smote={params['smote']!s:<5} "
              f"CV-F1={best['cv_f1']:.3f} | test F1={test['f1']:.3f} AUC={test['roc_auc']:.3f}")

        if not is_main:
            continue
        grid.to_csv(config.REPORT_DIR / "grid_results.csv", index=False)
        plot_k_curves(grid)
        # --- perbandingan dengan baseline (naskah: Naive Bayes, Random Forest) ---
        models = {
            f"KNN (K={params['k']}, {params['metric']})": knn_pipe,
            "Naive Bayes": model.build_pipeline(GaussianNB(), params["scaler"], params["smote"]),
            "Random Forest": model.build_pipeline(
                RandomForestClassifier(n_estimators=200, random_state=config.RANDOM_STATE, n_jobs=-1),
                params["scaler"], params["smote"]),
        }
        rows = []
        fig, ax = plt.subplots(figsize=(5.5, 5))
        for i, (name, mdl) in enumerate(models.items()):
            if i > 0:  # model KNN sudah terlatih di atas
                mdl.fit(X_tr, y_tr)
            rows.append({"model": name, **evaluate(mdl, X_te, y_te)})
            RocCurveDisplay.from_estimator(mdl, X_te, y_te, ax=ax, name=name)
        ax.plot([0, 1], [0, 1], "k--", alpha=.4)
        ax.set_title("Kurva ROC (data uji)")
        fig.tight_layout(); fig.savefig(config.REPORT_DIR / "roc_curve.png", dpi=150); plt.close(fig)
        comp = pd.DataFrame(rows)
        comp.to_csv(config.REPORT_DIR / "tabel_perbandingan_model.csv", index=False)
        print(comp.round(3).to_string(index=False))
        fig, ax = plt.subplots(figsize=(4.5, 4))
        ConfusionMatrixDisplay.from_predictions(y_te, knn_pipe.predict(X_te), display_labels=["Bukan", "Smart money"],
                                                ax=ax, cmap="Blues", colorbar=False)
        ax.set_title("Confusion matrix KNN (data uji)")
        fig.tight_layout(); fig.savefig(config.REPORT_DIR / "confusion_matrix.png", dpi=150); plt.close(fig)
        main = {"best_params": params, "cv": {k: float(best[f"cv_{k}"]) for k in SCORING},
                "test": test, "comparison": rows, "n_train": len(X_tr), "n_test": len(X_te),
                "majority_accuracy": float(max(y_te.mean(), 1 - y_te.mean())),
                "grid_configs": len(grid)}

    pd.DataFrame(summary).to_csv(config.REPORT_DIR / "all_targets.csv", index=False)
    loo = nlp.evaluate_loo()
    metrics = {"data_source": config.DATA_SOURCE, "n_clients": len(df), "cv_folds": config.CV_FOLDS,
               "target": "smart_money", **main, "all_targets": summary, "nlp_intent_loo_accuracy": loo}
    (config.REPORT_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False))
    print(f"Akurasi intent NLP (leave-one-out): {loo:.1%}\nLaporan: {config.REPORT_DIR} | model: {config.MODEL_DIR}")


if __name__ == "__main__":
    run()
