from typing import Any, Dict


def parse_symbol_qty(list) -> Dict[str, Any]:
    res = {}
    for item in list:
        res[item[0]] = {
            "min_qty": item[1][0],
            "max_qty": item[1][1],
        }
    return res
