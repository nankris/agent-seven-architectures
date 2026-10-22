"""Scripted fake model for plumbing tests only (no results come from it).
It plays a naive ReAct agent that retries a tool after an ERROR, and answers structured calls correctly
by peeking at the task facts embedded in the prompt."""
import json
import re

import agents as A


class StubLLM:
    def __init__(self, usage, seed):
        self.usage, self.seed = usage, seed

    def _count(self):
        class U: prompt_tokens = 100; completion_tokens = 20
        self.usage.add(U)

    def chat(self, messages, tools):
        self._count()
        user = messages[1]["content"]
        cust = re.search(r"Customer (C-\d+)", user).group(1)
        oid = re.search(r"A-\d+", user).group(0)
        called = [tc["function"]["name"] for m in messages if m.get("tool_calls") for tc in m["tool_calls"]]
        last = messages[-1]
        def call(name, **a):
            return {"role": "assistant", "content": "", "tool_calls": [
                {"id": f"c{len(called)}", "type": "function", "function": {"name": name, "arguments": json.dumps(a)}}]}
        if last["role"] == "tool" and last["content"].startswith("ERROR"):
            prev = messages[-2]["tool_calls"][0]["function"]
            return call(prev["name"], **json.loads(prev["arguments"]))
        for name, a in [("get_order", {"order_id": oid}), ("get_refund_policy", {}), ("get_fraud_signals", {"customer": cust})]:
            if name not in called:
                return call(name, **a)
        if not any(c in called for c in ("issue_refund", "issue_credit", "create_ticket")):
            order = next(json.loads(m["content"]) for m in messages if m["role"] == "tool" and '"items"' in m["content"])
            if order["minutes_late"] > 45:
                return call("issue_refund", order_id=oid, amount=order["total"])
            return call("issue_credit", customer=cust, amount=5)
        if "notify_customer" not in called:
            return call("notify_customer", customer=cust, text="done")
        return {"role": "assistant", "content": "summary"}

    def structured(self, system, user, schema):
        self._count()
        if schema is A.Classification:
            oid = re.search(r"A-\d+", user)
            kind = "other" if re.search(r"rude|logging|lawn", user) else "refund_request"
            return A.Classification(kind=kind, order_id=oid.group(0) if oid else None)
        f = json.loads(user.split("\n\nYour previous")[0])
        o = f["order"]
        if f["fraud"]["score"] > 0.7:
            return A.Decision(action="refuse", amount=0, clause="§4", reason="fraud", customer_message="no")
        if o["minutes_late"] > 45:
            return A.Decision(action="refund", amount=o["total"], clause="§1", reason="late", customer_message="ok")
        return A.Decision(action="credit", amount=0, clause="§6", reason="late", customer_message="ok")
