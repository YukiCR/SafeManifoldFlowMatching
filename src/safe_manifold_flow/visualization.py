"""Scientific plots of actual generated samples, not illustrative substitutes."""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import torch


def _sphere(axis):
    longitude, latitude = np.meshgrid(np.linspace(0, 2*np.pi, 48), np.linspace(0, np.pi, 30))
    axis.plot_surface(np.cos(longitude)*np.sin(latitude), np.sin(longitude)*np.sin(latitude),
                      np.cos(latitude), color="#bdbdbd", alpha=0.18, linewidth=0, shade=True,
                      zorder=0)
    axis.set(xlim=(-1.03,1.03), ylim=(-1.03,1.03), zlim=(-1.03,1.03))
    axis.set_box_aspect((1,1,1), zoom=1.45)
    axis.set_proj_type("ortho")
    axis.view_init(elev=90, azim=-90)
    axis.set_axis_off()


def plot_transport(study, output_dir, count=600):
    """Rows are validation/test conditioning windows; columns are generation times."""
    output_dir=Path(output_dir);output_dir.mkdir(parents=True,exist_ok=True)
    fig=plt.figure(figsize=(10.5,7.1), facecolor="white")
    banks={}
    for row, split in enumerate(["validation","test"]):
        bank=study.prepare_batch(split,seed=2026+row,count=count)
        flow=study.generate(bank["condition"],source=bank["noise"],snapshot_times=(0.,0.5,1.))
        banks[split]={"bank":bank,"flow":flow}
        for column,s in enumerate([0.,0.5,1.]):
            axis=fig.add_subplot(2,3,row*3+column+1,projection="3d",computed_zorder=False)
            _sphere(axis)
            for curve in study.points.numpy():
                axis.plot(*curve.T,color="#E69F00",linewidth=1.15,alpha=0.85,zorder=3)
            # Display the FIRST predicted position, with its joint chunk evolved by FM.
            cloud=flow["snapshots"][s][:,0].numpy()
            axis.scatter(*cloud.T,s=3.5,color="#0072B2",alpha=0.6,depthshade=False,zorder=4)
            if row==0:axis.set_title(f"Generation time s = {s:g}",fontsize=12,pad=0)
            if column==0:axis.text2D(-0.10,0.5,f"{split.capitalize()}-window\nconditions",transform=axis.transAxes,rotation=90,va="center",ha="center",fontsize=10)
    fig.legend(handles=[Line2D([0],[0],color="#E69F00",label="Embedded LShape recordings"),
                        Line2D([0],[0],marker=".",linestyle="none",color="#0072B2",label="Generated first positions")],
               loc="lower center",ncol=2,frameon=False,bbox_to_anchor=(0.5,0.035))
    fig.suptitle("Riemannian flow matching on S² — conditional transport",fontsize=15,y=0.98)
    fig.subplots_adjust(left=0.07,right=0.99,bottom=0.10,top=0.91,wspace=-0.06,hspace=-0.03)
    for extension in ["png","pdf"]:fig.savefig(output_dir/f"flow_transport.{extension}",dpi=220,facecolor="white")
    plt.close(fig)
    torch.save(banks,output_dir/"transport_samples.pt")
    (output_dir/"flow_transport_caption.md").write_text(
        "Orange: all seven embedded LShape recordings. Blue: first predicted positions from 600 conditional joint chunks. "
        "Columns show the SAME samples at generation times 0, 0.5 and 1. Rows use validation-window and test-window conditions, "
        "not RFMP versus SRFMP. Window splits overlap underlying recordings. Source noise is the approved wrapped Gaussian "
        "with tangent covariance 0.5 I; it is not narrowed for appearance. The embedding maps the recorded goal to the source pole. "
        "These density/transport plots do not establish autonomous motion quality, safety or held-out-recording generalization.\n")
    return output_dir/"flow_transport.png"


def plot_rollouts(study,positions,demo_ids,output_dir):
    output_dir=Path(output_dir)
    fig=plt.figure(figsize=(10,4.7),facecolor="white")
    axis=fig.add_subplot(1,2,1,projection="3d",computed_zorder=False);_sphere(axis)
    for curve in study.points.numpy():axis.plot(*curve.T,color="#E69F00",alpha=0.8,zorder=2)
    for curve in positions.numpy():axis.plot(*curve.T,color="#0072B2",alpha=0.25,linewidth=0.65,zorder=3)
    axis.set_title(f"Autonomous replanning: {len(positions)} attempts")
    loss_axis=fig.add_subplot(1,2,2)
    history=study.training_report["history"]
    loss_axis.plot([v["epoch"] for v in history],[v["train_loss"] for v in history],label="Training")
    loss_axis.plot([v["epoch"] for v in history],[v["validation_loss"] for v in history],label="Fixed-bank EMA validation")
    loss_axis.set(xlabel="Epoch",ylabel="Product-metric flow loss");loss_axis.legend(frameon=False)
    fig.tight_layout();fig.savefig(output_dir/"rollout_diagnostics.png",dpi=200);plt.close(fig)
