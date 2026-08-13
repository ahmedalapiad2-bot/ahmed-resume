from pathlib import Path
import importlib.util
root = Path('d:/ResumeForge')
for rel in ['site/software/Ahmed_Resume.pdf','site/data-entry/Ahmed_Resume.pdf','site/production/Ahmed_Resume.pdf','generator/output/Ahmed_Resume.pdf','deploy/Ahmed_Resume.pdf']:
    p = root / rel
    print('FILE', rel)
    print('exists', p.exists(), 'size', p.stat().st_size if p.exists() else None)
    if p.exists():
        data = p.read_bytes()[:64]
        print('bytes_head', data)
        print('has_pdf_header', data.startswith(b'%PDF'))
        text = data.decode('latin1', 'ignore')
        print('header_text', text)
        for mod_name in ['pypdf','PyPDF2','fitz']:
            spec = importlib.util.find_spec(mod_name)
            print(mod_name, 'available', bool(spec))
        print()
