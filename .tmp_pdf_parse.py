from pathlib import Path
from pypdf import PdfReader
root = Path('d:/ResumeForge')
for rel in ['site/software/Ahmed_Resume.pdf','site/data-entry/Ahmed_Resume.pdf','site/production/Ahmed_Resume.pdf']:
    p = root / rel
    print('FILE', rel)
    reader = PdfReader(str(p))
    print('pages', len(reader.pages))
    for i, page in enumerate(reader.pages[:2], 1):
        text = page.extract_text() or ''
        print(i, repr(text[:200]))
    print()
