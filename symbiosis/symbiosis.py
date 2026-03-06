"""
SYMBIOSIS — After J.C.R. Licklider, "Man-Computer Symbiosis" (1960)

Licklider didn't want artificial intelligence. He wanted something weirder
and more interesting: a system where humans and computers THINK TOGETHER,
each contributing what they're best at.

"Men will set the goals, formulate the hypotheses, determine the criteria,
and perform the evaluations. Computing machines will do the routinizable
work that must be done to prepare the way for insights and decisions in
technical and scientific thinking."

The human brings: intuition, goals, aesthetics, judgment, creativity.
The computer brings: speed, memory, tirelessness, pattern-matching, consistency.

Neither replaces the other. Together, they're smarter than either alone.

Licklider also envisioned what he called the "Intergalactic Computer Network"
(1963 memo) — a network of thinking systems that could share knowledge and
computation. He was describing the internet, but the version he imagined was
for collaborative thought, not for advertising.

This implementation provides:
- A thinking session framework for human-computer collaboration
- Hypothesis tracking and evidence management
- Automatic pattern detection in human observations
- A "thinking trace" that records the symbiotic reasoning process
- Network sharing of insights between thinking sessions
"""

import time
import hashlib
import math
from dataclasses import dataclass, field
from typing import Optional, Any
from collections import Counter


@dataclass
class Observation:
    """Something the human has noticed or the computer has detected."""
    content: str
    source: str  # "human" or "computer"
    confidence: float = 1.0
    tags: list = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)


@dataclass
class Hypothesis:
    """A conjecture about what's going on.

    Licklider envisioned humans forming hypotheses and computers
    helping evaluate them by crunching through data and finding
    patterns the human might miss.
    """
    statement: str
    author: str  # who proposed it
    supporting: list = field(default_factory=list)  # observation indices
    contradicting: list = field(default_factory=list)
    confidence: float = 0.5
    status: str = "active"  # active, supported, refuted, merged
    created_at: float = field(default_factory=time.time)


@dataclass
class ThinkingTrace:
    """A record of the collaborative thinking process.

    Not just what was concluded, but HOW it was reached — the interplay
    between human intuition and computer analysis.
    """
    steps: list = field(default_factory=list)

    def record(self, actor: str, action: str, content: str, metadata: Optional[dict] = None):
        self.steps.append({
            "actor": actor,
            "action": action,
            "content": content,
            "metadata": metadata or {},
            "time": time.time(),
        })


