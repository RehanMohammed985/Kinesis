"""Words: can the headset tell "yes" from "no"?

Proof of concept, tested honestly. A person is cued with a word, the word
disappears, and on a neutral "go" they say it in their head (imagine) or
silently mouth it (mouth). Each 2 s "go" window is one trial. Two
classifiers, both standard for this:
- covariance: the channels' covariance matrix, mapped to a flat space
  (Riemannian tangent space) + logistic regression
- bandpower: log power per channel in 5 bands + shrinkage LDA
Scored with stratified cross-validation and a permutation test, so a
result is only claimed when it beats shuffled labels.

Imagined speech from 6 dry electrodes is expected to sit near chance; the
published 64-channel results are modest (see scripts/eval_imagined_speech.py).
Mouthed words move the jaw and lips, which the temple and ear-clip pick up,
so "mouth" mode is the likely working version.
"""
import numpy as np
from scipy.signal import butter, resample_poly, sosfiltfilt

FS = 125
BANDS = [(1, 4), (4, 8), (8, 13), (13, 30), (30, 55)]
EPOCH_S = 2.0

# markers written by scripts/record_words.py
M_FIX, M_REST = 1, 30
M_CUE0, M_GO0 = 10, 20   # 10 + word index = cue shown, 20 + word index = go


def bandpass(x, lo, hi, fs=FS, order=4):
    hi = min(hi, 0.45 * fs)
    return sosfiltfilt(butter(order, [lo, hi], btype="band", fs=fs, output="sos"), x, axis=-1)


def to_fs(x, fs_in, fs_out=FS):
    if fs_in == fs_out:
        return x
    from fractions import Fraction
    f = Fraction(fs_out / fs_in).limit_denominator(100)
    return resample_poly(x, f.numerator, f.denominator, axis=-1)


def epochs_from_markers(eeg, markers, n_words, fs=FS, seconds=EPOCH_S, lo=1.0, hi=55.0, first_trial=0):
    """eeg: channels x samples, markers: per-sample marker row (0 = none).
    A GO window longer than 2 s is cut into 2 s pieces that share a trial id.
    Returns X (pieces x channels x samples), y (word index), trial ids, rest epochs."""
    x = bandpass(eeg - eeg.mean(axis=1, keepdims=True), lo, hi, fs)
    n = int(EPOCH_S * fs)
    pieces = max(1, int(seconds // EPOCH_S))
    X, y, g, R = [], [], [], []
    trial = first_trial
    for i in np.flatnonzero(markers):
        m = int(round(markers[i]))
        if M_GO0 <= m < M_GO0 + n_words and i + pieces * n <= x.shape[1]:
            for k in range(pieces):
                X.append(x[:, i + k * n:i + (k + 1) * n])
                y.append(m - M_GO0)
                g.append(trial)
            trial += 1
        elif m == M_REST and i + n <= x.shape[1]:
            R.append(x[:, i:i + n])
    return np.array(X), np.array(y), np.array(g), np.array(R)


def bandpower_features(X, fs=FS):
    out = []
    for lo, hi in BANDS:
        if lo >= 0.45 * fs:
            continue
        out.append(np.log(np.mean(bandpass(X, lo, hi, fs) ** 2, axis=-1) + 1e-12))
    return np.concatenate(out, axis=-1)


def classifiers():
    from pyriemann.estimation import Covariances
    from pyriemann.tangentspace import TangentSpace
    from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import FunctionTransformer, StandardScaler
    return {
        "covariance": make_pipeline(Covariances("oas"), TangentSpace(), LogisticRegression(C=1.0, max_iter=2000)),
        "bandpower": make_pipeline(FunctionTransformer(bandpower_features), StandardScaler(),
                                   LinearDiscriminantAnalysis(solver="lsqr", shrinkage="auto")),
    }


def evaluate(X, y, groups=None, n_perm=200, folds=5, seed=0):
    """Cross-validated accuracy for each classifier, with a permutation p-value.
    Pieces of the same trial (same group) are always kept on the same side of
    a split, and the permutation shuffles whole-trial labels."""
    from sklearn.base import clone
    from sklearn.model_selection import StratifiedGroupKFold
    groups = np.arange(len(y)) if groups is None else np.asarray(groups)
    ug = np.unique(groups)
    glab = np.array([y[groups == u][0] for u in ug])
    k = int(min(folds, np.bincount(glab).min()))
    if k < 2:
        return {name: {"accuracy": float("nan"), "chance": float("nan"), "p": None} for name in classifiers()}
    rng = np.random.default_rng(seed)

    def acc(clf, yy):
        # splits are re-drawn for each labelling so every fold stays balanced;
        # fixed splits with shuffled labels make chance look lower than it is
        hit = 0
        for tr, te in StratifiedGroupKFold(k, shuffle=True, random_state=seed).split(X, yy, groups):
            hit += int((clone(clf).fit(X[tr], yy[tr]).predict(X[te]) == yy[te]).sum())
        return hit / len(yy)

    out = {}
    for name, clf in classifiers().items():
        real = acc(clf, y)
        perm = []
        for _ in range(n_perm):
            shuffled = dict(zip(ug, rng.permutation(glab)))
            perm.append(acc(clf, np.array([shuffled[u] for u in groups])))
        p = (1 + sum(v >= real for v in perm)) / (1 + len(perm)) if perm else None
        out[name] = {"accuracy": real, "chance": float(np.mean(perm)) if perm else 1 / len(ug), "p": p, "trials": len(ug)}
    return out
