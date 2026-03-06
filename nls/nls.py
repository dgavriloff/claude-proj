"""
NLS (oN-Line System) — After Doug Engelbart, "Augmenting Human Intellect" (1962)

Engelbart's 1968 demo showed: hypertext, video conferencing, collaborative
editing, the mouse, windows, outline processing, and version control — all
in one system, all in 1968.

But the deeper idea was in his 1962 framework paper. The computer isn't
supposed to do our thinking for us. It's supposed to AUGMENT our ability
to think. The system should provide multiple simultaneous views of the same
underlying structure, let us restructure our thoughts fluidly, and
collaborate in real-time.

Key concepts:
1. STRUCTURED STATEMENTS: Every piece of content is a node in a tree.
   You can view it as an outline, a document, or a network.
2. VIEWSPECS: Different views of the same data — collapsed, expanded,
   filtered, sorted. The data doesn't change; your lens does.
3. COLLABORATIVE STRUCTURE: Multiple people editing the same structure
   simultaneously, each with their own viewspec.
4. AUGMENTATION: The system tracks your thought process and helps you
   see patterns you wouldn't see on your own.

"By 'augmenting human intellect' we mean increasing the capability of a
man to approach a complex problem situation, to gain comprehension to suit
his particular needs, and to derive solutions to problems."
"""

import time
import hashlib
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class ViewMode(Enum):
    OUTLINE = "outline"
    PROSE = "prose"
    NETWORK = "network"
    FILTERED = "filtered"


@dataclass
class Statement:
    """A structured statement — the atomic unit of NLS.

    Every piece of content in NLS is a statement in a hierarchical structure.
    Statements can be expanded, collapsed, linked, filtered, and rearranged.
    The same statement can appear differently depending on your viewspec.
    """
    sid: str
    content: str
    author: str
    children: list = field(default_factory=list)  # list of Statement sids
    parent: Optional[str] = None
    labels: list = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    modified_at: float = field(default_factory=time.time)
    links: list = field(default_factory=list)  # cross-reference sids


@dataclass
class ViewSpec:
    """A view specification — how to look at the structure.

    Engelbart's key insight: the same underlying structure can be viewed
    in radically different ways. An outline with 3 levels of depth. A
    flat document. A filtered view showing only items by one author.
    A network graph of cross-references.

    The data never changes. The viewspec changes.
    """
    mode: ViewMode = ViewMode.OUTLINE
    depth: int = 3              # how many levels deep to show
    show_labels: bool = True
    filter_labels: list = field(default_factory=list)  # only show these labels
    filter_author: Optional[str] = None
    sort_by: str = "order"      # order, date, alpha
    show_metadata: bool = False
    collapsed: set = field(default_factory=set)  # sids of collapsed nodes


