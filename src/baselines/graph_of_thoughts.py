"""
Graph of Thoughts for Medical Question Answering

Implements neurosymbolic reasoning using a graph structure:
- Nodes: Reasoning states (hypotheses, evidence, refinements)
- Edges: Transformations and dependencies
- Operations: Generate, Aggregate, Refine, Score

Reference: "Graph of Thoughts: Solving Elaborate Problems with Large Language Models"
"""

from typing import List, Dict, Any, Set, Optional
from dataclasses import dataclass
from enum import Enum
import json


class NodeType(Enum):
    """Types of nodes in the reasoning graph"""
    INITIAL = "initial"              # Initial problem understanding
    HYPOTHESIS = "hypothesis"        # Diagnostic hypothesis
    EVIDENCE = "evidence"            # Supporting/contradicting evidence
    REFINEMENT = "refinement"        # Refined hypothesis after evidence
    AGGREGATION = "aggregation"      # Aggregated reasoning
    DECISION = "decision"            # Final decision


@dataclass
class ThoughtNode:
    """A node in the graph of thoughts"""
    id: str
    type: NodeType
    content: str
    score: float = 0.0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ThoughtEdge:
    """An edge connecting two thoughts"""
    source_id: str
    target_id: str
    relation: str  # 'generates', 'supports', 'contradicts', 'refines', 'aggregates'
    weight: float = 1.0