class SymbioticSession:
    """A collaborative thinking session — human and computer working as one.

    The session provides a structured space for:
    1. The human to record observations and form hypotheses
    2. The computer to detect patterns, find contradictions, and suggest connections
    3. Both to converge on understanding through iterative refinement
    """

    def __init__(self, topic: str, thinker: str = "human"):
        self.session_id = hashlib.sha256(
            f"{topic}:{thinker}:{time.time()}".encode()
        ).hexdigest()[:12]
        self.topic = topic
        self.thinker = thinker
        self.observations: list[Observation] = []
        self.hypotheses: list[Hypothesis] = []
        self.trace = ThinkingTrace()
        self.created_at = time.time()

        self.trace.record("system", "start", f"Thinking session begun: {topic}")

    def observe(self, content: str, tags: Optional[list] = None) -> int:
        """Record a human observation.

        The human notices something. The computer remembers it perfectly
        and indexes it for pattern detection.
        """
        obs = Observation(content=content, source="human", tags=tags or [])
        idx = len(self.observations)
        self.observations.append(obs)
        self.trace.record("human", "observe", content, {"tags": tags})

        # Computer's turn: check for patterns triggered by this observation
        patterns = self._detect_patterns(obs)
        for pattern in patterns:
            self.trace.record("computer", "pattern_detected", pattern)

        return idx

    def hypothesize(self, statement: str, based_on: Optional[list] = None) -> int:
        """Form a hypothesis.

        The human proposes an explanation. The computer immediately
        checks it against all known observations.
        """
        hyp = Hypothesis(statement=statement, author="human",
                         supporting=based_on or [])
        idx = len(self.hypotheses)
        self.hypotheses.append(hyp)
        self.trace.record("human", "hypothesize", statement)

        # Computer evaluates
        evaluation = self._evaluate_hypothesis(idx)
        self.trace.record("computer", "evaluate", evaluation["summary"])

        return idx

    def _detect_patterns(self, new_obs: Observation) -> list[str]:
        """The computer's contribution: finding patterns humans miss.

        This is the symbiosis in action. The human makes observations
        one at a time. The computer holds ALL of them in memory and
        can spot repetitions, clusters, and anomalies.
        """
        patterns = []

        # Tag frequency analysis
        all_tags = [t for obs in self.observations for t in obs.tags]
        tag_counts = Counter(all_tags)
        recurring = [tag for tag, count in tag_counts.items() if count >= 3]
        if recurring and any(t in recurring for t in new_obs.tags):
            patterns.append(
                f"Recurring theme detected: {', '.join(recurring)} "
                f"(appeared 3+ times in observations)"
            )

        # Content similarity (simple word overlap)
        new_words = set(new_obs.content.lower().split())
        for i, old_obs in enumerate(self.observations[:-1]):
            old_words = set(old_obs.content.lower().split())
            overlap = new_words & old_words
            if len(overlap) > 3:
                patterns.append(
                    f"Observation #{len(self.observations)-1} shares vocabulary "
                    f"with #{i}: {', '.join(list(overlap)[:5])}"
                )

        return patterns

    def _evaluate_hypothesis(self, hyp_idx: int) -> dict:
        """The computer evaluates a hypothesis against all evidence.

        Licklider: the computer does the "routinizable work" of checking
        consistency, finding counterexamples, and quantifying confidence.
        """
        hyp = self.hypotheses[hyp_idx]
        hyp_words = set(hyp.statement.lower().split())

        supporting = []
        contradicting = []

        for i, obs in enumerate(self.observations):
            obs_words = set(obs.content.lower().split())
            overlap = hyp_words & obs_words

            # Simple relevance heuristic
            if len(overlap) >= 2:
                # Check for negation words as a crude contradiction detector
                negations = {"not", "never", "no", "false", "wrong", "incorrect",
                             "impossible", "unlikely", "doubt", "fail"}
                if negations & obs_words:
                    contradicting.append(i)
                else:
                    supporting.append(i)

        hyp.supporting = list(set(hyp.supporting + supporting))
        hyp.contradicting = contradicting

        total_evidence = len(supporting) + len(contradicting)
        if total_evidence > 0:
            hyp.confidence = len(supporting) / total_evidence
        else:
            hyp.confidence = 0.5

        return {
            "hypothesis": hyp.statement,
            "supporting_count": len(supporting),
            "contradicting_count": len(contradicting),
            "confidence": hyp.confidence,
            "summary": (
                f"Hypothesis '{hyp.statement[:50]}...' has "
                f"{len(supporting)} supporting and {len(contradicting)} "
                f"contradicting observations (confidence: {hyp.confidence:.0%})"
            ),
        }

    def computer_suggests(self) -> list[str]:
        """The computer's proactive contribution to the thinking process.

        Not waiting to be asked — actively participating in the thought.
        Suggesting connections, gaps, and next steps.
        """
        suggestions = []

        # Suggest under-explored areas
        all_tags = [t for obs in self.observations for t in obs.tags]
        tag_counts = Counter(all_tags)
        if tag_counts:
            least_explored = tag_counts.most_common()[-1]
            suggestions.append(
                f"Under-explored area: '{least_explored[0]}' has only "
                f"{least_explored[1]} observation(s)"
            )

        # Suggest hypotheses that need testing
        weak = [h for h in self.hypotheses
                if h.status == "active" and len(h.supporting) < 2]
        for h in weak:
            suggestions.append(
                f"Hypothesis needs more evidence: '{h.statement[:60]}...'"
            )

        # Suggest connections between observations
        if len(self.observations) >= 4:
            suggestions.append(
                f"You have {len(self.observations)} observations. "
                f"Consider: what ties the most recent ones together?"
            )

        # Note if there are contradictions
        for h in self.hypotheses:
            if h.contradicting:
                suggestions.append(
                    f"Contradiction found in '{h.statement[:40]}...' — "
                    f"observation(s) {h.contradicting} may conflict"
                )

        return suggestions

    def synthesis(self) -> dict:
        """Produce a synthesis of the thinking session.

        The symbiotic result: a summary that neither the human nor
        the computer could have produced alone.
        """
        active_hypotheses = [h for h in self.hypotheses if h.status == "active"]
        best = sorted(active_hypotheses, key=lambda h: h.confidence, reverse=True)

        return {
            "topic": self.topic,
            "total_observations": len(self.observations),
            "total_hypotheses": len(self.hypotheses),
            "thinking_steps": len(self.trace.steps),
            "top_hypotheses": [
                {
                    "statement": h.statement,
                    "confidence": h.confidence,
                    "evidence_count": len(h.supporting),
                }
                for h in best[:5]
            ],
            "human_contributions": sum(
                1 for s in self.trace.steps if s["actor"] == "human"
            ),
            "computer_contributions": sum(
                1 for s in self.trace.steps if s["actor"] == "computer"
            ),
            "suggestions": self.computer_suggests(),
        }


