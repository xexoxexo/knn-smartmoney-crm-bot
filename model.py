"""Pipeline KNN sesuai rekomendasi naskah: imputasi -> normalisasi -> SMOTE -> KNN.
Juga penyimpanan model per target dan prediksi untuk satu klien."""
from __future__ import annotations

import joblib
import numpy as np
import pandas as pd
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline
from sklearn.impute import SimpleImputer
from sklearn.neighbors import KNeighborsClassifier, NearestNeighbors
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler, StandardScaler

import config
import crm_data

SCALERS = {"minmax": MinMaxScaler, "standard": StandardScaler}


def make_knn(k: int, metric: str = "euclidean", weights: str = "uniform") -> KNeighborsClassifier:
    return KNeighborsClassifier(n_neighbors=k, metric=metric, weights=weights)


def build_pipeline(clf, scaler: str = "minmax", smote: bool = True, seed: int | None = None) -> ImbPipeline:
    """SMOTE hanya aktif saat fit (pada data latih tiap fold), tidak saat prediksi."""
    steps = [("imputer", SimpleImputer(strategy="median")), ("scaler", SCALERS[scaler]())]
    if smote:
        steps.append(("smote", SMOTE(random_state=seed if seed is not None else config.RANDOM_STATE)))
    steps.append(("clf", clf))
    return ImbPipeline(steps)


def model_path(target: str):
    return config.MODEL_DIR / f"knn_{target}.joblib"


def fit_bundle(target: str, params: dict, X: pd.DataFrame, y, ids, metrics: dict | None = None) -> dict:
    pipe = build_pipeline(make_knn(params["k"], params["metric"], params["weights"]),
                          params["scaler"], params["smote"]).fit(X, y)
    # praproses terlatih + indeks tetangga pada data ASLI (tanpa sampel sintetis SMOTE)
    pre = Pipeline([(n, s) for n, s in pipe.steps if n in ("imputer", "scaler")])
    nn = NearestNeighbors(n_neighbors=min(5, len(X)), metric=params["metric"]).fit(pre.transform(X))
    bundle = {"target": target, "model": pipe, "pre": pre, "nn": nn,
              "y_train": np.asarray(y), "ids_train": np.asarray(ids),
              "params": params, "metrics": metrics or {}}
    joblib.dump(bundle, model_path(target))
    return bundle


def load_all() -> dict:
    out = {}
    for t in crm_data.TARGET_ORDER:
        if model_path(t).exists():
            out[t] = joblib.load(model_path(t))
    return out


def predict_one(bundle: dict, feats: pd.DataFrame, n_similar: int = 3, exclude_id: str | None = None) -> dict:
    """feats: DataFrame 1 baris berisi crm_data.FEATURES (boleh ada NaN -> diimputasi median)."""
    X = feats[crm_data.FEATURES]
    pipe = bundle["model"]
    prob = float(pipe.predict_proba(X)[0, 1])
    dist, idx = bundle["nn"].kneighbors(bundle["pre"].transform(X), n_neighbors=n_similar + 1)
    similar = [{"client_id": str(bundle["ids_train"][i]), "label": int(bundle["y_train"][i]), "dist": float(d)}
               for d, i in zip(dist[0], idx[0]) if str(bundle["ids_train"][i]) != exclude_id][:n_similar]
    return {"label": int(pipe.predict(X)[0]), "prob": prob, "similar": similar,
            "k": bundle["params"]["k"]}


def predict_client(bundles: dict, raw: dict, client_id: str | None = None) -> dict:
    """raw: dict kolom mentah CRM (kolom yang kosong boleh dihilangkan) -> prediksi semua target."""
    row = pd.DataFrame([{c: raw.get(c, np.nan) for c in crm_data.RAW_COLS}])
    feats = crm_data.engineer_features(row)
    return {t: predict_one(b, feats, exclude_id=client_id) for t, b in bundles.items()}
