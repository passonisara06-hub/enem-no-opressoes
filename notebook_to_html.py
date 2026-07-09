"""
Gera um HTML autocontido a partir do notebook executado,
embutindo os gráficos Plotly como figuras interativas (Plotly.js via CDN).
"""
import json
import html
from pathlib import Path
import nbformat
import markdown
import plotly.io as pio

NB_IN = Path("notebooks/01_analise_completa.executed.ipynb")
HTML_OUT = Path("notebooks/01_analise_completa.html")

nb = nbformat.read(NB_IN, as_version=4)

PLOTLY_CDN = "https://cdn.plot.ly/plotly-2.35.2.min.js"

CSS = """
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;
  max-width:1000px;margin:2rem auto;padding:0 1.5rem;color:#1f2328;line-height:1.6}
h1{font-size:1.9rem;border-bottom:2px solid #d0d7de;padding-bottom:.3rem}
h2{font-size:1.5rem;border-bottom:1px solid #d0d7de;padding-bottom:.2rem;margin-top:2.2rem}
h3{font-size:1.2rem;margin-top:1.6rem}
blockquote{border-left:4px solid #d0d7de;margin:1rem 0;padding:.4rem 1rem;background:#f6f8fa;color:#57606a}
pre{background:#f6f8fa;padding:.9rem 1.1rem;border-radius:8px;overflow:auto;font-size:.85rem;border:1px solid #d0d7de}
code{background:#eff1f3;padding:.1rem .3rem;border-radius:4px;font-size:.85rem}
pre code{background:none;padding:0}
.cell{margin:1.6rem 0;padding:1rem 1.1rem;border:1px solid #e6e8eb;border-radius:10px}
.cell-code{background:#fbfcfd}
.cell-out{margin-top:.7rem;font-size:.88rem}
.cell-out pre{margin:.2rem 0}
hr{border:none;border-top:1px solid #d0d7de;margin:2rem 0}
"""

parts = []
parts.append(f"<!DOCTYPE html><html lang='pt-br'><head><meta charset='utf-8'>"
             f"<meta name='viewport' content='width=device-width, initial-scale=1'>"
             f"<title>O nó de opressões no ENEM 2025</title>"
             f"<style>{CSS}</style>"
             f"<script src='{PLOTLY_CDN}'></script></head><body>")

plotly_count = 0

for cell in nb.cells:
    if cell.cell_type == "markdown":
        parts.append(markdown.markdown(cell.source, extensions=["tables", "fenced_code"]))
        continue

    if cell.cell_type != "code":
        continue

    # code cell: show source + outputs
    parts.append(f"<div class='cell cell-code'>")
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
                    snippet = pio.to_html(fig, full_html=False, include_plotlyjs=False,
                                          div_id=div_id)
                except Exception as e:
                    snippet = f"<pre>[erro ao renderizar plotly: {e}]</pre>"
                parts.append(f"<div class='cell-out'>{snippet}</div>")
            elif "text/plain" in data:
                parts.append(f"<div class='cell-out'><pre>{html.escape(data['text/plain'])}</pre></div>")
            elif "image/png" in data:
                parts.append(f"<div class='cell-out'><img src='data:image/png;base64,{data['image/png']}'></div>")
        elif otype == "error":
            parts.append(f"<div class='cell-out'><pre style='color:#cf222e'>{html.escape('\\n'.join(out.get('traceback', [])))}</pre></div>")

    parts.append("</div>")

parts.append("</body></html>")

HTML_OUT.write_text("\n".join(parts), encoding="utf-8")
print(f"HTML escrito: {HTML_OUT} ({HTML_OUT.stat().st_size:,} bytes)")
print(f"Figuras Plotly embutidas: {plotly_count}")