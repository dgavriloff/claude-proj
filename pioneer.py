"""
PIONEER — The Unified System

What if all these ideas had been developed together instead of in isolation?
What if Bush's trails connected Nelson's documents which were structured
by Engelbart's outlines, populated by Kay's live objects, navigated through
Licklider's symbiotic thinking, drawn with Sutherland's constraints,
reasoned about with Hewitt's planner, explored through Papert's turtles,
and processed with Newell & Simon's list primitives?

This module wires them all together into a single coherent environment
that demonstrates what personal computing could have been.
"""

import json
import time
from pathlib import Path

from memex import Memex, Span, Trail
from xanadu import Xanadu
from nls import NLS, ViewSpec, ViewMode
from dynabook import Dynabook, DynaObject, Simulation
from symbiosis import SymbioticSession, IntergalacticNetwork


class Pioneer:
    """The unified environment — all systems working in concert.

    This is not how history went. But it's how it could have gone.
    """

    def __init__(self, storage_dir: str = ".pioneer"):
        self.memex = Memex(storage_dir=f"{storage_dir}/memex")
        self.xanadu = Xanadu()
        self.nls = NLS()
        self.dynabook = Dynabook()
        self.network = IntergalacticNetwork()
        self.storage_dir = Path(storage_dir)
        self._event_log = []

    def _log(self, system: str, action: str, detail: str = ""):
        self._event_log.append({
            "time": time.time(),
            "system": system,
            "action": action,
            "detail": detail,
        })

    # ---- Cross-system operations ----

    def think_about(self, topic: str, thinker: str = "human") -> dict:
        """Start a thinking session that spans all systems.

        Creates:
        - A Licklider symbiotic session for structured thinking
        - A Memex trail to record the journey
        - An NLS outline to structure emerging thoughts
        - A Xanadu document to hold the synthesis
        """
        session = self.network.create_session(topic, thinker)
        trail = self.memex.create_trail(f"Thinking: {topic}", thinker)
        root = self.nls.create_statement(topic, thinker, labels=["topic"])

        xdoc = self.xanadu.create_document(
            title=f"Synthesis: {topic}",
            author=thinker,
            content=f"# {topic}\n\nThinking in progress...\n",
        )

        self._log("pioneer", "think_about", topic)

        return {
            "session_id": session.session_id,
            "trail_name": trail.name,
            "outline_root": root.sid,
            "xanadu_doc": xdoc.doc_id,
            "message": f"Thinking session started. Use observe(), hypothesize(), and structure() to develop your thinking about '{topic}'.",
        }

    def observe(self, session_id: str, observation: str, tags: list = None) -> dict:
        """Record an observation in the symbiotic session and propagate
        it across all systems."""
        session = self.network.sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}

        idx = session.observe(observation, tags)

        # Also add to Memex as a document
        doc_id = self.memex.add_document(observation, f"Observation #{idx}")

        # Add to NLS as a statement
        stmt = self.nls.create_statement(
            observation, session.thinker,
            labels=tags or ["observation"],
        )

        # Get computer suggestions
        suggestions = session.computer_suggests()

        self._log("pioneer", "observe", observation[:60])

        return {
            "observation_index": idx,
            "memex_doc_id": doc_id,
            "nls_statement": stmt.sid,
            "computer_says": suggestions,
        }

    def structure(self, parent_sid: str, content: str, author: str,
                  labels: list = None) -> dict:
        """Add structured thought under an existing outline node,
        and create Memex documents + links for it."""
        stmt = self.nls.create_statement(content, author, parent_sid, labels)
        doc_id = self.memex.add_document(content, content[:50])

        # Link to parent's document if it exists
        parent = self.nls.statements.get(parent_sid)
        if parent:
            parent_doc = self.memex.add_document(parent.content, parent.content[:50])
            self.memex.link(
                Span(parent_doc, 0, len(parent.content)),
                Span(doc_id, 0, len(content)),
                annotation="structured under",
            )

        return {
            "statement_id": stmt.sid,
            "memex_doc_id": doc_id,
        }

    def synthesize(self, session_id: str) -> dict:
        """Produce a cross-system synthesis of a thinking session."""
        session = self.network.sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}

        synthesis = session.synthesis()

        # Get NLS thought statistics
        thought_stats = self.nls.thought_statistics()

        # Get Memex connection map
        total_docs = len(self.memex.documents)
        total_links = len(self.memex.links)
        total_trails = len(self.memex.trails)

        return {
            "thinking": synthesis,
            "structure": thought_stats,
            "knowledge_base": {
                "documents": total_docs,
                "links": total_links,
                "trails": total_trails,
            },
            "xanadu_documents": len(self.xanadu.documents),
            "live_objects": len(self.dynabook.objects),
        }

    def simulate(self, name: str, setup_fn=None) -> Simulation:
        """Create a Dynabook simulation linked to the thinking environment."""
        sim = self.dynabook.create_simulation(name)
        if setup_fn:
            setup_fn(sim, self.dynabook)
        self._log("pioneer", "simulate", name)
        return sim

    def view(self, mode: str = "outline", depth: int = 3, **kwargs) -> str:
        """View the structured thinking through Engelbart's viewspecs."""
        vs = ViewSpec(
            mode=ViewMode(mode),
            depth=depth,
            filter_labels=kwargs.get("labels", []),
            filter_author=kwargs.get("author"),
            show_metadata=kwargs.get("metadata", False),
        )
        return self.nls.render(vs)

    def connect(self, doc_a: str, span_a: tuple, doc_b: str, span_b: tuple,
                note: str = "") -> dict:
        """Create associations across the knowledge base.

        Works in both Memex (associative trails) and Xanadu (bidirectional links).
        """
        # Memex link
        memex_link = self.memex.link(
            Span(doc_a, span_a[0], span_a[1]),
            Span(doc_b, span_b[0], span_b[1]),
            annotation=note,
        )

        # Xanadu bidirectional link (if docs exist there too)
        xanadu_link = None
        if doc_a in self.xanadu.documents and doc_b in self.xanadu.documents:
            xanadu_link = self.xanadu.create_link(
                doc_a, span_a[0], span_a[1],
                doc_b, span_b[0], span_b[1],
                author="pioneer",
            )

        return {
            "memex_link": memex_link.link_id,
            "xanadu_link": xanadu_link.link_id if xanadu_link else None,
        }

    # ---- Demo ----

    def demo(self) -> str:
        """Run a demonstration of all systems working together.

        This shows what it's like when Bush, Nelson, Engelbart, Kay,
        and Licklider's ideas all converge into a single thinking environment.
        """
        output = []
        output.append("=" * 60)
        output.append("  PIONEER — The Roads Not Taken")
        output.append("  A demonstration of classic computing ideas, unified")
        output.append("=" * 60)

        # 1. Start a thinking session (Licklider)
        output.append("\n--- LICKLIDER: Starting symbiotic thinking session ---")
        ctx = self.think_about("The Future of Human-Computer Interaction", "researcher")
        output.append(f"Session: {ctx['session_id']}")
        output.append(f"Trail: {ctx['trail_name']}")

        # 2. Make observations
        output.append("\n--- BUSH: Recording observations as Memex documents ---")
        obs1 = self.observe(ctx["session_id"],
            "Current interfaces treat humans as button-pushers, not thinkers",
            ["interface", "critique"])
        output.append(f"Observation 1 stored: doc={obs1['memex_doc_id']}")

        obs2 = self.observe(ctx["session_id"],
            "Children learn by constructing, not by consuming pre-made content",
            ["education", "constructionism"])
        output.append(f"Observation 2 stored: doc={obs2['memex_doc_id']}")

        obs3 = self.observe(ctx["session_id"],
            "Bidirectional links would transform how we share knowledge",
            ["links", "knowledge"])
        output.append(f"Observation 3 stored: doc={obs3['memex_doc_id']}")

        if obs1.get("computer_says"):
            output.append(f"Computer suggests: {obs1['computer_says'][0]}")

        # 3. Structure thoughts (Engelbart)
        output.append("\n--- ENGELBART: Structuring thoughts in NLS outline ---")
        root = ctx["outline_root"]
        s1 = self.structure(root, "Current problems with computing interfaces", "researcher",
                           ["problems"])
        s2 = self.structure(s1["statement_id"], "Loss of agency — users are passive consumers", "researcher",
                           ["problems", "agency"])
        s3 = self.structure(s1["statement_id"], "Loss of transparency — systems are opaque black boxes", "researcher",
                           ["problems", "transparency"])
        s4 = self.structure(root, "Proposed solutions from the pioneers", "researcher",
                           ["solutions"])
        s5 = self.structure(s4["statement_id"], "Associative trails (Bush) for personal knowledge paths", "researcher",
                           ["solutions", "memex"])
        s6 = self.structure(s4["statement_id"], "Live objects (Kay) for inspectable, modifiable everything", "researcher",
                           ["solutions", "dynabook"])

        outline = self.view("outline", depth=4)
        output.append(outline)

        # 4. Create Xanadu documents with transclusion (Nelson)
        output.append("\n--- NELSON: Creating transcluded documents ---")
        manifesto = self.xanadu.create_document(
            "Manifesto", "researcher",
            "We need computing systems that augment human thought, not replace it. "
            "The pioneers showed us the way: associative trails, bidirectional links, "
            "structured views, live objects, and symbiotic thinking."
        )
        evidence = self.xanadu.create_document(
            "Evidence", "researcher",
            "Bush (1945) proposed the Memex. Nelson (1960) proposed Xanadu. "
            "Engelbart (1962) proposed augmentation. Kay (1972) proposed the Dynabook. "
            "Licklider (1960) proposed symbiosis."
        )
        # Transclude evidence into the manifesto
        self.xanadu.transclude(manifesto.doc_id, evidence.doc_id, 0, 0, 50)
        rendered = self.xanadu.render_document(manifesto.doc_id)
        output.append(f"Manifesto (with transclusion): {rendered[:120]}...")

        # 5. Create live objects (Kay)
        output.append("\n--- KAY: Creating live objects in the Dynabook ---")
        pioneer = self.dynabook.create_object("pioneer_idea", "concept", {
            "name": "augmentation",
            "era": "1960s",
            "status": "unrealized",
            "potential": "vast",
        })
        pioneer.add_method("describe", """result = f"Idea: {self_state['name']} ({self_state['era']}) - {self_state['status']}" """)

        desc = self.dynabook.send(pioneer.oid, "describe")
        output.append(f"Live object says: {desc}")

        inspection = self.dynabook.send(pioneer.oid, "inspect")
        output.append(f"Object inspection: {json.dumps(inspection, indent=2)[:200]}")

        # 6. Synthesize (Licklider's symbiosis)
        output.append("\n--- LICKLIDER: Symbiotic synthesis ---")
        synth = self.synthesize(ctx["session_id"])
        output.append(f"Observations: {synth['thinking']['total_observations']}")
        output.append(f"Structure: {synth['structure']['total_statements']} statements, "
                      f"depth {synth['structure']['max_depth']}")
        output.append(f"Knowledge base: {synth['knowledge_base']['documents']} docs, "
                      f"{synth['knowledge_base']['links']} links")

        if synth["thinking"]["suggestions"]:
            output.append("Computer's suggestions:")
            for s in synth["thinking"]["suggestions"]:
                output.append(f"  > {s}")

        # 7. View from different angles (Engelbart)
        output.append("\n--- ENGELBART: Same data, prose view ---")
        prose = self.view("prose")
        output.append(prose[:300])

        output.append("\n" + "=" * 60)
        output.append("  These ideas were never wrong. They were just early.")
        output.append("  Now we have the hardware. Do we have the will?")
        output.append("=" * 60)

        return "\n".join(output)


if __name__ == "__main__":
    p = Pioneer()
    print(p.demo())
