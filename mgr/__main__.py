from mgr.sim import simulate
from mgr.subm import Code

res = simulate(players=[Code("A"), Code("B"), Code("C")], ranking=[("B", 4.3), ("C", 2.8), ("A", 0)])
print(res)