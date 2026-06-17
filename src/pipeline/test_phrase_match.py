from src.pipeline.classificar_noticias import contains_exact_phrase

samples = [
    "Este texto fala de Segurança Presente no Rio.",
    "Este texto fala de seguranca presente no Rio.",
    "Este texto fala de SEGURANÇA PRESENTE no Rio.",
    "Este texto fala de SEGURANCA PRESENTE no Rio.",
    "Este texto fala de segurança e presente no Rio.",
]

for s in samples:
    rec = {"title": s, "summaryPreview": "", "rawText": ""}
    print(s, contains_exact_phrase(rec))
