#!/bin/bash

# Codexify - Project Agent Generator for OpenAI Codex
# This script reads a PR/pull request file and generates an AGENT.md file
# using OpenRouter API with various model options based on task complexity

set -euo pipefail

# Color codes for better UI
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$HOME/.codexify_config"
PR_FILE=""
API_KEY=""
BASE_URL="https://openrouter.ai/api/v1"

# Model configurations with pricing (per million tokens)
declare -A MODELS
declare -A MODEL_PRICES
declare -A MODEL_CATEGORIES

# Free/Low-cost models
MODELS["llama-3.1-8b-instruct:free"]="meta-llama/llama-3.1-8b-instruct:free"
MODEL_PRICES["llama-3.1-8b-instruct:free"]="FREE"
MODEL_CATEGORIES["llama-3.1-8b-instruct:free"]="free"

MODELS["mixtral-8x7b-instruct:free"]="mistralai/mixtral-8x7b-instruct:free"
MODEL_PRICES["mixtral-8x7b-instruct:free"]="FREE"
MODEL_CATEGORIES["mixtral-8x7b-instruct:free"]="free"

MODELS["gemma-2-9b:free"]="google/gemma-2-9b-it:free"
MODEL_PRICES["gemma-2-9b:free"]="FREE"
MODEL_CATEGORIES["gemma-2-9b:free"]="free"

# Mid-tier models
MODELS["gpt-4.1-mini"]="openai/gpt-4.1-mini"
MODEL_PRICES["gpt-4.1-mini"]="$0.15/$0.60"
MODEL_CATEGORIES["gpt-4.1-mini"]="mid"

MODELS["claude-3.5-sonnet"]="anthropic/claude-3.5-sonnet"
MODEL_PRICES["claude-3.5-sonnet"]="$3/$15"
MODEL_CATEGORIES["claude-3.5-sonnet"]="mid"

MODELS["gemini-1.5-flash"]="google/gemini-1.5-flash"
MODEL_PRICES["gemini-1.5-flash"]="$0.25/$1.25"
MODEL_CATEGORIES["gemini-1.5-flash"]="mid"

# High-end models
MODELS["gpt-4.1"]="openai/gpt-4.1"
MODEL_PRICES["gpt-4.1"]="$5/$15"
MODEL_CATEGORIES["gpt-4.1"]="high"

MODELS["claude-4-opus"]="anthropic/claude-4-opus"
MODEL_PRICES["claude-4-opus"]="$15/$75"
MODEL_CATEGORIES["claude-4-opus"]="high"

MODELS["gemini-1.5-pro"]="google/gemini-1.5-pro"
MODEL_PRICES["gemini-1.5-pro"]="$3.50/$10.50"
MODEL_CATEGORIES["gemini-1.5-pro"]="high"

