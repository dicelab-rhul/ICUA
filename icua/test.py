def t():
    yield 1

def s():
    yield 1,2

for a, *_ in t():
    print(a)

for a, *_ in s():
    print(a)