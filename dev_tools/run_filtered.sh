#!/bin/bash
# Run the Market Intelligence system with filtered output

echo "=== ULTRATHINK_QUANTITATIVE Market Intelligence System ==="
echo "Starting research process with filtered output..."
echo "------------------------------------------------------------"

# Run the system and filter out verbose messages
python -m department_of_market_intelligence.main 2>&1 | \
    grep -v "auth_config or auth_config.auth_scheme is missing" | \
    grep -v "UserWarning" | \
    grep -v "EXPERIMENTAL" | \
    grep -v "Using FunctionTool instead" | \
    grep -v "LiteLLM:WARNING" | \
    grep -v "utils.py:527" | \
    grep -v "ASYNC kwargs\[caching\]" | \
    grep -v "Final returned optional params" | \
    grep -v "Generating tools list" | \
    grep -v "super().__init__" | \
    grep -v "Loading server.ts" | \
    grep -v "Setting up request handlers" | \
    grep -v "Initialized FilteredStdioServerTransport" | \
    grep -v "Loading configuration" | \
    grep -v "Configuration loaded successfully" | \
    grep -v "Connecting server" | \
    grep -v "Server connected successfully" | \
    grep -E "(ROOT WORKFLOW|Chief_Researcher|Validator|Orchestrator|Coder|Executor|Starting|Complete|Error|write_file|read_file|task|plan|report)"