class NLS:
    """The oN-Line System — augmenting human intellect through structured thought.

    Where a word processor gives you a flat stream of characters, NLS gives
    you a living structure that you can view from multiple angles simultaneously.
    """

    def __init__(self):
        self.statements: dict[str, Statement] = {}
        self.root_ids: list[str] = []  # top-level statement ordering
        self._change_log: list[dict] = []  # for collaborative awareness

    def create_statement(self, content: str, author: str,
                         parent_id: Optional[str] = None,
                         labels: Optional[list] = None) -> Statement:
        """Create a new statement in the structure."""
        sid = hashlib.sha256(
            f"{content}:{author}:{time.time()}".encode()
        ).hexdigest()[:12]

        stmt = Statement(
            sid=sid, content=content, author=author,
            parent=parent_id, labels=labels or [],
        )
        self.statements[sid] = stmt

        if parent_id and parent_id in self.statements:
            self.statements[parent_id].children.append(sid)
        else:
            self.root_ids.append(sid)

        self._log_change("create", sid, author)
        return stmt

    def move_statement(self, sid: str, new_parent_id: Optional[str], author: str):
        """Restructure your thinking by moving a statement."""
        stmt = self.statements.get(sid)
        if not stmt:
            return

        # Remove from old parent
        if stmt.parent and stmt.parent in self.statements:
            old_parent = self.statements[stmt.parent]
            old_parent.children = [c for c in old_parent.children if c != sid]
        elif sid in self.root_ids:
            self.root_ids = [r for r in self.root_ids if r != sid]

        # Add to new parent
        if new_parent_id and new_parent_id in self.statements:
            self.statements[new_parent_id].children.append(sid)
            stmt.parent = new_parent_id
        else:
            self.root_ids.append(sid)
            stmt.parent = None

        stmt.modified_at = time.time()
        self._log_change("move", sid, author)

    def cross_reference(self, from_sid: str, to_sid: str):
        """Create a cross-reference link between statements.

        NLS statements exist in a tree, but cross-references create
        a network overlay. Same data, two structures.
        """
        if from_sid in self.statements and to_sid in self.statements:
            self.statements[from_sid].links.append(to_sid)

    def render(self, viewspec: ViewSpec, root: Optional[str] = None) -> str:
        """Render the structure through a particular viewspec.

        This is Engelbart's core contribution to interface design:
        the same data, viewed differently, reveals different things.
        """
        if viewspec.mode == ViewMode.OUTLINE:
            return self._render_outline(viewspec, root)
        elif viewspec.mode == ViewMode.PROSE:
            return self._render_prose(viewspec, root)
        elif viewspec.mode == ViewMode.NETWORK:
            return self._render_network(viewspec, root)
        elif viewspec.mode == ViewMode.FILTERED:
            return self._render_filtered(viewspec)
        return ""

    def _render_outline(self, vs: ViewSpec, root: Optional[str], depth: int = 0) -> str:
        """Render as a collapsible outline — the classic NLS view."""
        if depth >= vs.depth:
            return ""

        lines = []
        sids = [root] if root else self.root_ids

        for sid in sids:
            stmt = self.statements.get(sid)
            if not stmt:
                continue
            if not self._passes_filter(stmt, vs):
                continue

            indent = "  " * depth
            bullet = "+" if stmt.children and sid not in vs.collapsed else "-"
            label_str = f" [{', '.join(stmt.labels)}]" if vs.show_labels and stmt.labels else ""
            meta = f" ({stmt.author}, {time.strftime('%Y-%m-%d', time.localtime(stmt.created_at))})" if vs.show_metadata else ""
            lines.append(f"{indent}{bullet} {stmt.content}{label_str}{meta}")

            if sid not in vs.collapsed:
                for child_id in stmt.children:
                    lines.append(self._render_outline(vs, child_id, depth + 1))

        return "\n".join(l for l in lines if l)

    def _render_prose(self, vs: ViewSpec, root: Optional[str]) -> str:
        """Render as flowing prose — statements become paragraphs."""
        parts = []
        sids = [root] if root else self.root_ids

        for sid in sids:
            stmt = self.statements.get(sid)
            if not stmt or not self._passes_filter(stmt, vs):
                continue
            parts.append(stmt.content)
            for child_id in stmt.children:
                parts.append(self._render_prose(vs, child_id))

        return "\n\n".join(p for p in parts if p)

    def _render_network(self, vs: ViewSpec, root: Optional[str]) -> str:
        """Render as a network map showing cross-references."""
        lines = []
        sids = [root] if root else list(self.statements.keys())

        for sid in sids:
            stmt = self.statements.get(sid)
            if not stmt:
                continue
            refs = [f"-> {self.statements[r].content[:40]}..."
                    for r in stmt.links if r in self.statements]
            ref_str = f" ({'; '.join(refs)})" if refs else ""
            lines.append(f"[{stmt.content[:50]}]{ref_str}")

        return "\n".join(lines)

    def _render_filtered(self, vs: ViewSpec) -> str:
        """Render only statements matching the filter criteria."""
        lines = []
        for stmt in self.statements.values():
            if self._passes_filter(stmt, vs):
                lines.append(f"- {stmt.content}")
        return "\n".join(lines)

    def _passes_filter(self, stmt: Statement, vs: ViewSpec) -> bool:
        if vs.filter_author and stmt.author != vs.filter_author:
            return False
        if vs.filter_labels and not any(l in stmt.labels for l in vs.filter_labels):
            return False
        return True

    def _log_change(self, action: str, sid: str, author: str):
        self._change_log.append({
            "action": action,
            "sid": sid,
            "author": author,
            "time": time.time(),
        })

    def recent_changes(self, n: int = 10) -> list[dict]:
        """See what's been happening — collaborative awareness."""
        return self._change_log[-n:]

    def find_pattern(self, label: str) -> list[Statement]:
        """Find all statements with a given label — pattern discovery.

        Engelbart believed the system should help you see patterns
        in your own thinking that you wouldn't notice otherwise.
        """
        return [s for s in self.statements.values() if label in s.labels]

    def thought_statistics(self) -> dict:
        """Analyze the structure of your thinking.

        How deep is your outline? How interconnected are your ideas?
        Are there orphaned thoughts? Dense clusters?

        This is augmentation — the computer shows you things about
        your own thought process.
        """
        total = len(self.statements)
        if total == 0:
            return {"total": 0}

        depths = {}
        for sid in self.root_ids:
            self._measure_depth(sid, 0, depths)

        max_depth = max(depths.values()) if depths else 0
        avg_depth = sum(depths.values()) / len(depths) if depths else 0
        cross_refs = sum(len(s.links) for s in self.statements.values())
        leaf_count = sum(1 for s in self.statements.values() if not s.children)

        return {
            "total_statements": total,
            "max_depth": max_depth,
            "avg_depth": round(avg_depth, 2),
            "cross_references": cross_refs,
            "leaf_nodes": leaf_count,
            "branching_factor": round(total / max(len(self.root_ids), 1), 2),
            "interconnectedness": round(cross_refs / max(total, 1), 2),
        }

    def _measure_depth(self, sid: str, depth: int, depths: dict):
        depths[sid] = depth
        stmt = self.statements.get(sid)
        if stmt:
            for child_id in stmt.children:
                self._measure_depth(child_id, depth + 1, depths)
