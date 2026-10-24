"""Experimentos A: margen de contexto, color HSV, kNN+LogReg. CV agrupada por md5; test no se toca."""
from __future__ import annotations
import csv, json, sys
from collections import Counter
from pathlib import Path
import numpy as np, torch
from PIL import Image
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.utils.class_weight import compute_sample_weight
from transformers import AutoModel
sys.path.insert(0, str(Path(__file__).parent))
from embed_train import AUG, BASE, CLASSES, MODELS, OUT_J, ROOT, embed
from cv_eval import knn_predict, per_class
E = ROOT / "outputs/classification/emb2"
NA = 24
def crops(margin, splits):
    rows = list(csv.DictReader((ROOT/"data/annotations/flowers.csv").open()))
    files = {r["md5"]: r["file"] for r in csv.DictReader((ROOT/"data/raw/labels_imagen.csv").open())}
    man = {r["flower_id"]: r for r in csv.DictReader((OUT_J/"manifest.csv").open())}
    cnt = Counter(); out = []
    cache = {}
    for r in rows:
        m = r["md5"]
        if r["annotatable"] != "1" or m not in {v["md5"] for v in man.values() if v["split"] in splits} : continue
        cnt[m] += 1; fid = f"{m[:8]}_{cnt[m]:02d}"
        if fid not in man or man[fid]["split"] not in splits: continue
        if m not in cache: cache = {m: Image.open(ROOT/"data/raw/images"/files[m]).convert("RGB")}
        img = cache[m]; W, H = img.size
        x, y, w, h = (float(r[k]) for k in "xywh")
        c = img.crop((round(max(0,(x-margin*w)*W)), round(max(0,(y-margin*h)*H)),
                      round(min(W,(x+w*(1+margin))*W)), round(min(H,(y+h*(1+margin))*H))))
        out.append((fid, c))
    return out
def hsv(im):
    a = np.asarray(im.convert("HSV").resize((64,64))).reshape(-1,3).astype(float)/255
    s = np.sin(2*np.pi*a[:,0]); c = np.cos(2*np.pi*a[:,0])
    return np.array([s.mean(), c.mean(), a[:,1].mean(), a[:,1].std(), a[:,2].mean(), a[:,2].std()])
def feats(margin, pool_ids, test_ids, model):
    f = E/f"m{margin}.npz"
    if f.exists(): return dict(np.load(f))
    cp = dict(crops(margin, ("train","val","test")))
    ip = [cp[i] for i in pool_ids]; it = [cp[i] for i in test_ids]
    torch.manual_seed(1)
    d = dict(base=embed(model, ip, BASE), test=embed(model, it, BASE),
             aug=np.stack([embed(model, ip, AUG) for _ in range(NA)], 1),
             col=np.stack([hsv(i) for i in ip]), colt=np.stack([hsv(i) for i in it]))
    np.savez(f, **d); return d
def build(idx, X, aug, y, ns, col=None, wc=0):
    def mk(e, i): return e if col is None else np.hstack([e, wc*np.repeat(col[i][None], len(e), 0)])
    xs=[mk(X[idx], idx) if col is None else np.hstack([X[idx], wc*col[idx]])]; ys=[y[idx]]
    for i in idx:
        n = ns if y[i]==2 else 8
        xs.append(mk(aug[i,:n], i)); ys.append(np.full(n, y[i]))
    return np.concatenate(xs), np.concatenate(ys)
def run(X, aug, y, groups, folds_all, mode, col=None, wc=0, C=10, k=5, ns=24, wk=0.5):
    reps=[]
    for folds in folds_all:
        oof=np.full(len(y),-1)
        for tr,va in folds:
            xtr,ytr=build(tr,X,aug,y,ns,col,wc)
            xva = X[va] if col is None else np.hstack([X[va], wc*col[va]])
            sw=np.ones(len(ytr))
            lr=LogisticRegression(C=C,max_iter=3000).fit(xtr,ytr)
            P=lr.predict_proba(xva)
            if mode=="knn+lr":
                d=np.maximum(1-xva@xtr.T,1e-9) if col is None else None
                xn=xtr[:,:X.shape[1]]; d=np.maximum(1-X[va]@xn.T,1e-9)
                idx=np.argsort(d,1)[:,:k]; V=np.zeros((len(va),3))
                for j in range(k): np.add.at(V,(np.arange(len(va)),ytr[idx[:,j]]),1/d[np.arange(len(va)),idx[:,j]])
                P=(1-wk)*P+wk*V/V.sum(1,keepdims=True)
            oof[va]=P.argmax(1)
        reps.append((per_class(y,oof),oof))
    f1=np.mean([r[0]["f1"] for r in reps],0); fm=np.mean([r[0]["f1_macro"] for r in reps])
    # precision apto media
    pa=[]
    for _,o in reps:
        t=((o==1)&(y==1)).sum(); pa.append(t/max(1,(o==1).sum()))
    # bootstrap IC rep0
    rng=np.random.default_rng(0); ug=np.unique(groups); o=reps[0][1]; b=[]
    for _ in range(300):
        ii=np.concatenate([np.where(groups==g)[0] for g in rng.choice(ug,len(ug))]); b.append(per_class(y[ii],o[ii])["f1_macro"])
    return dict(f1m=round(float(fm),3), ic=np.percentile(b,[2.5,97.5]).round(2).tolist(), f1=f1.round(2).tolist(), prec_apto=round(float(np.mean(pa)),2))
def main():
    torch.set_num_threads(10)
    man=list(csv.DictReader((OUT_J/"manifest.csv").open()))
    pool=[r for r in man if r["split"] in("train","val")]; test=[r for r in man if r["split"]=="test"]
    y=np.array([CLASSES.index(r["stage"]) for r in pool]); g=np.array([r["md5"] for r in pool])
    pid=[r["flower_id"] for r in pool]; tid=[r["flower_id"] for r in test]
    folds_all=[list(StratifiedGroupKFold(5,shuffle=True,random_state=s).split(pid,y,g)) for s in (0,1,2)]
    model=AutoModel.from_pretrained(MODELS["vit_s14"]).eval()
    res={}
    import time
    for m in (0.1,0.0,0.25):
        t=time.time(); d=feats(m,pid,tid,model); print("emb",m,round(time.time()-t),"s",flush=True)
        res[f"m{m}"]=run(d["base"],d["aug"],y,g,folds_all,"lr"); print(f"margen {m} LR:",res[f"m{m}"],flush=True)
        if m==0.1:
            col=d["col"]; mu,sd=col.mean(0),col.std(0)+1e-9; cn=(col-mu)/sd
            for wc in (0.05,0.1,0.2):
                res[f"m0.1+col{wc}"]=run(d["base"],d["aug"],y,g,folds_all,"lr",cn,wc); print("color",wc,res[f"m0.1+col{wc}"],flush=True)
            for wk in (0.3,0.5):
                res[f"m0.1+knn{wk}"]=run(d["base"],d["aug"],y,g,folds_all,"knn+lr",wk=wk); print("knn+lr",wk,res[f"m0.1+knn{wk}"],flush=True)
    (OUT_J/"improve_cv.json").write_text(json.dumps(res,indent=1))
main()
