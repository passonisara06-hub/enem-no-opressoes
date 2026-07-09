"""
Gera um PDF do notebook executado usando Chrome headless.
1. Constrói um HTML autocontido com Plotly.js embutido inline (sem CDN).
2. Deixa o Chrome renderizar (executa o JS do Plotly) e imprime em PDF.
"""
import json, html, subprocess, sys, time
from pathlib import Path
import nbformat
import markdown
import plotly.io as pio
from plotly.offline.offline import get_plotlyjs

NB_IN = Path("notebooks/01_analise_completa.executed.ipynb")
HTML_TMP = Path("notebooks/_for_pdf.html")
PDF_OUT = Path("notebooks/01_analise_completa.pdf")

nb = nbformat.read(NB_IN, as_version=4)

CSS = """
@page { size: A4; margin: 14mm 12mm; }
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;
  color:#1f2328;line-height:1.55;font-size:11pt}
h1{font-size:20pt;border-bottom:2px solid #d0d7de;padding-bottom:.2rem}
h2{font-size:15pt;border-bottom:1px solid #d0d7de;padding-bottom:.15rem;margin-top:1.4rem;page-break-after:avoid}
h3{font-size:12pt;margin-top:1rem;page-break-after:avoid}
blockquote{border-left:4px solid #d0d7de;margin:.8rem 0;padding:.3rem .9rem;background:#f6f8fa;color:#57606a}
pre{background:#f6f8fa;padding:.6rem .8rem;border-radius:6px;font-size:8.5pt;border:1px solid #d0d7de;
   white-space:pre-wrap;word-wrap:break-word}
code{background:#eff1f3;padding:.05rem .2rem;border-radius:3px;font-size:9pt}
pre code{background:none;padding:0}
table{border-collapse:collapse;width:100%;font-size:9pt;margin:.5rem 0}
th,td{border:1px solid #d0d7de;padding:.25rem .4rem;text-align:left}
th{background:#f6f8fa}
.cell{margin:.9rem 0;padding:.6rem .7rem;border:1px solid #e6e8eb;border-radius:8px;page-break-inside:avoid}
.cell-code{background:#fbfcfd}
.cell-code pre{margin:.1rem 0}
.cell-out{margin-top:.5rem;font-size:9pt}
.cell-out pre{margin:.15rem 0;background:#fafbfc}
.js-plotly-plot, .plotly{page-break-inside:avoid}
"""

plotly_js = get_plotlyjs()
parts = []
parts.append("<!DOCTYPE html><html lang='pt-br'><head><meta charset='utf-8'>"
             f"<title>O nó de opressões no ENEM 2025</title>"
             f"<style>{CSS}</style>"
             f"<script>{plotly_js}</script></head><body>")

plotly_count = 0
for cell in nb.cells:
    if cell.cell_type == "markdown":
        parts.append(markdown.markdown(cell.source, extensions=["tables", "fenced_code"]))
        continue
    if cell.cell_type != "code":
        continue
    parts.append("<div class='cell cell-code'>")
    parts.append(f"<pre><code>{html.escape(cell.source)}</code></pre>")
    for out in cell.get("outputs", []):
        otype = out.get("output_type")
        if otype == "stream":
            parts.append(f"<div class='cell-out'><pre>{html.escape(out.get('text',''))}</pre></div>")
        elif otype in ("execute_result", "display_data"):
            data = out.get("data", {})
            if "application/vnd.plotly.v1+json" in data:
                fig_json = data["application/vnd.plotly.v1+json"]
                plotly_count += 1
                div_id = f"plotly-div-{plotly_count}"
                try:
                    fig = pio.from_json(json.dumps(fig_json))
                    snippet = pio.to_html(fig, full_html=False, include_plotlyjs=False, div_id=div_id)
                except Exception as e:
                    snippet = f"<pre>[erro plotly: {e}]</pre>"
                parts.append(f"<div class='cell-out'>{snippet}</div>")
            elif "text/plain" in data:
                parts.append(f"<div class='cell-out'><pre>{html.escape(data['text/plain'])}</pre></div>")
            elif "image/png" in data:
                parts.append(f"<div class='cell-out'><img src='data:image/png;base64,{data['image/png']}'></div>")
        elif otype == "error":
            parts.append(f"<div class='cell-out'><pre style='color:#cf222e'>{html.escape(chr(10).join(out.get('traceback', [])))}</pre></div>")
    parts.append("</div>")
parts.append("</body></html>")

HTML_TMP.write_text("\n".join(parts), encoding="utf-8")
print(f"HTML temporário: {HTML_TMP} ({HTML_TMP.stat().st_size:,} bytes) — {plotly_count} figuras Plotly")

# Chrome headless -> PDF
chrome = "/usr/bin/google-chrome-stable"
url = "file://" + str(HTML_TMP.resolve())
cmd = [
    chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
    "--disable-dev-shm-usage", "--no-pdf-header-footer",
    "--run-all-compositor-stages-before-draw",
    "--virtual-time-budget=15000",
    f"--print-to-pdf={PDF_OUT.resolve()}", url,
]
print("Executando Chrome headless...")
r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
print("rc=", r.returncode)
if r.stderr:
    print("stderr:", r.stderr[-800:])
if PDF_OUT.exists():
    print(f"PDF gerado: {PDF_OUT} ({PDF_OUT.stat().st_size:,} bytes)")
else:
    print("PDF NÃO gerado"); sys.exit(1)