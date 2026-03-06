"""
MEMEX — After Vannevar Bush, "As We May Think" (1945)

Bush imagined a desk-sized device where a researcher stores all their books,
records, and communications, and which can be consulted with exceeding speed
and flexibility. The essential feature: ASSOCIATIVE TRAILS.

Not hierarchical folders. Not keyword search. Trails — personal paths through
knowledge that a thinker blazes as they work, which can be shared, forked,
and extended by others.

"Wholly new forms of encyclopedias will appear, ready-made with a trail of
associative trails running through them, ready to be dropped into the memex
and there amplified."

This implementation provides:
- A content-addressed store for documents (like Bush's microfilm reels)
- Associative links between arbitrary spans of text
- Named trails that record a thinker's path through material
- Trail sharing and forking
"""

import hashlib
import json
import time
from dataclasses import dataclass, field, asdict
from typing import Optional
from pathlib import Path


@dataclass
class Span:
    """A reference to a specific region within a document."""
    doc_id: str
    start: int
    end: int

    def __post_init__(self):
        if self.end < self.start:
            raise ValueError("Span end must be >= start")


@dataclass
class Link:
    """An associative link between two spans — the core of the Memex.

    Bush: "When the user is building a trail, he names it, inserts the name
    in his code book, and taps it out on his keyboard. Before him are the
    two items to be joined, projected onto adjacent viewing positions."
    """
    source: Span
    target: Span
    annotation: str = ""
    created_at: float = field(default_factory=time.time)
    link_id: str = ""

    def __post_init__(self):
        if not self.link_id:
            raw = f"{self.source.doc_id}:{self.source.start}-{self.source.end}" \
                  f">{self.target.doc_id}:{self.target.start}-{self.target.end}" \
                  f"@{self.created_at}"
            self.link_id = hashlib.sha256(raw.encode()).hexdigest()[:16]


@dataclass
class Trail:
    """A named path through documents — Bush's key insight.

    A trail is an ordered sequence of (document, span) stops with annotations.
    It represents one person's journey through a body of knowledge.
    Trails can be forked, extended, and shared.
    """
    name: str
    author: str
    stops: list = field(default_factory=list)  # list of Spans
    annotations: dict = field(default_factory=dict)  # stop_index -> note
    created_at: float = field(default_factory=time.time)
    forked_from: Optional[str] = None

    def add_stop(self, span: Span, note: str = ""):
        idx = len(self.stops)
        self.stops.append(span)
        if note:
            self.annotations[str(idx)] = note
        return idx

    def fork(self, new_author: str, new_name: Optional[str] = None):
        """Fork a trail — take someone else's path and make it your own."""
        return Trail(
            name=new_name or f"{self.name} (fork by {new_author})",
            author=new_author,
            stops=list(self.stops),
            annotations=dict(self.annotations),
            forked_from=self.name,
        )


