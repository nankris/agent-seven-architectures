"""Figures for Exp 133 from results/summary.json (+ hypotheses table). 150 dpi PNGs in figures/."""
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

S = json.load(open("results/summary.json"))
T = {(r["arch"], r["condition"]): r for r in S["table"]}
ARCHS = ["V1_react", "V2_structured", "V3_parallel", "V4_checkpoint", "V5_approval", "V6_retries", "V7_full"]
LAB = ["V1 ReAct loop", "V2 + structured state", "V3 + parallel nodes", "V4 + checkpointing",
       "V5 + human approval", "V6 + retries + idem. keys", "V7 full combination"]
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
plt.rcParams.update({"font.size": 12, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
                     "ytick.color": INK2, "figure.facecolor": SURF, "axes.facecolor": SURF, "font.family": "DejaVu Sans"})
n = f"{S['n_tasks']} tasks x {len(S['seeds'])} seeds, Qwen3-8B on L4; bars = mean, whiskers = 95% bootstrap CI over tasks"


def style(ax):
    ax.grid(axis="x", color=GRID, lw=0.8); ax.set_axisbelow(True)
    for s in ("top", "right"): ax.spines[s].set_visible(False)


def grouped(metric, conds, colors, labels, fname, title, xlabel, pct=True):
    fig, ax = plt.subplots(figsize=(10, 6.2))
    y = np.arange(len(ARCHS)); h = 0.8 / len(conds)
    k = 100 if pct else 1
    for i, (c, col, lb) in enumerate(zip(conds, colors, labels)):
        m = np.array([T[(a, c)][metric] for a in ARCHS]) * k
        lo = np.array([T[(a, c)][metric + "_lo"] for a in ARCHS]) * k
        hi = np.array([T[(a, c)][metric + "_hi"] for a in ARCHS]) * k
        yy = y + (i - (len(conds) - 1) / 2) * h
        ax.barh(yy, m, height=h * 0.9, color=col, label=lb, edgecolor=SURF, linewidth=2)
        ax.errorbar(m, yy, xerr=[m - lo, hi - m], fmt="none", ecolor=INK2, elinewidth=1.2, capsize=3)
        for yv, mv, hv in zip(yy, m, hi):
            ax.text(hv + (1.5 if pct else 0.05 * max(m.max(), 1)), yv, f"{mv:.0f}%" if pct else f"{mv:.1f}",
                    va="center", fontsize=9.5, color=INK)
    ax.set_yticks(y); ax.set_yticklabels(LAB); ax.invert_yaxis()
    if pct: ax.set_xlim(0, 112)
    ax.set_xlabel(xlabel); style(ax)
    ax.set_title(title, loc="left", fontsize=14, fontweight="bold", color=INK)
    fig.text(0.01, 0.01, n, fontsize=9, color=INK2)
    ax.legend(frameon=False, loc="lower right")
    fig.tight_layout(rect=(0, 0.03, 1, 1)); fig.savefig(f"figures/{fname}", dpi=150); plt.close(fig)


grouped("dup", ["timeout", "crash"], [BLUE, ORANGE], ["API timeout (lost ack)", "process crash + resume"],
        "fig1_duplicates.png", "Runs that sent a refund, credit or ticket twice",
        "runs with a duplicate money side effect (%)")
grouped("success", ["clean", "timeout", "crash"], [BLUE, ORANGE, AQUA], ["no fault", "API timeout", "crash + resume"],
        "fig2_success.png", "Task success: exactly the right side effects, once", "runs with a correct final ledger (%)")

# fig3: cost when nothing fails, two panels (one scale each)
fig, axs = plt.subplots(1, 2, figsize=(11, 5.6), sharey=True)
for ax, met, lab, col in [(axs[0], "calls", "model calls per run", BLUE), (axs[1], "ptok", "prompt tokens per run", BLUE)]:
    m = np.array([T[(a, "clean")][met] for a in ARCHS])
    lo = np.array([T[(a, "clean")][met + "_lo"] for a in ARCHS]); hi = np.array([T[(a, "clean")][met + "_hi"] for a in ARCHS])
    y = np.arange(len(ARCHS))
    ax.barh(y, m, color=col, height=0.6)
    ax.errorbar(m, y, xerr=[m - lo, hi - m], fmt="none", ecolor=INK2, elinewidth=1.2, capsize=3)
    for yv, mv, hv in zip(y, m, hi):
        ax.text(hv + 0.02 * hi.max(), yv, f"{mv:,.1f}" if met == "calls" else f"{mv:,.0f}", va="center", fontsize=10, color=INK)
    ax.set_xlabel(lab); style(ax); ax.set_xlim(0, hi.max() * 1.25)
