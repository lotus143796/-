import json
from datetime import datetime

def generate_html_report(report_data: dict, output_path: str = "report.html"):
    html = f"""
    <html><head><title>Code Review Report</title></head>
    <body><h1>审查报告</h1><pre>{json.dumps(report_data, indent=2)}</pre></body>
    </html>
    """
    with open(output_path, "w") as f:
        f.write(html)
    return output_path