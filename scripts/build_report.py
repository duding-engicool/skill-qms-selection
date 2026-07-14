#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QMS 系统选型评估报告生成器
读入结构化结果 JSON，生成 MD 文档 + 网页版 HTML（双版）。主色 #C8102E。
评分方法：各维度 1-5 分，加权总分 = Σ(权重 × 分值)，权重合计须为 1。

用法：
  python build_report.py --input result.json --md-out report.md --html-out report.html
  python build_report.py --demo            # 使用内置小样本

输入 JSON 结构：
{
  "title":"QMS 系统选型评估",
  "requirements":"业务需求摘要",
  "compliance":["IATF 16949","ISO 9001"],
  "dimensions":[{"name":"功能覆盖","weight":0.20},{"name":"合规匹配","weight":0.15}],
  "candidates":[
    {"name":"系统A","scores":{"功能覆盖":4,"合规匹配":5},"tco":"待企业补充","note":"..."}
  ],
  "recommendation":"推荐摘要"
}
"""
import argparse
import json
import sys
import html
from datetime import datetime

PRIMARY = "#C8102E"


def esc(s):
    return html.escape(str(s), quote=True)


def load_result(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def compute(dims, cands):
    """返回 {candidate_name: total}，并校验权重合计。"""
    total_w = sum(d.get("weight", 0) for d in dims)
    normalized = total_w not in (0, 1)
    results = {}
    for c in cands:
        sc = c.get("scores", {}) or {}
        tot = 0.0
        for d in dims:
            w = d.get("weight", 0)
            v = sc.get(d.get("name", ""), 0) or 0
            tot += w * v
        # 若权重合计不为 1，归一到 5 分制
        if normalized:
            tot = tot / total_w if total_w else 0
        results[c.get("name", "")] = round(tot, 2)
    return results, normalized


def build_md(r):
    dims = r.get("dimensions", []) or []
    cands = r.get("candidates", []) or []
    totals, norm = compute(dims, cands)
    L = []
    L.append(f"# {r.get('title','QMS 选型评估')}\n")
    L.append("## 一、需求与合规框架\n")
    L.append(f"- 业务需求：{r.get('requirements','待企业补充')}")
    L.append(f"- 合规框架：{', '.join(r.get('compliance',[]) or []) or '待企业补充'}")
    if norm:
        L.append(f"- 权重合计校验：原权重合计≠1，已归一化到 5 分制。")
    L.append("")
    L.append("## 二、评分维度与权重\n")
    L.append("| 维度 | 权重 |")
    L.append("|------|------|")
    for d in dims:
        L.append(f"| {d.get('name','')} | {d.get('weight','待企业补充')} |")
    L.append("")
    L.append("## 三、选型评估矩阵（1-5 分）\n")
    header = "| 候选系统 | " + " | ".join(d.get("name", "") for d in dims) + " | 加权总分 | TCO |"
    L.append(header)
    L.append("|" + "---|" * (len(dims) + 3))
    for c in cands:
        sc = c.get("scores", {}) or {}
        cells = " | ".join(str(sc.get(d.get("name", ""), "—")) for d in dims)
        L.append(f"| {c.get('name','')} | {cells} | {totals.get(c.get('name',''),'—')} | {c.get('tco','待企业补充')} |")
    L.append("")
    L.append("## 四、推荐结论\n")
    L.append(r.get("recommendation", "（待企业补充）"))
    L.append("")
    L.append(f"> 报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')} ｜ 主色 {PRIMARY}")
    return "\n".join(L)


CSS = """
:root{--primary:#C8102E;--bg:#f8fafc;--card:#ffffff;--ink:#1e293b;--muted:#64748b;--line:#e2e8f0}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,"Segoe UI",Roboto,"PingFang SC","Microsoft YaHei",sans-serif;background:var(--bg);color:var(--ink);line-height:1.7;padding:32px}
.wrap{max-width:1160px;margin:0 auto}
header{text-align:center;padding:28px 0 18px;border-bottom:3px solid var(--primary);margin-bottom:28px}
header h1{font-size:26px;letter-spacing:1px;color:var(--primary)}
header .meta{color:var(--muted);font-size:14px;margin-top:10px}
.sec{background:var(--card);border-radius:14px;padding:24px;box-shadow:0 4px 16px rgba(0,0,0,.06);margin-bottom:28px}
.sec h2{font-size:21px;margin-bottom:16px;border-left:5px solid var(--primary);padding-left:12px}
table{width:100%;border-collapse:collapse;font-size:14px}
th,td{border:1px solid var(--line);padding:8px 10px;text-align:center}
th{background:#fef2f2;color:var(--primary)}
td.name{text-align:left;font-weight:700}
tr.win td{background:#fef2f2}
.rec{font-size:15px;background:#fef2f2;border-left:4px solid var(--primary);padding:12px 16px;border-radius:8px}
footer{text-align:center;color:var(--muted);font-size:12px;margin-top:20px}
"""


def build_html(r):
    dims = r.get("dimensions", []) or []
    cands = r.get("candidates", []) or []
    totals, norm = compute(dims, cands)
    best = max(totals, key=totals.get) if totals else ""

    head = "".join(f"<th>{esc(d.get('name',''))}</th>" for d in dims)
    wrow = "<tr><td class='name'>权重</td>" + "".join(f"<td>{esc(d.get('weight',''))}</td>" for d in dims) + "<td>—</td><td>—</td></tr>"
    rows = [wrow]
    for c in cands:
        sc = c.get("scores", {}) or {}
        cells = "".join(f"<td>{esc(sc.get(d.get('name',''),'—'))}</td>" for d in dims)
        is_win = " class='win'" if c.get("name", "") == best else ""
        rows.append(
            f"<tr{is_win}><td class='name'>{esc(c.get('name',''))}</td>{cells}"
            f"<td><b>{totals.get(c.get('name',''),'—')}</b></td><td>{esc(c.get('tco','待企业补充'))}</td></tr>"
        )
    if not cands:
        rows.append('<tr><td colspan="%d" style="color:#64748b">（暂无候选系统，待企业补充）</td></tr>' % (len(dims) + 3))
    matrix_html = (
        "<table><tr><th>候选系统</th>" + head + "<th>加权总分</th><th>TCO</th></tr>"
        + "".join(rows) + "</table>"
    )

    dim_html = "".join(f"<div>• {esc(d.get('name',''))}：权重 {esc(d.get('weight',''))}</div>" for d in dims) or "<div>待企业补充</div>"

    note = "（注：原权重合计≠1，已归一化到 5 分制）" if norm else ""

    return (
        "<!DOCTYPE html><html lang='zh-CN'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>{esc(r.get('title','QMS 选型评估'))}</title>"
        f"<style>{CSS}</style></head><body><div class='wrap'>"
        f"<header><h1>{esc(r.get('title','QMS 选型评估'))}</h1>"
        f"<div class='meta'>合规框架：{esc(', '.join(r.get('compliance',[]) or []) or '待企业补充')} ｜ "
        f"候选数：{len(cands)} {esc(note)}</div></header>"
        "<section class='sec'><h2>需求与评分维度</h2>"
        f"<div class='kpi'><b>业务需求：</b>{esc(r.get('requirements','待企业补充'))}</div>{dim_html}</section>"
        "<section class='sec'><h2>选型评估矩阵（1-5 分）</h2>" + matrix_html + "</section>"
        f"<section class='sec'><h2>推荐结论</h2><div class='rec'>{esc(r.get('recommendation','（待企业补充）'))}</div></section>"
        f"<footer>本报告由 QMS 系统选型评估 生成 · {datetime.now().strftime('%Y-%m-%d %H:%M')} · 主色 {PRIMARY}</footer>"
        "</div></body></html>"
    )


SAMPLE = {
    "title": "QMS 系统选型评估（演示样本）",
    "requirements": "汽车行业 Tier1，需覆盖文档/培训/内审/NC-CAPA/供应商/测量，支持 IATF 16949 与 ISO 9001",
    "compliance": ["IATF 16949", "ISO 9001"],
    "dimensions": [
        {"name": "功能覆盖", "weight": 0.20},
        {"name": "合规匹配", "weight": 0.15},
        {"name": "技术架构与集成", "weight": 0.15},
        {"name": "易用性", "weight": 0.10},
        {"name": "实施与服务", "weight": 0.15},
        {"name": "TCO", "weight": 0.15},
        {"name": "可扩展性", "weight": 0.10},
    ],
    "candidates": [
        {"name": "系统A（行业云）", "scores": {"功能覆盖": 5, "合规匹配": 5, "技术架构与集成": 4, "易用性": 4, "实施与服务": 4, "TCO": 4, "可扩展性": 4},
         "tco": "待企业补充", "note": "行业贴合度高，订阅制"},
        {"name": "系统B（通用本地）", "scores": {"功能覆盖": 4, "合规匹配": 4, "技术架构与集成": 3, "易用性": 3, "实施与服务": 4, "TCO": 3, "可扩展性": 5},
         "tco": "待企业补充", "note": "可二次开发强，实施周期长"},
        {"name": "系统C（轻量SaaS）", "scores": {"功能覆盖": 3, "合规匹配": 3, "技术架构与集成": 3, "易用性": 5, "实施与服务": 3, "TCO": 5, "可扩展性": 2},
         "tco": "待企业补充", "note": "易用便宜，扩展弱"},
    ],
    "recommendation": "综合加权评分：系统A 居首，行业合规贴合且 TCO 可控，建议进入商务谈判短名单；系统B 适合强定制需求可备选。具体以 TCO 报价与 POC 验证为准（待企业补充）。"
}


def main():
    ap = argparse.ArgumentParser(description="QMS 选型评估报告生成器")
    ap.add_argument("--input", help="结构化结果 JSON 路径")
    ap.add_argument("--md-out", default="demo_qms.md", help="输出 MD 路径")
    ap.add_argument("--html-out", default="demo_qms.html", help="输出 HTML 路径")
    ap.add_argument("--demo", action="store_true", help="使用内置小样本生成演示报告")
    args = ap.parse_args()

    if args.demo:
        r = SAMPLE
    elif args.input:
        try:
            r = load_result(args.input)
        except Exception as e:
            sys.stderr.write(f"读取输入失败：{e}\n")
            sys.exit(1)
    else:
        sys.stderr.write("请使用 --input <json> 或 --demo。\n")
        sys.exit(1)

    with open(args.md_out, "w", encoding="utf-8") as f:
        f.write(build_md(r))
    sys.stderr.write(f"MD 已生成：{args.md_out}\n")
    with open(args.html_out, "w", encoding="utf-8") as f:
        f.write(build_html(r))
    sys.stderr.write(f"HTML 已生成：{args.html_out}\n")


if __name__ == "__main__":
    main()