class Memex:
    """The Memex itself — a personal knowledge store with associative trails.

    Bush envisioned this as a physical desk with translucent screens,
    levers, and microfilm. We build it as a content-addressed store
    with bidirectional link indices and named trails.
    """

    def __init__(self, storage_dir: Optional[str] = None):
        self.documents: dict[str, str] = {}      # doc_id -> content
        self.doc_titles: dict[str, str] = {}      # doc_id -> title
        self.links: dict[str, Link] = {}          # link_id -> Link
        self.trails: dict[str, Trail] = {}        # trail_name -> Trail
        # Indices for fast lookup
        self._links_from: dict[str, list[str]] = {}  # doc_id -> [link_ids]
        self._links_to: dict[str, list[str]] = {}    # doc_id -> [link_ids]
        self.storage_dir = Path(storage_dir) if storage_dir else None

    def add_document(self, content: str, title: str = "") -> str:
        """Add a document to the Memex. Returns content-addressed ID.

        Bush used microfilm. We use SHA-256. Same idea —
        the content IS the address.
        """
        doc_id = hashlib.sha256(content.encode()).hexdigest()[:16]
        self.documents[doc_id] = content
        self.doc_titles[doc_id] = title or f"Untitled ({doc_id[:8]})"
        return doc_id

    def get_document(self, doc_id: str) -> Optional[str]:
        return self.documents.get(doc_id)

    def get_span_text(self, span: Span) -> str:
        doc = self.documents.get(span.doc_id, "")
        return doc[span.start:span.end]

    def link(self, source: Span, target: Span, annotation: str = "") -> Link:
        """Create an associative link between two spans.

        This is the fundamental operation of the Memex — connecting
        two pieces of information across documents.
        """
        lnk = Link(source=source, target=target, annotation=annotation)
        self.links[lnk.link_id] = lnk
        self._links_from.setdefault(source.doc_id, []).append(lnk.link_id)
        self._links_to.setdefault(target.doc_id, []).append(lnk.link_id)
        return lnk

    def links_from(self, doc_id: str) -> list[Link]:
        """All links originating from a document."""
        return [self.links[lid] for lid in self._links_from.get(doc_id, [])]

    def links_to(self, doc_id: str) -> list[Link]:
        """All links pointing to a document."""
        return [self.links[lid] for lid in self._links_to.get(doc_id, [])]

    def create_trail(self, name: str, author: str) -> Trail:
        """Start a new trail through the Memex."""
        trail = Trail(name=name, author=author)
        self.trails[name] = trail
        return trail

    def walk_trail(self, trail_name: str):
        """Generator that walks a trail, yielding each stop with context.

        Bush: "It is exactly as though the physical items had been gathered
        together from widely separated sources and bound together to form
        a new book."
        """
        trail = self.trails.get(trail_name)
        if not trail:
            return

        for idx, span in enumerate(trail.stops):
            text = self.get_span_text(span)
            note = trail.annotations.get(str(idx), "")
            links_out = [l for l in self.links_from(span.doc_id)
                         if l.source.start <= span.end and l.source.end >= span.start]
            yield {
                "stop": idx,
                "document": self.doc_titles.get(span.doc_id, span.doc_id),
                "text": text,
                "annotation": note,
                "outgoing_links": len(links_out),
            }

    def find_connections(self, doc_id: str, depth: int = 2) -> dict:
        """Discover the web of associations around a document.

        This is what Bush was really after — not just storage, but
        the ability to follow a web of associations that mirrors
        how the human mind actually works.
        """
        visited = set()
        connections = {}

        def _explore(did, d):
            if d <= 0 or did in visited:
                return
            visited.add(did)
            connections[did] = {
                "title": self.doc_titles.get(did, did),
                "links_out": [],
                "links_in": [],
            }
            for link in self.links_from(did):
                connections[did]["links_out"].append({
                    "target": link.target.doc_id,
                    "annotation": link.annotation,
                })
                _explore(link.target.doc_id, d - 1)
            for link in self.links_to(did):
                connections[did]["links_in"].append({
                    "source": link.source.doc_id,
                    "annotation": link.annotation,
                })
                _explore(link.source.doc_id, d - 1)

        _explore(doc_id, depth)
        return connections

    def save(self):
        """Persist the Memex to disk."""
        if not self.storage_dir:
            return
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        data = {
            "documents": self.documents,
            "doc_titles": self.doc_titles,
            "links": {lid: asdict(l) for lid, l in self.links.items()},
            "trails": {
                name: {
                    "name": t.name,
                    "author": t.author,
                    "stops": [asdict(s) for s in t.stops],
                    "annotations": t.annotations,
                    "created_at": t.created_at,
                    "forked_from": t.forked_from,
                }
                for name, t in self.trails.items()
            },
        }
        (self.storage_dir / "memex.json").write_text(json.dumps(data, indent=2))

    def load(self):
        """Load a Memex from disk."""
        if not self.storage_dir:
            return
        path = self.storage_dir / "memex.json"
        if not path.exists():
            return

        data = json.loads(path.read_text())
        self.documents = data["documents"]
        self.doc_titles = data["doc_titles"]

        for lid, ld in data["links"].items():
            source = Span(**ld["source"])
            target = Span(**ld["target"])
            link = Link(source=source, target=target,
                        annotation=ld["annotation"],
                        created_at=ld["created_at"],
                        link_id=ld["link_id"])
            self.links[lid] = link
            self._links_from.setdefault(source.doc_id, []).append(lid)
            self._links_to.setdefault(target.doc_id, []).append(lid)

        for name, td in data["trails"].items():
            trail = Trail(
                name=td["name"],
                author=td["author"],
                stops=[Span(**s) for s in td["stops"]],
                annotations=td["annotations"],
                created_at=td["created_at"],
                forked_from=td.get("forked_from"),
            )
            self.trails[name] = trail
