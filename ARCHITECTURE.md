# Architecture & Design Documentation

## Table of Contents

1. [System Overview](#system-overview)
2. [Design Principles](#design-principles)
3. [Core Architecture](#core-architecture)
4. [Component Design](#component-design)
5. [Data Flow](#data-flow)
6. [Extension Points](#extension-points)
7. [Research Methodology](#research-methodology)

## System Overview

### Purpose

This framework implements a **multi-agent code review system** using CrewAI to analyze pull requests and generate actionable, evidence-based review comments. It is designed as a master's thesis project to evaluate whether coordinated agent teams outperform single-agent baselines.

### Key Innovation

**Evidence Requirement**: Every finding must cite:
- Tool output (semgrep, ruff, bandit, eslint)
- Code reference (file:line with snippet)
- No speculative suggestions without proof

This ensures **low noise** and **high actionability**.

## Design Principles

### 1. SOLID Principles

**Single Responsibility**
- Each agent handles ONE concern (security, style, context)
- Each tool handles ONE type of analysis
- Each metric calculates ONE measurement

**Open/Closed**
- New agents: Extend `BaseAgent`
- New tools: Extend `BaseTool`
- New metrics: Extend `BaseMetric`
- Core framework unchanged

**Liskov Substitution**
- Any `BaseAgent` can be swapped
- Any `BaseTool` can be swapped
- Interfaces define behavior contracts

**Interface Segregation**
- Agents don't depend on tools they don't use
- Tools provide minimal interface (`run()`, `parse_output()`, `is_available()`)

**Dependency Inversion**
- High-level modules (flows) depend on abstractions (BaseAgent)
- Tools registered via registry (dependency injection pattern)

### 2. DRY (Don't Repeat Yourself)

- **Tool integration**: Shared `BaseTool` with common logic
- **Evidence validation**: Centralized in `BaseAgent._validate_findings()`
- **Prompt loading**: Shared `BaseAgent.load_prompt()`
- **Metric calculation**: Reusable `MetricsAggregator`

### 3. Separation of Concerns

```
Domain Models ──────► Pure data structures (Pydantic)
Tools ──────────────► External system integration
Agents ─────────────► Analysis logic + LLM calls
Flows ──────────────► Orchestration
Evaluation ─────────► Metrics and comparison
CLI ────────────────► User interface
```

## Core Architecture

### Layered Architecture

```
┌─────────────────────────────────────────┐
│         Presentation Layer              │
│  CLI (Typer) + Rich Output              │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│        Application Layer                │
│  ReviewFlow + ContextBuilder            │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│          Domain Layer                   │
│  Agents (CCA, SR, SFR, RP, Supervisor)  │
│  Models (PRContext, Finding, etc.)      │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│       Infrastructure Layer              │
│  Tools (Git, Ruff, Semgrep, etc.)       │
│  Storage (Artifacts, Results)           │
│  External APIs (OpenAI, Anthropic)      │
└─────────────────────────────────────────┘
```

### Agent Orchestration Pattern

**Pipeline Pattern** with parallel stages:

```
Input: PR + Repo
│
├─> ContextBuilder (sequential)
│   ├─> Git Diff
│   ├─> Ruff/ESLint (if applicable)
│   └─> Semgrep/Bandit
│
├─> Parallel Agents (concurrent)
│   ├─> CCA (Change & Context Analyst)
│   ├─> SR (Security Reviewer)
│   └─> SFR (Style & Format Reviewer)
│
├─> Revision Proposer (sequential)
│   └─> Generate patches from findings
│
├─> Supervisor (sequential)
│   └─> Validate, dedupe, prioritize
│
└─> Output: PRReviewResult
```

## Component Design

### 1. Domain Models (`domain/models.py`)

**Design Pattern**: Value Objects (immutable data)

Key models:
- `PRContext`: Complete PR information
- `Finding`: Single review issue
- `Evidence`: Tool output + code reference
- `PRReviewResult`: Complete review output
- `EvaluationResult`: Metrics for comparison

**Type Safety**: Pydantic v2 with strict validation

```python
class Finding(BaseModel):
    evidence: Evidence  # Required
    
    @field_validator("patch")
    def validate_patch_size(cls, v):
        # Enforce max patch size
```

### 2. Tools (`tools/`)

**Design Pattern**: Strategy Pattern + Registry

```python
class BaseTool(ABC):
    @abstractmethod
    def run(self, target_path, **kwargs) -> ToolResult:
        pass
    
    @abstractmethod
    def parse_output(self, output) -> Dict:
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        pass
```

**Tool Registry** (Dependency Injection):
```python
registry = ToolRegistry()
registry.register(RuffTool())
registry.register(SemgrepTool())

# Later...
tool = registry.get("ruff")
```

### 3. Agents (`agents/`)

**Design Pattern**: Template Method

```python
class BaseAgent(ABC):
    def analyze(self, context):
        # Template method
        findings = self._perform_analysis(context)  # Subclass implements
        validated = self._validate_findings(findings)  # Base class
        return self._create_decision(validated)      # Base class
    
    @abstractmethod
    def _perform_analysis(self, context):
        pass
```

**Specialization**:
- `ChangeContextAnalyst`: Uses LLM + diff analysis
- `SecurityReviewer`: Processes tool findings + LLM
- `StyleFormatReviewer`: Processes tool findings only
- `RevisionProposer`: Generates patches from findings
- `Supervisor`: Validates and consolidates

### 4. Flows (`flows/`)

**Design Pattern**: Façade + Coordinator

```python
class ReviewFlow:
    def run_multi_agent_review(self, pr_metadata, repo_path):
        # Build context
        context = self.context_builder.build_context(...)
        
        # Parallel agents
        decisions = self._run_parallel_agents(context)
        
        # Sequential post-processing
        decisions += [self._run_revision_proposer(...)]
        decisions += [self._run_supervisor(...)]
        
        # Synthesize output
        return self._synthesize_review(...)
```

### 5. Evaluation (`eval/`)

**Design Pattern**: Strategy Pattern for Metrics

```python
class MetricsAggregator:
    def register(self, metric: BaseMetric):
        self.metrics.append(metric)
    
    def evaluate(self, results, ground_truth):
        all_metrics = {}
        for metric in self.metrics:
            all_metrics.update(metric.calculate(...))
        return EvaluationResult(**all_metrics)
```

**Metric Implementations**:
- `ActionabilityMetric`: Findings with patches / total
- `NoiseMetric`: False positives / total
- `CoverageMetric`: Detected important issues / total
- `PerformanceMetric`: Time, cost, throughput

## Data Flow

### 1. Review Flow

```
PRMetadata + repo_path
    ↓
ContextBuilder.build_context()
    ├─> Git diff extraction
    ├─> Tool execution (ruff, semgrep, etc.)
    └─> PRContext {correlation_id, metadata, diff, tool_results}
    ↓
Parallel Agents
    ├─> CCA.analyze(context) → AgentDecision {findings: []}
    ├─> SR.analyze(context)  → AgentDecision {findings: []}
    └─> SFR.analyze(context) → AgentDecision {findings: []}
    ↓
RevisionProposer.analyze(context, upstream_decisions)
    └─> AgentDecision {findings: [...with patches]}
    ↓
Supervisor.analyze(context, all_decisions)
    ├─> Validate evidence
    ├─> Deduplicate
    ├─> Resolve conflicts
    ├─> Apply nit limit
    └─> AgentDecision {findings: [final list]}
    ↓
Synthesize
    ├─> Generate markdown comment
    ├─> Calculate costs
    └─> PRReviewResult
```

### 2. Evaluation Flow

```
Dataset (PR list + ground truth)
    ↓
For each PR:
    ReviewFlow.run_single_agent_review()  → PRReviewResult
    ReviewFlow.run_multi_agent_review()   → PRReviewResult
    ↓
MetricsAggregator
    ├─> ActionabilityMetric.calculate()
    ├─> NoiseMetric.calculate()
    ├─> CoverageMetric.calculate()
    └─> ...
    ↓
EvaluationResult {actionability, noise, coverage, ...}
    ↓
Statistical Tests
    ├─> Chi-square (proportions)
    ├─> Wilcoxon (paired samples)
    └─> Mann-Whitney (independent samples)
    ↓
LaTeX Export (for thesis)
```

## Extension Points

### Adding a New Agent

1. **Create agent class**:
```python
# agents/my_agent.py
class MyAgent(BaseAgent):
    def __init__(self, settings):
        super().__init__(AgentRole.MY_AGENT, settings)
    
    def analyze(self, context):
        # Your logic
        findings = [...]
        return self._create_decision(...)
```

2. **Add role to enum**:
```python
# domain/models.py
class AgentRole(str, Enum):
    MY_AGENT = "MA"
```

3. **Create prompt**:
```markdown
# prompts/my_agent/v1.md
Your instructions...
```

4. **Register in flow**:
```python
# flows/review_flow.py
def _run_parallel_agents(self, context):
    my_agent = MyAgent(self.settings)
    decisions.append(my_agent.analyze(context))
```

### Adding a New Tool

1. **Implement tool**:
```python
# tools/my_tool.py
class MyTool(BaseTool):
    def run(self, target_path, **kwargs):
        # Execute tool
        return ToolResult(...)
    
    def parse_output(self, output):
        # Parse JSON/XML/etc.
        return {...}
    
    def is_available(self):
        # Check if installed
        return True
```

2. **Register in factory**:
```python
# tools/factory.py
def create_tool_registry(settings):
    registry.register(MyTool(settings.my_tool_path))
```

### Adding a New Metric

1. **Implement metric**:
```python
# eval/metrics/my_metric.py
class MyMetric(BaseMetric):
    def calculate(self, results, ground_truth):
        # Compute metric
        return {"my_metric": value}
```

2. **Register in evaluation**:
```python
# eval/run_eval.py
aggregator.register(MyMetric())
```

## Research Methodology

### Hypothesis

**H1**: Multi-agent code review with tool integration achieves higher actionability than single-agent baseline.

**H2**: Multi-agent system produces less noise (fewer false positives).

**H3**: Multi-agent system has better coverage of important issues.

### Experimental Design

**Independent Variable**: Review system type
- Baseline: Single agent (CCA only)
- Proposed: Multi-agent (CCA + SR + SFR + RP + Supervisor)

**Dependent Variables**:
1. Actionability rate (has_patch or severity≥major)
2. Noise rate (false positives / total)
3. Important issue coverage (detected / total)

**Controls**:
- Same LLM model (GPT-4-turbo)
- Same temperature (0.0)
- Same seed (42)
- Same tool versions (pinned in pyproject.toml)
- Same dataset (20-30 PRs)

**Procedure**:
1. Prepare dataset with ground truth labels (2+ experts, Cohen's κ)
2. Run both systems on each PR
3. Calculate metrics
4. Statistical significance testing (chi-square, Wilcoxon)
5. Effect size calculation (Cohen's d)

### Validity Threats

**Internal Validity**:
- **Mitigation**: Deterministic settings, seed control, pinned versions

**External Validity**:
- **Limitation**: Dataset size (20-30 PRs), single language ecosystem
- **Mitigation**: Diverse PR types, real OSS projects

**Construct Validity**:
- **Threat**: "Actionability" definition subjective
- **Mitigation**: Clear operationalization (has_patch OR severity≥major)

## Configuration & Deployment

### Environment Variables

```env
# Required
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo-preview

# Determinism
OPENAI_TEMPERATURE=0.0
OPENAI_SEED=42

# Limits
MAX_NITS_PER_REVIEW=5
MAX_PATCH_LINES=10

# Evaluation
SEED_FOR_EXPERIMENTS=42
```

### Single Environment (Production)

As per requirements, only one environment:
- No dev/staging distinction
- Configuration via .env only
- Explicit versioning in code (prompt_version, tool versions)

### Tool Installation

```bash
# Core framework
poetry install

# Optional analysis tools
poetry install --with tools

# Verify
poetry run code-review --help
```

## Performance Considerations

### Parallelization

Agents CCA, SR, SFR run in parallel when `ENABLE_PARALLEL_AGENTS=true`.

Current: Sequential (for determinism)
Future: Threading/asyncio for speed

### Caching

Tools results cached in `PRContext.tool_results` to avoid re-running same tool.

### Token Usage

Estimated costs logged in `PRReviewResult.token_cost_estimate`.

Typical PR (200 lines):
- Single-agent: ~500 tokens = $0.005
- Multi-agent: ~2000 tokens = $0.02

## Testing Strategy

### Unit Tests
- Domain models validation
- Tool parsing logic
- Metric calculations
- Individual agent logic

### Integration Tests
- Tool availability checks
- Full review flow (mocked LLM)

### E2E Tests
- Complete review on test PR
- Evaluation pipeline

### Coverage Target
- Core: >80%
- Tools: >70% (depends on tool availability)
- Agents: >60% (LLM interactions hard to test)

## Logging & Observability

### Structured Logging

```python
{
  "timestamp": "2025-11-22T10:30:00Z",
  "level": "INFO",
  "correlation_id": "uuid",
  "agent_role": "SR",
  "message": "Security analysis complete",
  "findings_count": 5
}
```

### Traceability

Every object linked via `correlation_id`:
- `PRContext.correlation_id`
- `PRReviewResult.correlation_id`
- Logs include correlation_id

Follow a review end-to-end by searching logs for UUID.

## Conclusion

This architecture prioritizes:
1. **Research validity**: Deterministic, reproducible, traceable
2. **Code quality**: SOLID, DRY, testable
3. **Extensibility**: Easy to add agents, tools, metrics
4. **Thesis focus**: Clean data flow, clear evaluation framework

Every design decision supports the research hypothesis and methodology.

