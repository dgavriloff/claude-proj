"""
XANADU — After Ted Nelson, "Computer Lib / Dream Machines" (1974)

Nelson's vision, conceived in 1960, was for a universal hypertext system
where EVERY document is permanently available, EVERY quotation links back
to its source, and EVERY link is bidirectional.

The web gave us one-way links that rot. Xanadu promised:

1. TRANSCLUSION: Instead of copying text, you reference it. The original
   is always the source of truth. Quotes are live windows into originals.

2. BIDIRECTIONAL LINKS: If I link to you, you know about it. No more
   broken links, no more orphaned pages.

3. TRANSCOPYRIGHT: Authors get paid when their content is transcluded.
   The system itself handles attribution and micropayments.

4. PARALLEL DOCUMENTS: You can view documents side-by-side with visible
   connections between corresponding parts.

5. VERSION MANAGEMENT: Nothing is ever deleted. Every version is preserved
   and addressable.

"A file is not bumped. You just add on. And you never throw anything away."

This implementation provides:
- Content-addressed, append-only document storage
- Transclusion spans that reference rather than copy
- Bidirectional link registry
- Parallel document visualization
- Full version history
"""

import hashlib
import time
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class ContentType(Enum):
    TEXT = "text"
    TRANSCLUSION = "transclusion"


@dataclass
class EDL:
    """Edit Decision List — Nelson's term for a document structure.

    An EDL is a list of spans, where each span is either original content
    or a transclusion (a live reference to content in another document).
    The document you see is assembled from these spans at render time.

    This is fundamentally different from copy-paste. The source is always
    the source. Attribution is structural, not social.
    """
    spans: list = field(default_factory=list)

    def add_original(self, text: str) -> int:
        idx = len(self.spans)
        self.spans.append({
            "type": ContentType.TEXT.value,
            "content": text,
        })
        return idx

    def add_transclusion(self, source_doc: str, source_version: int,
                         start: int, end: int) -> int:
        """Transclude content from another document.

        This is the big idea. You're not copying — you're creating a live
        window into the original. If someone reads your document and
        encounters this span, they can always trace it back to its origin.
        """
        idx = len(self.spans)
        self.spans.append({
            "type": ContentType.TRANSCLUSION.value,
            "source_doc": source_doc,
            "source_version": source_version,
            "start": start,
            "end": end,
        })
        return idx


@dataclass
class XanaduDocument:
    """A Xanadu document — versioned, transclusive, permanently addressed."""
    doc_id: str
    title: str
    author: str
    versions: list = field(default_factory=list)  # list of EDLs
    created_at: float = field(default_factory=time.time)

    @property
    def current_version(self) -> int:
        return len(self.versions) - 1

    @property
    def current_edl(self) -> Optional[EDL]:
        if self.versions:
            return self.versions[-1]
        return None

    def new_version(self) -> EDL:
        """Create a new version. The old one is NEVER deleted.

        'A file is not bumped.'
        """
        edl = EDL()
        self.versions.append(edl)
        return edl


@dataclass
class BiLink:
    """A bidirectional link between two document spans.

    In Xanadu, links are not embedded in documents — they exist in a
    separate link registry. This means:
    - Links are bidirectional by default
    - Anyone can create links between any documents
    - Documents don't need to be modified to be linked
    - Links themselves are first-class objects that can be linked to
    """
    link_id: str
    source_doc: str
    source_start: int
    source_end: int
    target_doc: str
    target_start: int
    target_end: int
    link_type: str = "reference"
    author: str = ""
    created_at: float = field(default_factory=time.time)


