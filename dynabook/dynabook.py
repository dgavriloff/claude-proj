"""
DYNABOOK — After Alan Kay, "A Personal Computer for Children of All Ages" (1972)

Kay imagined a portable, reactive computing medium where:
- EVERYTHING is an object that can receive messages
- Objects are LIVE — you can inspect and modify them while they run
- The system is its own development environment
- Children can create simulations, not just consume media
- The medium itself is programmable, like paper but dynamic

"The best way to predict the future is to invent it."

Kay and the Learning Research Group at Xerox PARC built Smalltalk to
realize this vision. The iPad looks like a Dynabook but isn't one —
it's a consumption device. A real Dynabook is a *creation* device
where the boundary between using and programming dissolves.

This implementation provides:
- A live object system where objects communicate via messages
- Runtime inspection and modification of any object
- A simulation engine for modeling dynamic systems
- A "media" system where text, graphics, and code are all objects
  that can be composed and modified live
"""

import time
import hashlib
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass
class DynaObject:
    """A live object in the Dynabook — everything is one of these.

    In Smalltalk, "everything is an object." Numbers, strings, windows,
    the compiler itself — all objects, all inspectable, all modifiable.

    Each object has:
    - State (instance variables)
    - Behavior (methods that respond to messages)
    - Identity (unique, persistent)

    Objects communicate ONLY by sending messages. This is Kay's big
    insight — not inheritance, not classes, but MESSAGE PASSING.
    "I invented the term Object-Oriented, and I can tell you I did
    not have C++ in mind."
    """
    oid: str
    name: str
    kind: str  # what type of thing this represents
    state: dict = field(default_factory=dict)
    methods: dict = field(default_factory=dict)  # name -> source code string
    created_at: float = field(default_factory=time.time)
    alive: bool = True

    def receive(self, message: str, args: Optional[dict] = None) -> Any:
        """Receive a message — the ONLY way to interact with an object.

        Kay: "OOP to me means only messaging, local retention and
        protection and hiding of state-process, and extreme late-binding
        of all things."
        """
        args = args or {}

        # Check for a method
        if message in self.methods:
            return self._execute_method(message, args)

        # Built-in messages every object understands
        if message == "inspect":
            return self._inspect()
        elif message == "set":
            for k, v in args.items():
                self.state[k] = v
            return self.state
        elif message == "get":
            key = args.get("key", "")
            return self.state.get(key)
        elif message == "responds_to":
            return list(self.methods.keys()) + ["inspect", "set", "get", "responds_to", "kind"]
        elif message == "kind":
            return self.kind

        return f"Object '{self.name}' does not understand '{message}'"

    def _inspect(self) -> dict:
        """Inspect this object — see everything about it, live.

        In the Dynabook, there's no opacity. You can always open up
        any object and see how it works. This is how children learn —
        by taking things apart.
        """
        return {
            "oid": self.oid,
            "name": self.name,
            "kind": self.kind,
            "state": dict(self.state),
            "methods": list(self.methods.keys()),
            "alive": self.alive,
        }

    def _execute_method(self, message: str, args: dict) -> Any:
        """Execute a method defined on this object.

        Methods are stored as source code, compiled and run with
        access to self. This is live — you can redefine methods
        while the system is running.
        """
        source = self.methods[message]
        local_env = {"self_state": self.state, "args": args, "result": None}
        try:
            safe_builtins = {
                "str": str, "int": int, "float": float, "bool": bool,
                "len": len, "range": range, "enumerate": enumerate,
                "zip": zip, "map": map, "filter": filter, "sorted": sorted,
                "min": min, "max": max, "sum": sum, "abs": abs, "round": round,
                "list": list, "dict": dict, "set": set, "tuple": tuple,
                "True": True, "False": False, "None": None,
                "print": print, "isinstance": isinstance, "type": type,
            }
            exec(source, {"__builtins__": safe_builtins}, local_env)
            return local_env.get("result")
        except Exception as e:
            return f"Error in {self.name}.{message}: {e}"

    def add_method(self, name: str, source: str):
        """Add or replace a method on this object — LIVE.

        No recompile. No restart. Just change it and it changes.
        This is what Kay meant by a living system.
        """
        self.methods[name] = source


