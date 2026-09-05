"""The four fixed annotator pools (spec section 3) and the fixed condition
order used throughout this module. Order matters for the grid's columns and
for canonicalizing collapse pairs (e.g. "bare=ma" not "ma=bare"); it does
not affect the majority-vote math itself.
"""

POOLS = {
    "core3": ["Media", "Materials", "EngLit"],
    "econ": ["Media", "Materials", "EngLit", "Econ"],
    "bwl": ["Media", "Materials", "EngLit", "BWL"],
    "all5": ["Media", "Materials", "EngLit", "Econ", "BWL"],
}

CONDITIONS = ("bare", "ba", "ma")
