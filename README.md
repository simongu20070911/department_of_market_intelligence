# 🧠 ULTRATHINK_QUANTITATIVEMarketAlpha 

An advanced agentic research framework for quantitative finance research with **context-aware validation**.

## 🎯 Key Features

### 🔍 Context-Aware Validation System
- **Intelligent Context Detection**: Automatically detects what type of artifact is being validated
- **Specialized Validators**: Each research phase gets targeted validation criteria
- **Parallel Processing**: Multiple specialized validators run concurrently for comprehensive coverage
- **5 Validation Contexts**: Research plans, implementation manifests, code, experiments, results

### 🏗️ Multi-Agent Architecture
- **Chief Researcher**: Generates comprehensive research plans with statistical rigor
- **Orchestrator**: Creates maximally parallel implementation strategies 
- **Parallel Coders**: Execute independent coding tasks simultaneously
- **Experiment Executor**: Runs experiments with meticulous logging
- **Context-Aware Validators**: Junior, senior, and specialized parallel validation

### 🔄 Advanced Workflow Management
- **SessionState Model**: Type-safe state management with artifact-pointer pattern
- **Checkpoint System**: Automatic recovery and resumption capabilities
- **Sophisticated DAGs**: Parallel execution with precise stitching points
- **Dry Run Mode**: Early bug detection and workflow verification

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Google ADK (`pip install google-adk`)
- Custom Gemini endpoint (configured in config.py)

### Installation
```bash
git clone <repository>  
cd department_of_market_intelligence
pip install -r requirements.txt  # If available
```

### Configuration
```python
# config.py
ENABLE_CONTEXT_AWARE_VALIDATION = True  # Enable intelligent validation
CUSTOM_GEMINI_API_ENDPOINT = "http://0.0.0.0:8000"
CUSTOM_API_KEY = "sk-7m-daily-token-1"
```

### Run Research
```bash
python -m department_of_market_intelligence.main
```

## 🎯 Context-Aware Validation

The framework automatically detects what type of artifact is being validated and applies appropriate criteria:

| Phase | Context | Junior Validator Focus | Senior Validator Focus |
|-------|---------|----------------------|----------------------|
| **Planning** | `research_plan` | Data availability edge cases, Statistical assumptions | Statistical rigor, Hypothesis clarity, Data hygiene |
| **Implementation** | `implementation_manifest` | Missing dependencies, Resource conflicts | Parallelization efficiency, Alignment points |
| **Coding** | `code_implementation` | Critical bugs, Data leakage risks | Success criteria compliance, Statistical correctness |
| **Execution** | `experiment_execution` | Missing steps, Parameter errors | Protocol adherence, Reproducibility |
| **Results** | `results_extraction` | Missing outputs, Calculation errors | Question coverage, Interpretation validity |

## 🏗️ Architecture

### Core Agents
```
RootWorkflowAgent
├── ResearchPlanningWorkflow
│   ├── ChiefResearcher (planning)
│   ├── JuniorValidator (context-aware)
│   ├── SeniorValidator (context-aware) 
│   └── ParallelFinalValidation (specialized)
├── ImplementationWorkflow
│   ├── Orchestrator (task decomposition)
│   ├── ParallelCoders (independent execution)
│   ├── ExperimentExecutor (meticulous execution)
│   └── ContextAwareValidation (each phase)
└── ChiefResearcher (final reporting)
```

### State Management
- **SessionState Model**: Pydantic-based type safety
- **Artifact-Pointer Pattern**: Stores file paths, not large data
- **StateProxy**: Thread-safe state access
- **Checkpoint Recovery**: Automatic resumption from any point

### Validation Architecture
```
ValidationContextManager
├── Context Detection (phase/task-based)
├── Specialized Prompts (per context)
├── Parallel Validators
│   ├── StatisticalRigorValidator
│   ├── DataQualityValidator  
│   ├── MethodologyValidator
│   ├── EfficiencyValidator
│   └── GeneralValidator
└── Recursive Context Loading
```

## 📊 Example Workflow

### 1. Research Planning
```
Chief Researcher generates plan → 
Context-Aware Validation (research_plan) →
Focus: Statistical assumptions, data quality, experimental design
```