axs[0].set_yticks(np.arange(len(ARCHS))); axs[0].set_yticklabels(LAB); axs[0].invert_yaxis()
fig.suptitle("What each run costs when nothing fails", x=0.01, ha="left", fontsize=14, fontweight="bold", color=INK)
fig.text(0.01, 0.01, n.replace("bars", "no-fault runs; bars"), fontsize=9, color=INK2)
fig.tight_layout(rect=(0, 0.03, 1, 0.95)); fig.savefig("figures/fig3_cost.png", dpi=150); plt.close(fig)

# table.png: pre-registered hypotheses
H = S["hypotheses"]
rows = []
for k, h in H.items():
    unit = "s" if "latency" in h["metric"] else ("" if "calls," in h["metric"] or "minus V4" in h["metric"] else "")
    fmt = (lambda v: f"{v:.2f}") if ("latency" in h["metric"] or "V4" in h["metric"] and "calls" in h["metric"]) else (lambda v: f"{v:.1f}")
    rows.append([k, h["metric"], f"{fmt(h['est'])} [{fmt(h['lo'])}, {fmt(h['hi'])}]", str(h["margin"]), h["verdict"]])
fig, ax = plt.subplots(figsize=(13, 0.42 * len(rows) + 1.0)); ax.axis("off")
tb = ax.table(cellText=rows, colLabels=["#", "Metric (pre-registered)", "Estimate [95% CI]", "Margin", "Verdict"],
              bbox=[0, 0, 1, 0.92], cellLoc="left", colWidths=[0.05, 0.52, 0.2, 0.08, 0.15])
tb.auto_set_font_size(False); tb.set_fontsize(11); 
VC = {"PROVEN": "#d8f0e4", "DISPROVEN": "#fbe0d6", "INCONCLUSIVE": "#f3f2ee"}
for (r, c), cell in tb.get_celld().items():
    cell.set_edgecolor(GRID)
    if r == 0: cell.set_text_props(fontweight="bold"); cell.set_facecolor("#ecebe7")
    elif c == 4: cell.set_facecolor(VC.get(rows[r - 1][4], SURF))
ax.set_title(f"Exp 133: pre-registered hypotheses ({S['n_tasks']} fresh tasks x {len(S['seeds'])} seeds, 7 architectures x 3 conditions)",
             loc="left", fontsize=13, fontweight="bold")
fig.tight_layout(); fig.savefig("figures/table.png", dpi=150); plt.close(fig)

# table_archs.png: per-architecture results (rates in %, means per run)
rows = []
for a, lb in zip(ARCHS, LAB):
    c, t, k = T[(a, "clean")], T[(a, "timeout")], T[(a, "crash")]
    rows.append([lb, f"{c['success']*100:.0f}%", f"{t['success']*100:.0f}%", f"{k['success']*100:.0f}%",
                 f"{t['dup']*100:.0f}%", f"{k['dup']*100:.0f}%", f"{c['calls']:.1f}", f"{c['ptok']:,.0f}", f"{c['lat']:.1f}"])
fig, ax = plt.subplots(figsize=(14, 0.45 * len(rows) + 1.3)); ax.axis("off")
tb = ax.table(cellText=rows, colLabels=["Architecture", "Success\nno fault", "Success\ntimeout", "Success\ncrash",
              "Duplicate\ntimeout", "Duplicate\ncrash", "Model calls\n(no fault)", "Prompt tok\n(no fault)", "Latency s\n(no fault)"],
              bbox=[0, 0, 1, 0.9], cellLoc="center", colWidths=[0.22] + [0.0975] * 8)
tb.auto_set_font_size(False); tb.set_fontsize(11)
for (r, c), cell in tb.get_celld().items():
    cell.set_edgecolor(GRID)
    if r == 0: cell.set_text_props(fontweight="bold"); cell.set_facecolor("#ecebe7"); cell.set_height(cell.get_height() * 1.4)
    if c == 0 and r > 0: cell.set_text_props(ha="left")
ax.set_title(f"Exp 133: one refund agent, seven architectures ({S['n_tasks']} tasks x {len(S['seeds'])} seeds per cell, Qwen3-8B)",
             loc="left", fontsize=13, fontweight="bold")
fig.tight_layout(); fig.savefig("figures/table_archs.png", dpi=150); plt.close(fig)
print("figures written")
