"""Task agent: one selection, many actions. Each task builds a plan from the
profile, the app shows it, and nothing runs until the person confirms. Steps
only run through the registry's actions (text, call), so a task can never do
something the registry does not allow."""
import time

from kinesis.agent.profile import contact


def _meds(p):
    m = (p.get("medications") or [{}])[0]
    return m.get("name", "my medication"), m.get("dose", ""), m.get("last_filled", "")


def plan_for(task, p):
    """Returns (title, steps). Each step: {what, detail, run: None | {action...}}."""
    me = p["name"]
    care = p["care_list"][0] if p.get("care_list") else None
    if task == "refill":
        name, dose, last = _meds(p)
        pharm = p.get("pharmacy", {})
        carer = contact(p, care)["name"] if care else "my caregiver"
        return "Refill my prescription", [
            {"what": "Find the prescription", "detail": f"{name} {dose}, last filled {last}".strip()},
            {"what": "Call the pharmacy", "detail": pharm.get("name", "Pharmacy"),
             "run": {"action": "call_number", "name": pharm.get("name", "Pharmacy"), "phone": pharm.get("phone"),
                     "say": f"Hello, this is an automated call for {p.get('full_name', me)}. Please refill {name} {dose} for pickup today."}},
            {"what": "Ask for pickup today", "detail": "Requested in the call"},
            {"what": f"Text {carer} to pick it up", "detail": f'"Can you pick up my {name} today?"',
             "run": {"action": "message", "contact": care, "text": f"Can you pick up my {name} at {pharm.get('name', 'the pharmacy')} today?"}},
        ]
    if task == "tell_family":
        fam = [c for c, v in p["contacts"].items() if v.get("relation") in ("mother", "father", "sister", "brother", "partner")]
        steps = [{"what": "Write the message", "detail": '"Good day today. Love you."'}]
        for c in fam:
            steps.append({"what": f"Send to {p['contacts'][c]['name']}", "detail": "Text message",
                          "run": {"action": "message", "contact": c, "text": f"Good day today. Love you. ({me}, sent with Kinesis)"}})
        return "Tell my family I'm okay", steps
    if task == "ride":
        return "Book a ride", [
            {"what": "Check my calendar", "detail": "Next appointment"},
            {"what": "Request an accessible van", "detail": "Paratransit request drafted"},
            {"what": "Confirm pickup", "detail": "Sent to my caregiver to confirm",
             "run": {"action": "message", "contact": care, "text": f"{me} needs a wheelchair van for the next appointment. Can you confirm the pickup?"}},
        ]
    if task == "groceries":
        return "Order groceries", [
            {"what": "Copy last week's order", "detail": "Saved list"},
            {"what": "Pick a delivery window", "detail": "Next available"},
            {"what": "Ask my caregiver to place it", "detail": "Text message",
             "run": {"action": "message", "contact": care, "text": f"{me} would like last week's grocery order again. Can you place it?"}},
        ]
    if task == "appointment":
        doc = contact(p, p["doctor"])
        return "Book an appointment", [
            {"what": "Find open times", "detail": doc["name"]},
            {"what": "Ask the clinic for the first morning slot", "detail": "Text message",
             "run": {"action": "message", "contact": p["doctor"], "text": f"Hello, this is {p.get('full_name', me)} using Kinesis. Could I book the first available morning appointment?"}},
        ]
    raise KeyError(f"unknown task '{task}'")


class TaskAgent:
    def __init__(self, profile, registry, emit):
        self.p = profile
        self.registry = registry
        self.emit = emit
        self.pending = {}

    def propose(self, task):
        title, steps = plan_for(task, self.p)
        pid = f"t-{task}-{int(time.time())}"
        self.pending[pid] = steps
        self.emit({"type": "plan", "id": pid, "task": task, "title": title,
                   "steps": [{"what": s["what"], "detail": s.get("detail")} for s in steps]})
        return pid

    def cancel(self, pid):
        self.pending.pop(pid, None)

    def run(self, pid):
        steps = self.pending.pop(pid, None)
        if not steps:
            return
        for i, s in enumerate(steps):
            self.emit({"type": "step", "id": pid, "index": i, "status": "running"})
            detail = s.get("detail")
            if s.get("run"):
                res = self.registry.execute(s["run"])
                if not res.get("ok", True):
                    detail = f"Did not go through: {res.get('error', 'unknown error')}"
                elif res.get("mode") == "dry":
                    detail = f"{detail} (practice mode, not sent)"
            time.sleep(0.9)
            self.emit({"type": "step", "id": pid, "index": i, "status": "done", "detail": detail})