### 2. Implementation Planning  
```
Orchestrator creates manifest →
Context-Aware Validation (implementation_manifest) →
Focus: Parallelization efficiency, interface contracts
```

### 3. Parallel Coding
```
Multiple coders execute tasks →
Context-Aware Validation (code_implementation) →  
Focus: Critical bugs, data leakage, performance
```

### 4. Experiment Execution
```
Experiment Executor runs tests →
Context-Aware Validation (experiment_execution) →
Focus: Protocol adherence, completeness, reproducibility  
```

### 5. Results Extraction
```
Orchestrator creates extraction plan →
Context-Aware Validation (results_extraction) →
Focus: Question coverage, statistical accuracy
```

## 🧪 Testing

```bash
# Test context-aware validation
python -m tests.test_context_aware_validation

# Test full system integration  
python -m tests.test_full_context_aware_system

# Test SessionState model
python -m tests.test_session_state

# Test DAG parallelization
python -m tests.test_sophisticated_dag

# Run all tests
python -m tests.run_all_tests
```

## ⚙️ Configuration Options

```python
# Model Configuration
CHIEF_RESEARCHER_MODEL = "gemini-2.5-pro" 
ORCHESTRATOR_MODEL = "gemini-2.5-pro"
VALIDATOR_MODEL = "gemini-2.5-pro"

# Workflow Control
MAX_PLAN_REFINEMENT_LOOPS = 5
MAX_ORCHESTRATOR_REFINEMENT_LOOPS = 5
PARALLEL_VALIDATION_SAMPLES = 4

# Context-Aware Validation
ENABLE_CONTEXT_AWARE_VALIDATION = True

# Debugging
DRY_RUN_MODE = False
VERBOSE_LOGGING = False
```

## 📁 Project Structure

```
department_of_market_intelligence/
├── agents/                    # Core agent implementations
│   ├── chief_researcher.py   # Research planning and reporting
│   ├── orchestrator.py       # Task decomposition and coordination  
│   ├── validators_enhanced.py # Context-aware validation
│   └── experiment_executor.py # Experiment execution
├── workflows/                 # Workflow orchestration
│   ├── root_workflow_context_aware.py
│   ├── research_planning_workflow_context_aware.py
│   └── implementation_workflow_context_aware.py  
├── utils/                     # Utilities and helpers
│   ├── state_model.py        # Pydantic SessionState
│   ├── validation_context.py # Context detection
│   ├── checkpoint_manager.py # Recovery system
│   └── state_adapter.py      # State management
├── tests/                     # Comprehensive test suite
├── docs/                      # Documentation
├── tasks/                     # Research task definitions
└── main.py                   # Application entry point
```

## 🎉 Benefits

### 🎯 **Targeted Validation**
Each artifact type gets validation criteria specifically designed for its purpose

### ⚡ **Improved Efficiency** 
Parallel specialized validators catch issues faster with fewer false positives

### 🔍 **Comprehensive Coverage**
Domain-specific validators catch subtle issues that generic validation might miss

### 📊 **Better Research Quality**
Statistical rigor, data hygiene, and methodology get specialized attention

### 🚀 **Reduced Iteration Time**
More accurate validation reduces back-and-forth refinements

## 🔮 Advanced Features

- **Recursive Context Loading**: Senior validators can explore dependencies for deeper understanding
- **Checkpoint Recovery**: Resume from any point in the workflow
- **Dry Run Mode**: Test workflows without LLM calls
- **Sophisticated DAGs**: Partial completion with automatic stitching
- **Artifact Management**: File-based state with automatic versioning

## 📚 Documentation

- [Context-Aware Validation Guide](docs/context_aware_validation.md)
- [Implementation Summary](docs/CONTEXT_AWARE_VALIDATION_SUMMARY.md)  
- [Test Documentation](tests/README.md)

## 🤝 Contributing

This is a sophisticated agentic research framework designed for quantitative finance. When contributing:

1. Maintain type safety with Pydantic models
2. Follow the artifact-pointer pattern
3. Ensure context-aware validation compatibility
4. Add comprehensive tests
5. Update documentation

---

**🧠 ULTRATHINK_QUANTITATIVEMarketAlpha** - Where intelligent agents meet quantitative finance research.