# Function to display banner
display_banner() {
    echo -e "${CYAN}${BOLD}"
    echo "╔═══════════════════════════════════════════════════════╗"
    echo "║                    CODEXIFY v1.0                      ║"
    echo "║          Project Agent Generator for Codex            ║"
    echo "╚═══════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Function to load configuration
load_config() {
    if [[ -f "$CONFIG_FILE" ]]; then
        source "$CONFIG_FILE"
    fi
}

# Function to save configuration
save_config() {
    echo "API_KEY=\"$API_KEY\"" > "$CONFIG_FILE"
    chmod 600 "$CONFIG_FILE"
}

# Function to check and set API key
check_api_key() {
    if [[ -z "$API_KEY" ]]; then
        echo -e "${YELLOW}OpenRouter API key not found.${NC}"
        echo -e "${CYAN}Please enter your OpenRouter API key:${NC}"
        read -s API_KEY
        echo
        if [[ -n "$API_KEY" ]]; then
            save_config
            echo -e "${GREEN}✓ API key saved successfully${NC}"
        else
            echo -e "${RED}✗ API key is required to continue${NC}"
            exit 1
        fi
    fi
}

# Function to find PR file
find_pr_file() {
    local pr_files=(
        "PR.md" "pr.md" "PR.txt" "pr.txt" 
        "PULL_REQUEST.md" "pull_request.md"
        "pull-request.md" "PULL-REQUEST.md"
    )
    
    for file in "${pr_files[@]}"; do
        if [[ -f "$file" ]]; then
            PR_FILE="$file"
            echo -e "${GREEN}✓ Found PR file: $file${NC}"
            return 0
        fi
    done
    
    # If no standard PR file found, look for any file with PR in name
    local custom_pr=$(find . -maxdepth 1 -type f -name "*PR*" -o -name "*pr*" | head -n 1)
    if [[ -n "$custom_pr" ]]; then
        PR_FILE="$custom_pr"
        echo -e "${GREEN}✓ Found PR file: $custom_pr${NC}"
        return 0
    fi
    
    echo -e "${RED}✗ No PR file found in current directory${NC}"
    echo -e "${YELLOW}Please create a PR.md file with your pull request description${NC}"
    exit 1
}

# Function to display model selection menu
select_model() {
    echo -e "\n${CYAN}${BOLD}Select Model Based on Task Complexity:${NC}\n"
    
    echo -e "${GREEN}${BOLD}FREE MODELS (Rate Limited)${NC}"
    echo -e "${YELLOW}Best for: Simple code understanding, basic documentation${NC}"
    local i=1
    for model in "${!MODELS[@]}"; do
        if [[ "${MODEL_CATEGORIES[$model]}" == "free" ]]; then
            printf "%2d) %-25s %s\n" "$i" "$model" "${MODEL_PRICES[$model]}"
            ((i++))
        fi
    done
    
    echo -e "\n${BLUE}${BOLD}MID-TIER MODELS${NC}"
    echo -e "${YELLOW}Best for: Complex code analysis, detailed agent instructions${NC}"
    for model in "${!MODELS[@]}"; do
        if [[ "${MODEL_CATEGORIES[$model]}" == "mid" ]]; then
            printf "%2d) %-25s %s\n" "$i" "$model" "${MODEL_PRICES[$model]}"
            ((i++))
        fi
    done
    
    echo -e "\n${MAGENTA}${BOLD}HIGH-END MODELS${NC}"
    echo -e "${YELLOW}Best for: Architecture decisions, complex refactoring, critical systems${NC}"
    for model in "${!MODELS[@]}"; do
        if [[ "${MODEL_CATEGORIES[$model]}" == "high" ]]; then
            printf "%2d) %-25s %s\n" "$i" "$model" "${MODEL_PRICES[$model]}"
            ((i++))
        fi
    done
    
    echo -e "\n${CYAN}Enter your choice (1-$((i-1))):${NC}"
    read -r choice
    
    # Convert choice to model
    i=1
    for model in "${!MODELS[@]}"; do
        if [[ $i -eq $choice ]]; then
            SELECTED_MODEL="${MODELS[$model]}"
            SELECTED_MODEL_NAME="$model"
            echo -e "\n${GREEN}✓ Selected: $model (${MODEL_PRICES[$model]})${NC}"
            return 0
        fi
        ((i++))
    done
    
    echo -e "${RED}✗ Invalid selection${NC}"
    exit 1
}

# Function to read PR content
read_pr_content() {
    if [[ ! -f "$PR_FILE" ]]; then
        echo -e "${RED}✗ PR file not found: $PR_FILE${NC}"
        exit 1
    fi
    
    PR_CONTENT=$(cat "$PR_FILE")
    echo -e "${GREEN}✓ PR content loaded ($(wc -l < "$PR_FILE") lines)${NC}"
}

# Function to generate system prompt following GPT-4.1 best practices
generate_system_prompt() {
    cat << 'EOF'
<instructions>
You are an expert AI agent architect tasked with creating a comprehensive AGENT.md file for a software project. Your role is to analyze the provided pull request (PR) and generate detailed agent instructions that will enable AI models to understand and work with this codebase effectively.

## Core Responsibilities:
1. Analyze the PR to understand the project's purpose, architecture, and key changes
2. Generate a comprehensive AGENT.md that serves as the primary reference for AI agents
3. Follow the structured format provided below exactly
4. Be explicit and literal in all instructions (following GPT-4.1 best practices)

## AGENT.md Structure Requirements:

### 1. Project Overview
- Clear, concise description of what the project does
- Primary technologies and frameworks used
- Key architectural patterns and design decisions

### 2. Agent Mission
- Specific goals and responsibilities for AI agents working on this project
- Clear boundaries of what agents should and should not modify
- Performance metrics or quality standards to maintain

### 3. Codebase Structure
- Directory layout with descriptions
- Key files and their purposes
- Module dependencies and relationships
- Entry points and configuration files

### 4. Development Guidelines
- Coding standards and conventions
- Testing requirements
- Documentation standards
- Error handling patterns

### 5. Common Tasks
- Step-by-step instructions for frequent operations
- Examples with actual code snippets
- Troubleshooting guides

### 6. Technical Context
- External APIs or services used
- Database schemas or data models
- Authentication/authorization patterns
- Performance considerations

### 7. PR-Specific Instructions
- What changes the PR introduces
- Areas requiring special attention
- Migration steps if applicable
- Potential impacts on other systems

## Formatting Rules:
- Use clear markdown formatting
- Include code examples in appropriate language blocks
- Use XML-style tags for special sections: <important>, <warning>, <example>
- Provide explicit file paths and function names
- Number all sequential steps

## Quality Criteria:
- Instructions must be unambiguous and testable
- Include both positive examples (what to do) and negative examples (what to avoid)
- Prioritize clarity over brevity
- Assume the agent has no prior context beyond what you provide

Remember: You are creating the definitive guide for AI agents to work effectively on this project. Be thorough, explicit, and structured.
</instructions>

<examples>
<example type="codebase_structure">
## Codebase Structure

```
project-root/
├── src/
│   ├── components/     # React UI components
│   ├── services/       # API and business logic
│   ├── utils/          # Helper functions
│   └── types/          # TypeScript definitions
├── tests/              # Test files mirroring src/
├── config/             # Configuration files
└── scripts/            # Build and deployment scripts
```

Key files:
- `src/index.tsx`: Application entry point
- `src/services/api.ts`: Central API client
- `config/env.ts`: Environment configuration
</example>

<example type="task_instruction">
### Adding a New API Endpoint

1. Define the endpoint interface in `src/types/api.ts`:
   ```typescript
   export interface UserEndpoint {
     getUser(id: string): Promise<User>;
     updateUser(id: string, data: Partial<User>): Promise<User>;
   }
   ```

2. Implement the endpoint in `src/services/endpoints/user.ts`
3. Add tests in `tests/services/endpoints/user.test.ts`
4. Update the API documentation in `docs/api.md`

<warning>Never modify the base API client in `src/services/api.ts` without updating all endpoints</warning>
</example>
</examples>
EOF
}

# Function to create the API request
create_api_request() {
    local pr_content="$1"
    local system_prompt="$2"
    
    # Following GPT-4.1 sandwich method for long context
    local user_message="<context>
<document id=\"1\" title=\"Pull Request\">
$pr_content
</document>
</context>

Based on the pull request above, create a comprehensive AGENT.md file following all the instructions and format requirements provided in the system prompt.

<important>
Remember to:
1. Be explicit and literal in all instructions
2. Use the exact structure specified
3. Include concrete examples from the PR
4. Follow GPT-4.1 best practices for clarity
</important>"

    # Create JSON payload
    jq -n \
        --arg model "$SELECTED_MODEL" \
        --arg system "$system_prompt" \
        --arg user "$user_message" \
        '{
            model: $model,
            messages: [
                {role: "system", content: $system},
                {role: "user", content: $user}
            ],
            temperature: 0.7,
            max_tokens: 4000,
            stream: false
        }'
}

