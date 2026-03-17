from mgr.sim import simulate
from mgr.code import Code

res = simulate(players=[Code("A"), Code("B"), Code("C")])
print(res)