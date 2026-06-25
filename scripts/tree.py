from pathlib import Path
root = Path(__file__).resolve().parents[1]
for p in sorted(root.rglob('*')):
    if any(part in {'.git','node_modules','.next','__pycache__'} for part in p.parts):
        continue
    print(p.relative_to(root))