# Function to call OpenRouter API
call_openrouter_api() {
    local request_body="$1"
    
    echo -e "\n${YELLOW}⚡ Generating AGENT.md with $SELECTED_MODEL_NAME...${NC}"
    
    local response=$(curl -s -X POST "$BASE_URL/chat/completions" \
        -H "Authorization: Bearer $API_KEY" \
        -H "Content-Type: application/json" \
        -H "HTTP-Referer: https://github.com/yourusername/codexify" \
        -H "X-Title: Codexify" \
        -d "$request_body")
    
    # Check for errors
    if echo "$response" | jq -e '.error' > /dev/null 2>&1; then
        local error_msg=$(echo "$response" | jq -r '.error.message // .error')
        echo -e "${RED}✗ API Error: $error_msg${NC}"
        exit 1
    fi
    
    # Extract content
    local content=$(echo "$response" | jq -r '.choices[0].message.content // empty')
    if [[ -z "$content" ]]; then
        echo -e "${RED}✗ No content received from API${NC}"
        echo -e "${YELLOW}Response: $response${NC}"
        exit 1
    fi
    
    echo "$content"
}

# Function to save AGENT.md
save_agent_file() {
    local content="$1"
    
    # Add header to AGENT.md
    local header="<!-- 
Generated by Codexify v1.0
Model: $SELECTED_MODEL_NAME
Date: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
PR File: $PR_FILE
-->

"
    
    echo -e "$header$content" > AGENT.md
    echo -e "\n${GREEN}✓ AGENT.md created successfully!${NC}"
    echo -e "${CYAN}File location: $(pwd)/AGENT.md${NC}"
}

