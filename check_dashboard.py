from streamlit.testing.v1 import AppTest

at = AppTest.from_file("app/dashboard.py", default_timeout=120)
at.run()
print("RUN HEADLESS OK")
print("exceptions:", at.exception)
if at.exception:
    print("---- exception details ----")
    print(at.exception)
else:
    print("Nenhuma exceção. Elementos por tipo:")
    from collections import Counter
    c = Counter()
    for el in at:
        c[type(el).__name__] += 1
    print(dict(c))
    # títulos / textos visíveis para confirmar que renderizou
    for h in at.header:
        print("H:", h.value)
    for t in at.title:
        print("T:", t.value)