class IntergalacticNetwork:
    """Licklider's Intergalactic Computer Network (1963).

    A network not for transmitting files but for sharing THINKING.
    Sessions can publish insights that other sessions can discover
    and build upon.

    "The hope is that, in not too many years, human brains and
    computing machines will be coupled together very tightly."
    """

    def __init__(self):
        self.sessions: dict[str, SymbioticSession] = {}
        self.shared_insights: list[dict] = []

    def create_session(self, topic: str, thinker: str = "human") -> SymbioticSession:
        session = SymbioticSession(topic, thinker)
        self.sessions[session.session_id] = session
        return session

    def share_insight(self, session_id: str, insight: str, tags: list):
        """Share an insight from one thinking session to the network.

        In Licklider's vision, these insights would be discoverable
        by anyone working on related problems.
        """
        session = self.sessions.get(session_id)
        if not session:
            return

        self.shared_insights.append({
            "insight": insight,
            "tags": tags,
            "source_session": session_id,
            "source_topic": session.topic,
            "time": time.time(),
        })

    def discover(self, tags: list) -> list[dict]:
        """Discover shared insights relevant to your thinking.

        The network helps you find others who've been thinking about
        related problems.
        """
        results = []
        query_tags = set(tags)
        for insight in self.shared_insights:
            insight_tags = set(insight["tags"])
            overlap = query_tags & insight_tags
            if overlap:
                results.append({
                    **insight,
                    "relevance": len(overlap) / len(query_tags) if query_tags else 0,
                })
        return sorted(results, key=lambda x: x["relevance"], reverse=True)

    def cross_pollinate(self) -> list[dict]:
        """Find unexpected connections between different thinking sessions.

        The real power of a network: serendipitous discovery.
        Someone working on biology might share an insight relevant
        to economics, if the computer can spot the structural similarity.
        """
        connections = []
        session_list = list(self.sessions.values())

        for i, s1 in enumerate(session_list):
            for s2 in session_list[i+1:]:
                # Find shared vocabulary between session observations
                words1 = set()
                for obs in s1.observations:
                    words1.update(obs.content.lower().split())
                words2 = set()
                for obs in s2.observations:
                    words2.update(obs.content.lower().split())

                overlap = words1 & words2
                # Filter common words
                stopwords = {"the", "a", "an", "is", "are", "was", "were", "be",
                             "been", "being", "have", "has", "had", "do", "does",
                             "did", "will", "would", "could", "should", "may",
                             "might", "can", "shall", "to", "of", "in", "for",
                             "on", "with", "at", "by", "from", "it", "this",
                             "that", "and", "or", "but", "not", "as"}
                meaningful = overlap - stopwords

                if len(meaningful) >= 3:
                    connections.append({
                        "session_a": s1.topic,
                        "session_b": s2.topic,
                        "shared_concepts": list(meaningful)[:10],
                        "strength": len(meaningful),
                    })

        return sorted(connections, key=lambda x: x["strength"], reverse=True)
