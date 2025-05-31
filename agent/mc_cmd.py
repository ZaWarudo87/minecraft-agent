import json

def extra(ipt: list) -> str:
    ans = ""
    for i in ipt:
        if "text" in i:
            ans += i["text"]
        if "extra" in i:
            ans += extra(i["extra"])
    return ans

def decode(ipt: str) -> tuple[str, str]:
    ipt = json.loads(ipt)
    if "translate" in ipt and "with" in ipt:
        tp = ipt["translate"]
        if tp == "chat.type.text":
            pl = ipt["with"][1]
        else:
            pl = extra(ipt["with"][1:])
        return tp, pl
    else:
        return "error", "Can't decode this message."