# Function to show usage
show_usage() {
    echo -e "${CYAN}Usage: $0 [OPTIONS]${NC}"
    echo -e "\nOptions:"
    echo -e "  -h, --help          Show this help message"
    echo -e "  -k, --key KEY       Set OpenRouter API key"
    echo -e "  -p, --pr FILE       Specify PR file (default: auto-detect)"
    echo -e "  -m, --model MODEL   Use specific model (skip selection menu)"
    echo -e "  --list-models       List all available models"
    echo -e "\nExamples:"
    echo -e "  $0                  # Interactive mode"
    echo -e "  $0 -p PR.md         # Use specific PR file"
    echo -e "  $0 -m gpt-4.1-mini  # Use specific model"
}

# Function to list models
list_models() {
    echo -e "${CYAN}${BOLD}Available Models:${NC}\n"
    printf "%-30s %-15s %s\n" "Model Name" "Category" "Price (Input/Output)"
    echo "────────────────────────────────────────────────────────────────"
    for model in "${!MODELS[@]}"; do
        printf "%-30s %-15s %s\n" "$model" "${MODEL_CATEGORIES[$model]}" "${MODEL_PRICES[$model]}"
    done | sort -k2,2 -k1,1
}

# Main execution
main() {
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_usage
                exit 0
                ;;
            -k|--key)
                API_KEY="$2"
                save_config
                shift 2
                ;;
            -p|--pr)
                PR_FILE="$2"
                shift 2
                ;;
            -m|--model)
                DIRECT_MODEL="$2"
                shift 2
                ;;
            --list-models)
                list_models
                exit 0
                ;;
            *)
                echo -e "${RED}Unknown option: $1${NC}"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # Display banner
    clear
    display_banner
    
    # Load configuration
    load_config
    
    # Check API key
    check_api_key
    
    # Find PR file if not specified
    if [[ -z "$PR_FILE" ]]; then
        find_pr_file
    fi
    
    # Read PR content
    read_pr_content
    
    # Select model (or use direct model if specified)
    if [[ -n "${DIRECT_MODEL:-}" ]]; then
        if [[ -n "${MODELS[$DIRECT_MODEL]:-}" ]]; then
            SELECTED_MODEL="${MODELS[$DIRECT_MODEL]}"
            SELECTED_MODEL_NAME="$DIRECT_MODEL"
            echo -e "${GREEN}✓ Using model: $DIRECT_MODEL${NC}"
        else
            echo -e "${RED}✗ Unknown model: $DIRECT_MODEL${NC}"
            exit 1
        fi
    else
        select_model
    fi
    
    # Generate system prompt
    local system_prompt=$(generate_system_prompt)
    
    # Create API request
    local request_body=$(create_api_request "$PR_CONTENT" "$system_prompt")
    
    # Call API and get response
    local agent_content=$(call_openrouter_api "$request_body")
    
    # Save AGENT.md
    save_agent_file "$agent_content"
    
    echo -e "\n${GREEN}${BOLD}✨ Codexify completed successfully!${NC}"
    echo -e "${CYAN}Your project is now ready for AI-powered development.${NC}\n"
}

# Check dependencies
check_dependencies() {
    local deps=("curl" "jq")
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            echo -e "${RED}✗ Missing dependency: $dep${NC}"
            echo -e "${YELLOW}Please install $dep to continue${NC}"
            exit 1
        fi
    done
}

# Run dependency check
check_dependencies

# Run main function
main "$@"