class Xanadu:
    """The Xanadu system — a universal hypertext with transclusion.

    Nelson has been working on this since 1960. The web was supposed to be
    a temporary measure. Here we build what he actually wanted.
    """

    def __init__(self):
        self.documents: dict[str, XanaduDocument] = {}
        self.links: dict[str, BiLink] = {}
        # Bidirectional index: both sides know about every link
        self._forward_links: dict[str, list[str]] = {}  # doc_id -> [link_ids]
        self._backward_links: dict[str, list[str]] = {}  # doc_id -> [link_ids]
        # Transclusion registry: who's transcluding whom
        self._transcluded_by: dict[str, list[str]] = {}  # source_doc -> [transcluding_docs]

    def create_document(self, title: str, author: str, content: str = "") -> XanaduDocument:
        """Create a new document in the Xanadu system."""
        doc_id = hashlib.sha256(
            f"{title}:{author}:{time.time()}".encode()
        ).hexdigest()[:16]
        doc = XanaduDocument(doc_id=doc_id, title=title, author=author)
        if content:
            edl = doc.new_version()
            edl.add_original(content)
        self.documents[doc_id] = doc
        return doc

    def transclude(self, target_doc_id: str, source_doc_id: str,
                   source_version: int, start: int, end: int) -> int:
        """Transclude content from one document into another.

        This is NOT copying. This is creating a live reference.
        The source document's author gets attribution (and in Nelson's
        full vision, micropayment) every time someone reads through
        the transclusion.
        """
        target = self.documents[target_doc_id]
        edl = target.current_edl
        if edl is None:
            edl = target.new_version()

        span_idx = edl.add_transclusion(source_doc_id, source_version, start, end)

        self._transcluded_by.setdefault(source_doc_id, []).append(target_doc_id)
        return span_idx

    def create_link(self, source_doc: str, source_start: int, source_end: int,
                    target_doc: str, target_start: int, target_end: int,
                    link_type: str = "reference", author: str = "") -> BiLink:
        """Create a bidirectional link between two document spans.

        The link lives in the registry, NOT in either document.
        Both documents are aware of it through the index.
        """
        link_id = hashlib.sha256(
            f"{source_doc}:{source_start}>{target_doc}:{target_start}@{time.time()}".encode()
        ).hexdigest()[:16]

        link = BiLink(
            link_id=link_id,
            source_doc=source_doc, source_start=source_start, source_end=source_end,
            target_doc=target_doc, target_start=target_start, target_end=target_end,
            link_type=link_type, author=author,
        )
        self.links[link_id] = link
        self._forward_links.setdefault(source_doc, []).append(link_id)
        self._backward_links.setdefault(target_doc, []).append(link_id)
        return link

    def render_document(self, doc_id: str, version: Optional[int] = None) -> str:
        """Render a document by resolving all transclusions.

        This is where the magic happens. A Xanadu document is assembled
        at read-time by pulling in all transcluded content from its sources.
        The reader sees a seamless document; the system tracks every origin.
        """
        doc = self.documents.get(doc_id)
        if not doc or not doc.versions:
            return ""

        v = version if version is not None else doc.current_version
        edl = doc.versions[v]
        parts = []

        for span in edl.spans:
            if span["type"] == ContentType.TEXT.value:
                parts.append(span["content"])
            elif span["type"] == ContentType.TRANSCLUSION.value:
                source = self.documents.get(span["source_doc"])
                if source and span["source_version"] < len(source.versions):
                    source_edl = source.versions[span["source_version"]]
                    source_text = self._render_edl_text(source_edl)
                    parts.append(source_text[span["start"]:span["end"]])
                else:
                    parts.append(f"[transclusion:{span['source_doc']}:unavailable]")

        return "".join(parts)

    def _render_edl_text(self, edl: EDL) -> str:
        """Render just the text spans of an EDL (non-recursive for safety)."""
        parts = []
        for span in edl.spans:
            if span["type"] == ContentType.TEXT.value:
                parts.append(span["content"])
        return "".join(parts)

    def links_involving(self, doc_id: str) -> list[BiLink]:
        """Get ALL links involving a document — incoming AND outgoing.

        This is what the web never gave us. If someone links to your
        document, YOU KNOW ABOUT IT.
        """
        link_ids = set()
        link_ids.update(self._forward_links.get(doc_id, []))
        link_ids.update(self._backward_links.get(doc_id, []))
        return [self.links[lid] for lid in link_ids]

    def parallel_view(self, doc_a_id: str, doc_b_id: str) -> dict:
        """Generate a parallel view of two documents with visible connections.

        Nelson's "parallel documents" view: two documents side by side
        with lines drawn between corresponding/linked spans.
        """
        text_a = self.render_document(doc_a_id)
        text_b = self.render_document(doc_b_id)

        connections = []
        for link in self.links.values():
            if link.source_doc == doc_a_id and link.target_doc == doc_b_id:
                connections.append({
                    "left_start": link.source_start,
                    "left_end": link.source_end,
                    "right_start": link.target_start,
                    "right_end": link.target_end,
                    "type": link.link_type,
                })
            elif link.source_doc == doc_b_id and link.target_doc == doc_a_id:
                connections.append({
                    "left_start": link.target_start,
                    "left_end": link.target_end,
                    "right_start": link.source_start,
                    "right_end": link.source_end,
                    "type": link.link_type,
                })

        return {
            "left": {"doc_id": doc_a_id, "text": text_a},
            "right": {"doc_id": doc_b_id, "text": text_b},
            "connections": connections,
        }

    def who_transcluded(self, doc_id: str) -> list[str]:
        """Find all documents that transclude from this one.

        This is the transcopyright mechanism — the source always knows
        who is quoting it.
        """
        return list(set(self._transcluded_by.get(doc_id, [])))

    def version_history(self, doc_id: str) -> list[dict]:
        """Get the full version history of a document.

        Nothing is ever deleted in Xanadu. Every version is permanent
        and addressable.
        """
        doc = self.documents.get(doc_id)
        if not doc:
            return []
        return [
            {
                "version": i,
                "span_count": len(edl.spans),
                "text_preview": self._render_edl_text(edl)[:100],
            }
            for i, edl in enumerate(doc.versions)
        ]
