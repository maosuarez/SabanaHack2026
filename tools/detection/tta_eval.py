"""B: TTA (volteo, escalas) + fusión de cajas; umbral solo con las 9 imágenes de validación."""
from __future__ import annotations
import json, sys, time
from pathlib import Path
import numpy as np, torch
from PIL import Image
from transformers import RTDetrForObjectDetection
sys.path.insert(0, str(Path(__file__).parent))
from common import ROOT, OUT_DIR, load_gt, md5_to_file
from evaluate import evaluate, iou
from fit_and_eval import rtdetr_val_md5s
torch.set_num_threads(10)
det = RTDetrForObjectDetection.from_pretrained(ROOT/"outputs/rtdetr_final/checkpoint").eval()

@torch.no_grad()
def raw(img, size, flip):
    im = img.resize((size, size), Image.Resampling.BILINEAR)
    if flip: im = im.transpose(Image.FLIP_LEFT_RIGHT)
    x = torch.from_numpy(np.asarray(im, dtype=np.float32)/255).permute(2,0,1)[None]
    o = det(pixel_values=x); sc = o.logits[0].sigmoid().max(-1).values
    res = []
    for (cx,cy,w,h),s in zip(o.pred_boxes[0].tolist(), sc.tolist()):
        if s < 0.01: continue
        b=[max(0,cx-w/2),max(0,cy-h/2),min(1,cx+w/2),min(1,cy+h/2)]
        if flip: b=[1-b[2],b[1],1-b[0],b[3]]
        res.append((b,s))
    return res

def fuse(lists, thr_iou=0.55):
    n=len(lists); allb=sorted([(b,s) for l in lists for b,s in l], key=lambda t:-t[1]); cl=[]
    for b,s in allb:
        for c in cl:
            if iou(c["box"],b)>=thr_iou: c["m"].append((b,s)); w=np.array([x[1] for x in c["m"]]); c["box"]=list(np.average([x[0] for x in c["m"]],axis=0,weights=w)); break
        else: cl.append({"box":list(b),"m":[(b,s)]})
    out=[]
    for c in cl:
        # una sola contribución por variante no se puede distinguir aquí: tomar los n mejores scores
        sc=sorted([x[1] for x in c["m"]],reverse=True)[:n]
        out.append((tuple(c["box"]), sum(sc)/n))
    return out

CFG = {"base":[(640,0)], "flip":[(640,0),(640,1)], "flip+2esc":[(640,0),(640,1),(512,0),(768,0)],
       "flip+2esc+flip":[(640,0),(640,1),(512,0),(512,1),(768,0),(768,1)]}
files=md5_to_file(); gt=load_gt(); split=json.loads((OUT_DIR/"split.json").read_text())
val=rtdetr_val_md5s(); test=split["test"]
def preds(md5s, tag):
    cache={}; P={k:{} for k in CFG}
    for m in md5s:
        img=Image.open(files[m]).convert("RGB")
        for v in {v for c in CFG.values() for v in c}: cache[v]=raw(img,*v)
        for k,vs in CFG.items(): P[k][m]=fuse([cache[v] for v in vs]) if len(vs)>1 else cache[vs[0]]
    return P
def f1(r):
    p=r["tp"]/(r["tp"]+r["fp"]) if r["tp"]+r["fp"] else 0; rc=r["recall"]
    return 2*p*rc/(p+rc) if p+rc else 0
t=time.time(); PV=preds(val,"val"); print("val preds",round(time.time()-t),"s")
chosen={}
for k in CFG:
    scs=sorted({s for m in val for _,s in PV[k][m]})
    best=max(scs,key=lambda th:(f1(evaluate(gt,PV[k],val,th)),th))
    r=evaluate(gt,PV[k],val,best); b0=evaluate(gt,PV[k],val,0.152)
    chosen[k]=best
    print(f"{k:16} thr_val {best:.3f} rec {r['recall']:.2f} fp/img {r['fp_per_image']:.2f} F1 {f1(r):.3f} AP {r['ap']:.3f} | @0.152 rec {b0['recall']:.2f} fp {b0['fp_per_image']:.2f} F1 {f1(b0):.3f} (gt {r['gt']}, tp {r['tp']}, fp {r['fp']})")
json.dump(chosen,open(OUT_DIR/"tta_val_thresholds.json","w"))
if len(sys.argv)>1:
    k=sys.argv[1]; PT=preds(test,"test")
    for name,th in (("base@0.152",None),(k,chosen[k])):
        kk="base" if th is None else k; th=0.152 if th is None else th
        r=evaluate(gt,PT[kk],test,th); print("TEST",name,th,{a:round(b,3) for a,b in r.items()},"F1",round(f1(r),3))
