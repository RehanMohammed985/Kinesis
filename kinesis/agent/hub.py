"""The hub: one object the core server talks to. Routes app messages to the
right agent, feeds live signal to the monitor, and sends results back."""
import threading

from kinesis.agent import profile as profiles
from kinesis.agent import report
from kinesis.agent.comms import CommunicationAgent
from kinesis.agent.monitor import DayLog, Monitor
from kinesis.agent.registry import Registry
from kinesis.agent.tasks import TaskAgent


class Hub:
    def __init__(self, emit):
        self.emit = emit
        self.p = profiles.load()
        self.log = DayLog()
        self.registry = Registry(self.p, emit)
        self.comms = CommunicationAgent(self.p)
        self.tasks = TaskAgent(self.p, self.registry, emit)
        self.monitor = Monitor(self.p, self.registry, emit, self.log)
        print(f"Profile: {self.p['name']} from {self.p['_source']}")

    def handle(self, msg):
        """Called from a worker thread for each message the app sends."""
        kind = msg.get("type")
        if kind == "action":
            a = msg.get("action")
            self.log.write("action", action=a)
            if a == "speak":
                self.comms.said(msg.get("text", ""))
            elif a == "task":
                self.tasks.propose(msg["task"])
                return
            elif a == "report":
                rep = report.build(self.p, self.log)
                self.emit(rep)
                from kinesis.agent import channels
                from kinesis.agent.profile import contact
                channels.send_file(contact(self.p, self.p["doctor"]), rep["file"], f"Kinesis daily report for {self.p['name']}: {rep['summary']}")
                return
            elif a == "note":
                self.log.write("note", text=msg.get("text", ""))
                return
            self.registry.execute(msg)
        elif kind == "confirm":
            threading.Thread(target=self.tasks.run, args=(msg["id"],), daemon=True).start()
        elif kind == "cancel":
            self.tasks.cancel(msg.get("id"))
        elif kind == "heard":
            self.emit({"type": "heard", "speaker": msg.get("speaker", "Someone nearby"), "text": msg["text"]})
            items, source = self.comms.replies(msg.get("speaker", "Someone nearby"), msg["text"], msg.get("setting", "home"))
            self.emit({"type": "replies", "items": items, "source": source})
        elif kind == "report_request":
            self.emit(report.build(self.p, self.log))
