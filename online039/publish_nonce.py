from pathlib import Path
p=Path(__file__).with_name("publish_counter.json")
n=int(p.read_text()) if p.exists() else 0
assert n<98,"Use a new legitimate fresh URL series"
p.write_text(str(n+2)+"\n")
print(n+1)
