from mgr.simPrison import simulate
from mgr.subm import PrisonCode

res = simulate(players=[PrisonCode("A"), PrisonCode("B"), PrisonCode("C")], ranking=[("B", 4.3), ("C", 2.8), ("A", 0)])
print(res)