class Simulation:
    """A simulation — Kay's primary use case for the Dynabook.

    Kay envisioned children building simulations to understand the world:
    gravity, ecosystems, economics. Not by reading about them, but by
    building working models and playing with the parameters.
    """

    def __init__(self, name: str):
        self.name = name
        self.objects: dict[str, DynaObject] = {}
        self.tick_count: int = 0
        self.history: list[dict] = []
        self.rules: list[dict] = []  # {condition_src, action_src, description}

    def add_entity(self, obj: DynaObject):
        self.objects[obj.oid] = obj

    def add_rule(self, description: str, condition_src: str, action_src: str):
        """Add a simulation rule.

        Rules are evaluated every tick. If the condition is true,
        the action runs. Children can add, remove, and modify rules
        to see how systems behave differently.
        """
        self.rules.append({
            "description": description,
            "condition": condition_src,
            "action": action_src,
        })

    def tick(self) -> dict:
        """Advance the simulation by one step.

        Each tick: evaluate all rules against all objects,
        apply actions, record state.
        """
        self.tick_count += 1
        events = []

        for rule in self.rules:
            for oid, obj in list(self.objects.items()):
                if not obj.alive:
                    continue
                try:
                    env = {"state": obj.state, "result": False}
                    exec(rule["condition"], {"__builtins__": {}}, env)
                    if env.get("result"):
                        action_env = {"state": obj.state, "objects": {
                            o.name: o.state for o in self.objects.values()
                        }}
                        exec(rule["action"], {"__builtins__": {}}, action_env)
                        events.append({
                            "tick": self.tick_count,
                            "object": obj.name,
                            "rule": rule["description"],
                        })
                except Exception:
                    pass

        snapshot = {
            oid: dict(obj.state) for oid, obj in self.objects.items()
        }
        self.history.append({"tick": self.tick_count, "state": snapshot, "events": events})
        return {"tick": self.tick_count, "events": events}

    def run(self, ticks: int = 10) -> list[dict]:
        """Run the simulation for multiple ticks."""
        results = []
        for _ in range(ticks):
            results.append(self.tick())
        return results

    def rewind(self, to_tick: int) -> Optional[dict]:
        """Rewind the simulation to a previous state.

        Because we record everything, you can always go back.
        "What if gravity were stronger?" Rewind, change it, run again.
        """
        for record in self.history:
            if record["tick"] == to_tick:
                for oid, state in record["state"].items():
                    if oid in self.objects:
                        self.objects[oid].state = dict(state)
                self.tick_count = to_tick
                self.history = [h for h in self.history if h["tick"] <= to_tick]
                return record
        return None


class Dynabook:
    """The Dynabook environment — a personal, dynamic computing medium.

    Not an operating system. Not an application. A MEDIUM — like paper,
    but one where the marks you make can come alive and interact.
    """

    def __init__(self):
        self.objects: dict[str, DynaObject] = {}
        self.simulations: dict[str, Simulation] = {}
        self._message_log: list[dict] = []

    def create_object(self, name: str, kind: str, initial_state: Optional[dict] = None) -> DynaObject:
        """Create a new live object in the environment."""
        oid = hashlib.sha256(f"{name}:{kind}:{time.time()}".encode()).hexdigest()[:12]
        obj = DynaObject(oid=oid, name=name, kind=kind, state=initial_state or {})
        self.objects[oid] = obj
        return obj

    def send(self, oid: str, message: str, args: Optional[dict] = None) -> Any:
        """Send a message to an object — the universal interaction.

        Everything in the Dynabook happens through message sends.
        Opening a file? Message. Drawing a circle? Message.
        Running a simulation? Message. Redefining how addition works?
        Message.
        """
        obj = self.objects.get(oid)
        if not obj:
            return f"No object with id {oid}"

        result = obj.receive(message, args)
        self._message_log.append({
            "time": time.time(),
            "target": oid,
            "message": message,
            "args": args,
        })
        return result

    def create_simulation(self, name: str) -> Simulation:
        """Create a new simulation environment."""
        sim = Simulation(name)
        self.simulations[name] = sim
        return sim

    def inspect_all(self) -> list[dict]:
        """See everything alive in the environment.

        No hidden state. No mystery. Full transparency.
        """
        return [obj.receive("inspect") for obj in self.objects.values()]

    def find_by_kind(self, kind: str) -> list[DynaObject]:
        """Find all objects of a given kind."""
        return [o for o in self.objects.values() if o.kind == kind]

    def compose(self, name: str, *oids: str) -> DynaObject:
        """Compose multiple objects into a new one.

        Composition over inheritance. Kay's actual vision for OOP
        was about composing simple objects into complex behaviors
        through message passing, not about class hierarchies.
        """
        composite = self.create_object(name, "composite", {
            "components": list(oids),
        })

        # The composite can forward messages to its components
        for oid in oids:
            component = self.objects.get(oid)
            if component:
                for method_name in component.methods:
                    composite.add_method(
                        f"{component.name}_{method_name}",
                        component.methods[method_name]
                    )

        return composite

    def interaction_history(self, n: int = 20) -> list[dict]:
        """Review recent interactions — learn from how you've been thinking."""
        return self._message_log[-n:]