class GraphOfThoughts:
    """
    Graph of Thoughts reasoning for medical QA.

    Architecture:
    1. Initialize: Understand the question
    2. Generate: Create multiple diagnostic hypotheses
    3. Evidence: Gather evidence for/against each hypothesis
    4. Refine: Update hypotheses based on evidence (with feedback)
    5. Aggregate: Combine refined hypotheses
    6. Decide: Make final decision
    """

    def __init__(self, llm_client, config):
        self.llm = llm_client
        self.config = config
        self.nodes: Dict[str, ThoughtNode] = {}
        self.edges: List[ThoughtEdge] = []
        self.node_counter = 0

    def _generate_node_id(self) -> str:
        """Generate unique node ID"""
        self.node_counter += 1
        return f"node_{self.node_counter}"

    def add_node(self, node_type: NodeType, content: str, score: float = 0.0,
                 metadata: Dict = None) -> str:
        """Add a node to the graph"""
        node_id = self._generate_node_id()
        node = ThoughtNode(
            id=node_id,
            type=node_type,
            content=content,
            score=score,
            metadata=metadata or {}
        )
        self.nodes[node_id] = node
        return node_id

    def add_edge(self, source_id: str, target_id: str, relation: str, weight: float = 1.0):
        """Add an edge between nodes"""
        edge = ThoughtEdge(source_id, target_id, relation, weight)
        self.edges.append(edge)

    def get_node(self, node_id: str) -> Optional[ThoughtNode]:
        """Get node by ID"""
        return self.nodes.get(node_id)

    def get_children(self, node_id: str) -> List[ThoughtNode]:
        """Get all children of a node"""
        child_ids = [e.target_id for e in self.edges if e.source_id == node_id]
        return [self.nodes[cid] for cid in child_ids if cid in self.nodes]

    def get_parents(self, node_id: str) -> List[ThoughtNode]:
        """Get all parents of a node"""
        parent_ids = [e.source_id for e in self.edges if e.target_id == node_id]
        return [self.nodes[pid] for pid in parent_ids if pid in self.nodes]

    def reason(self, question: str, options: List[str]) -> Dict[str, Any]:
        """
        Main reasoning loop using Graph of Thoughts.

        Returns:
            Dict with answer, reasoning, graph structure, and metrics
        """
        import time
        start_time = time.time()
        total_tokens = 0

        # Format options
        options_text = "\n".join([f"{chr(65+i)}. {opt}" for i, opt in enumerate(options)])

        # Step 1: Initialize - Understand the problem
        initial_id, tokens = self._initialize(question, options_text)
        total_tokens += tokens

        # Step 2: Generate - Create multiple hypotheses (high temperature)
        hypothesis_ids, tokens = self._generate_hypotheses(initial_id, question, options_text)
        total_tokens += tokens

        # Step 3: Evidence - Gather evidence for each hypothesis
        evidence_map, tokens = self._gather_evidence(hypothesis_ids, question, options_text)
        total_tokens += tokens

        # Step 4: Refine - Update hypotheses based on evidence (iterative)
        refined_ids, tokens = self._refine_hypotheses(hypothesis_ids, evidence_map,
                                                       question, options_text)
        total_tokens += tokens

        # Step 5: Aggregate - Combine all refined reasoning
        agg_id, tokens = self._aggregate_reasoning(refined_ids, question, options_text)
        total_tokens += tokens

        # Step 6: Decide - Make final deterministic decision
        decision_id, answer, reasoning, tokens = self._make_decision(agg_id, question, options_text)
        total_tokens += tokens

        latency = time.time() - start_time

        return {
            'answer': answer,
            'reasoning': reasoning,
            'graph': self._export_graph(),
            'tokens_used': total_tokens,
            'latency_seconds': latency,
            'num_nodes': len(self.nodes),
            'num_edges': len(self.edges)
        }

    def _initialize(self, question: str, options_text: str) -> tuple:
        """Step 1: Initialize reasoning by understanding the problem"""
        prompt = f"""Analyze this medical question and identify key clinical features.

Question: {question}

Options:
{options_text}

Provide a structured analysis:
1. Key symptoms/findings
2. Patient demographics if mentioned
3. Critical diagnostic clues
4. What makes this case interesting/challenging

Be concise but thorough."""

        response = self.llm.complete(
            prompt=prompt,
            temperature=0.7,  # Moderate temp for broad problem understanding
            max_tokens=self.config.max_output_tokens
        )

        node_id = self.add_node(
            NodeType.INITIAL,
            response.content,
            metadata={'question': question}
        )

        return node_id, response.tokens_used or 0

    def _generate_hypotheses(self, initial_id: str, question: str,
                            options_text: str, num_hypotheses: int = 4) -> tuple:
        """Step 2: Generate multiple diagnostic hypotheses"""
        initial_node = self.get_node(initial_id)

        prompt = f"""Based on this clinical analysis, generate {num_hypotheses} distinct diagnostic hypotheses.

Clinical Analysis:
{initial_node.content}

Question: {question}

Options:
{options_text}

For EACH of the 4 options (A, B, C, D), provide:
1. Why this diagnosis fits
2. What evidence supports it
3. Confidence level (0-1)

Format as JSON:
{{
  "A": {{"reasoning": "...", "confidence": 0.X}},
  "B": {{"reasoning": "...", "confidence": 0.X}},
  "C": {{"reasoning": "...", "confidence": 0.X}},
  "D": {{"reasoning": "...", "confidence": 0.X}}
}}"""

        response = self.llm.complete(
            prompt=prompt,
            temperature=1.0,  # Maximum temp for diverse hypotheses (matches V4 Parallel)
            max_tokens=self.config.max_output_tokens
        )

        # Parse hypotheses
        try:
            hypotheses = json.loads(response.content)
        except:
            # Fallback: create one hypothesis per option
            hypotheses = {chr(65+i): {"reasoning": "Generated hypothesis", "confidence": 0.25}
                         for i in range(4)}

        hypothesis_ids = []
        for option, data in hypotheses.items():
            h_id = self.add_node(
                NodeType.HYPOTHESIS,
                f"Option {option}: {data['reasoning']}",
                score=data.get('confidence', 0.5),
                metadata={'option': option}
            )
            self.add_edge(initial_id, h_id, 'generates')
            hypothesis_ids.append(h_id)

        return hypothesis_ids, response.tokens_used or 0

    def _gather_evidence(self, hypothesis_ids: List[str], question: str,
                        options_text: str) -> tuple:
        """Step 3: Gather evidence for/against each hypothesis"""
        evidence_map = {}
        total_tokens = 0

        for h_id in hypothesis_ids:
            hypothesis = self.get_node(h_id)
            option = hypothesis.metadata.get('option', '?')

            prompt = f"""Evaluate evidence for this diagnostic hypothesis.

Hypothesis: {hypothesis.content}

Question: {question}

Analyze:
1. Clinical findings that SUPPORT this diagnosis
2. Clinical findings that CONTRADICT this diagnosis
3. Missing information that would help confirm/rule out
4. Updated confidence (0-1)

Be specific and evidence-based."""

            response = self.llm.complete(
                prompt=prompt,
                temperature=0.7,  # Higher temp for thorough evidence exploration
                max_tokens=self.config.max_output_tokens
            )

            e_id = self.add_node(
                NodeType.EVIDENCE,
                response.content,
                metadata={'hypothesis_id': h_id, 'option': option}
            )
            self.add_edge(h_id, e_id, 'supports')
            evidence_map[h_id] = e_id
            total_tokens += response.tokens_used or 0

        return evidence_map, total_tokens

    def _refine_hypotheses(self, hypothesis_ids: List[str], evidence_map: Dict[str, str],
                          question: str, options_text: str, iterations: int = 1) -> tuple:
        """Step 4: Refine hypotheses based on evidence (with feedback loop)"""
        refined_ids = []
        total_tokens = 0

        for _ in range(iterations):
            current_refined = []

            for h_id in hypothesis_ids:
                hypothesis = self.get_node(h_id)
                evidence_id = evidence_map.get(h_id)
                evidence = self.get_node(evidence_id) if evidence_id else None

                # Get all current reasoning context
                all_hypotheses = "\n\n".join([
                    f"Option {self.get_node(hid).metadata.get('option')}: {self.get_node(hid).content}"
                    for hid in hypothesis_ids
                ])

                prompt = f"""Refine this hypothesis considering ALL evidence and competing diagnoses.

Original Hypothesis:
{hypothesis.content}

Evidence Analysis:
{evidence.content if evidence else 'No evidence yet'}

All Competing Hypotheses:
{all_hypotheses}

Question: {question}

Provide:
1. Refined hypothesis (updated reasoning)
2. How it compares to other options
3. Final confidence score (0-1)
4. Key discriminating factors

Format as JSON:
{{"refined_reasoning": "...", "confidence": 0.X, "key_factors": ["..."]}}"}}"""

                response = self.llm.complete(
                    prompt=prompt,
                    temperature=0.5,  # Balanced temp for refinement with cross-pollination
                    max_tokens=self.config.max_output_tokens
                )

                r_id = self.add_node(
                    NodeType.REFINEMENT,
                    response.content,
                    metadata={'original_hypothesis': h_id, 'option': hypothesis.metadata.get('option')}
                )
                self.add_edge(h_id, r_id, 'refines')
                if evidence:
                    self.add_edge(evidence_id, r_id, 'informs')

                current_refined.append(r_id)
                total_tokens += response.tokens_used or 0

            refined_ids = current_refined

        return refined_ids, total_tokens

    def _aggregate_reasoning(self, refined_ids: List[str], question: str,
                            options_text: str) -> tuple:
        """Step 5: Aggregate all refined reasoning"""
        # Gather all refined reasoning
        all_refined = "\n\n---\n\n".join([
            f"Option {self.get_node(r_id).metadata.get('option')}:\n{self.get_node(r_id).content}"
            for r_id in refined_ids
        ])

        prompt = f"""Synthesize all diagnostic reasoning into a comprehensive analysis.

All Refined Hypotheses:
{all_refined}

Question: {question}

Options:
{options_text}

Provide:
1. Comparative analysis of all options
2. Which diagnosis best fits ALL clinical findings
3. What rules out other options
4. Ranked ordering (1st, 2nd, 3rd, 4th choice)

Be deterministic and evidence-based."""

        response = self.llm.complete(
            prompt=prompt,
            temperature=0.0,  # Deterministic aggregation
            max_tokens=self.config.max_output_tokens
        )

        agg_id = self.add_node(
            NodeType.AGGREGATION,
            response.content
        )

        for r_id in refined_ids:
            self.add_edge(r_id, agg_id, 'aggregates')

        return agg_id, response.tokens_used or 0

    def _make_decision(self, agg_id: str, question: str, options_text: str) -> tuple:
        """Step 6: Make final deterministic decision"""
        aggregation = self.get_node(agg_id)

        prompt = f"""Make the final diagnostic decision.

Comprehensive Analysis:
{aggregation.content}

Question: {question}

Options:
{options_text}

Provide ONLY:
1. Final answer (single letter: A, B, C, or D)
2. Brief justification (2-3 sentences)

Format as JSON:
{{"answer": "X", "justification": "..."}}"}}"""

        response = self.llm.complete(
            prompt=prompt,
            temperature=0.0,  # Fully deterministic
            max_tokens=512
        )

        # Parse decision
        try:
            decision = json.loads(response.content)
            answer = decision.get('answer', 'A')
            justification = decision.get('justification', response.content)
        except:
            # Fallback: extract first letter
            content = response.content
            answer = next((c for c in content if c in 'ABCD'), 'A')
            justification = content

        decision_id = self.add_node(
            NodeType.DECISION,
            justification,
            metadata={'answer': answer}
        )
        self.add_edge(agg_id, decision_id, 'concludes')

        return decision_id, answer, justification, response.tokens_used or 0

    def _export_graph(self) -> Dict[str, Any]:
        """Export graph structure for analysis/visualization"""
        return {
            'nodes': [
                {
                    'id': node.id,
                    'type': node.type.value,
                    'content': node.content[:200] + '...' if len(node.content) > 200 else node.content,
                    'score': node.score,
                    'metadata': node.metadata
                }
                for node in self.nodes.values()
            ],
            'edges': [
                {
                    'source': edge.source_id,
                    'target': edge.target_id,
                    'relation': edge.relation,
                    'weight': edge.weight
                }
                for edge in self.edges
            ]
        }


def run_graph_of_thoughts(question: str, options: List[str], llm_client, config) -> Dict[str, Any]:
    """
    Main entry point for Graph of Thoughts reasoning.

    Args:
        question: Medical question text
        options: List of 4 answer options
        llm_client: LLM client instance
        config: Configuration object

    Returns:
        Dict with answer, reasoning, graph, and metrics
    """
    got = GraphOfThoughts(llm_client, config)
    result = got.reason(question, options)

    # Add graph visualization info
    result['graph_summary'] = {
        'num_nodes': len(got.nodes),
        'num_edges': len(got.edges),
        'node_types': {
            node_type.value: sum(1 for n in got.nodes.values() if n.type == node_type)
            for node_type in NodeType
        }
    }

    return result
