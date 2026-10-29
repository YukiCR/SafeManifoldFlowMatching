"""Capture measured Phase 1 artifacts; run only after the study finishes."""
from pathlib import Path
import hashlib
import json
import platform
import os
os.environ.setdefault("MPLCONFIGDIR", str(Path("runs/phase1-context-expanded/matplotlib-cache").resolve()))
import subprocess
import sys
import numpy as np
import scipy
import torch
import matplotlib
from safe_manifold_flow.study import Phase1Study

root=Path.cwd()
run=root/'runs/phase1-context-expanded'
training=json.loads((run/'training.json').read_text())
evaluation=json.loads((run/'evaluation.json').read_text())
manifest=json.loads((run/'manifest.json').read_text())
study=Phase1Study.from_mat(root/'data/raw/LShape.mat').load_checkpoint(run/'best.pt')
torch.set_num_threads(2)
# Real checkpoint reload, source-bank generation and metric computations must agree.
saved=torch.load(run/'transport_samples.pt',weights_only=True)
max_reload_delta=0.
max_tangency=0.
max_norm=0.
with torch.no_grad():
    for split,entry in saved.items():
        bank,flow=entry['bank'],entry['flow']
        regenerated=study.generate(bank['condition'],source=bank['noise'])
        max_reload_delta=max(max_reload_delta,float((regenerated-flow['positions']).abs().max()))
        for s,points in flow['snapshots'].items():
            v=study.model(torch.tensor(s),points,bank['condition'].float())
            max_tangency=max(max_tangency,float((v*points).sum(-1).abs().max()))
            max_norm=max(max_norm,float((points.norm(dim=-1)-1).abs().max()))
    rollouts=torch.load(run/'rollouts.pt',weights_only=True)
    checked=study.evaluate_rollouts(rollouts['positions'],[d for d in range(7) for _ in range(5)],rollouts['seeds'])
assert checked['rollouts']==evaluation['rollouts'], 'Saved rollout scores differ after checkpoint reload'
assert max_reload_delta==0, 'Reload changed generated outputs'

files=['best.pt','banks.pt','training_pairs.pt','training.json','evaluation.json','rollouts.pt','transport_samples.pt','flow_transport.png','flow_transport.pdf','flow_transport_caption.md','rollout_diagnostics.png','manifest.json']
artifacts={f:hashlib.sha256((run/f).read_bytes()).hexdigest() for f in files}
split_indices={k:v.tolist() for k,v in study.splits.items()}
canonical=json.dumps(split_indices,sort_keys=True,separators=(',',':')).encode()
valid=[r for r in evaluation['rollouts'] if r['valid']]
metrics={key:{'mean':float(np.mean([r[key] for r in valid])),'min':float(min(r[key] for r in valid)),'max':float(max(r[key] for r in valid))} for key in ['goal_deg','dtw_deg','max_jump_deg','norm_error']}
failed={}
first=root/'runs/phase1-baseline'
if first.exists():
    t=json.loads((first/'training.json').read_text());e=json.loads((first/'evaluation.json').read_text())
    failed={'run':'runs/phase1-baseline','best_validation':t['best_validation'],'test_loss':t['test_loss'],'optimizer_steps':1800,'success_count':e['success_count'],'attempts':e['attempts'],'checkpoint_sha256':hashlib.sha256((first/'best.pt').read_bytes()).hexdigest()}
summary={
 'run':'runs/phase1-context-expanded','source_url':'https://raw.githubusercontent.com/epfl-lasa/LASAHandwritingDataset/master/DataSet/LShape.mat',
 'source_sha256':study.source_hash,'source_bytes':(root/'data/raw/LShape.mat').stat().st_size,
 'code_commit':manifest['git_commit'],'code_sha256':manifest['code_sha256'],
 'environment':{'python':platform.python_version(),'torch':torch.__version__,'numpy':np.__version__,'scipy':scipy.__version__,'matplotlib':matplotlib.__version__,'device':'cpu','threads':2,'cuda_available':torch.cuda.is_available()},
 'training':{k:v for k,v in training.items() if k!='history'},
 'configuration':{'embedding_scale':study.scale,'embedding_training_max_angle_deg':60,'split_counts':{k:len(v) for k,v in study.splits.items()},'split_indices_sha256':hashlib.sha256(canonical).hexdigest(),'split_indices':split_indices,'prior_tangent_covariance':0.5,'horizon':8,'execute':4,'integration_steps':100,'learning_rate':0.0001,'ema_decay':0.999,'batch_size':128,'hidden_layers':5,'width':64,'bootstrap_positions':2,'rollout_length':200,'rollout_seeds':[0,1,2,3,4]},
 'evaluation':{k:v for k,v in evaluation.items() if k!='rollouts'},'metric_statistics':metrics,
 'diagnostics':{'checkpoint_reload_max_abs_delta':max_reload_delta,'snapshot_max_tangency_residual':max_tangency,'snapshot_max_unit_norm_residual':max_norm,'saved_rollout_metrics_reproduced':True},
 'artifacts_sha256':artifacts,'preserved_failed_run':failed,
 'limitations':['Window partitions overlap recordings; no held-out-recording generalization claim.','35 attempts use only seven recorded bootstrap pairs.','Phase 1 has no safety filter, physical dynamics or hardware experiment.','Explicit paper-gap conventions are listed in the approved specification.','Transport figure rows represent validation/test conditioning, not RFMP/SRFMP.']}
folder=root/'docs/results';folder.mkdir(exist_ok=True)
(folder/'phase1_baseline.json').write_text(json.dumps(summary,indent=2)+'\n')
(folder/'phase1_rollouts.json').write_text(json.dumps(evaluation,indent=2)+'\n')
print(json.dumps({k:summary[k] for k in ['training','evaluation','metric_statistics','diagnostics']},indent=2))
