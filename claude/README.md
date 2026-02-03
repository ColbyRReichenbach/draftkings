# DK Sentinel Claude Code Configuration

**Project**: Responsible Gaming Intelligence System  
**Purpose**: Production-ready analytics platform for behavioral risk detection

---

## Quick Start
```bash
# Navigate to project
cd ~/Desktop/dk-sentinel-rg-analytics

# Start Claude Code
claude

# First command (press Shift+Tab twice for Plan Mode)
"Review CLAUDE.md and propose first 3 tasks for Week 1: Data Foundation"
```

---

## Directory Structure
```
claude/
├── README.md                       # This file
├── skills/                         # Auto-invoked domain expertise
│   ├── dbt-transformations.md      # dbt best practices
│   ├── behavioral-analytics.md     # Risk scoring domain knowledge
│   ├── llm-integration.md          # Claude API patterns
│   └── validate-pipeline.md        # Data quality validation workflow
├── agents/                         # Specialized subagents
│   ├── data-quality-tester.md      # Testing specialist
│   ├── compliance-validator.md     # Regulatory compliance expert
│   ├── dbt-architect.md            # dbt modeling expert
│   ├── python-backend-dev.md       # FastAPI backend developer
│   └── react-ui-developer.md       # Frontend React developer
├── workflows/                      # Step-by-step procedures
│   ├── create-new-risk-feature.md  # Add new behavioral indicator
│   └── deploy-dbt-model.md         # Production deployment process
└── context/                        # Reference documentation
    ├── business_logic.md           # Risk calculations & thresholds
    ├── data_dictionary.md          # Complete schema reference
    ├── stakeholder_requirements.md # Job alignment & success criteria
    └── architecture.md             # System design & tech stack
```

---

## How to Use

### 1. Skills (Auto-Invoked)
Claude automatically loads relevant skills based on your request. No explicit invocation needed.

**Example**:
```
You: "Create int_loss_chasing_indicators.sql"
Claude: [Automatically loads dbt-transformations.md skill]
```

### 2. Agents (Delegated Tasks)
Use `@agent-name` or "use subagents" to delegate specialized work.

**Example**:
```
You: "Use subagents. Have @data-quality-tester write comprehensive tests for the new model."
Claude: [Spawns testing agent with isolated context]
```

### 3. Workflows (Step-by-Step)
Follow workflows for complex multi-phase tasks.

**Example**:
```
You: "Walk me through the create-new-risk-feature workflow for deposit_frequency_score"
Claude: [Loads workflow and guides through each phase]
```

### 4. Context Files (Reference)
Claude references these automatically when relevant. You can also request explicitly.

**Example**:
```
You: "What are the risk category thresholds?"
Claude: [References business_logic.md]
```

---

## Best Practices

✅ **DO**:
- Start complex tasks in Plan Mode (Shift+Tab twice)
- Use voice dictation (Fn+Fn) for detailed prompts
- Update CLAUDE.md after each correction
- Use /validate-pipeline before committing changes
- Delegate testing to @data-quality-tester

❌ **DON'T**:
- Skip Plan Mode for multi-file changes
- Implement without reading relevant skills first
- Commit without running tests
- Ignore compliance validation for customer-facing features

---

## Common Commands
```bash
# Validate full pipeline
/validate-pipeline

# Generate and serve dbt docs
/dbt-docs

# Smart git commit (future custom command)
/commit
```

---

## Week-by-Week Guide

**Week 1-2**: Data Foundation  
→ Use Plan Mode + voice dictation  
→ Update CLAUDE.md after corrections  

**Week 3-4**: dbt Development  
→ @dbt-architect for modeling  
→ @data-quality-tester for tests  
→ /validate-pipeline frequently  

**Week 5**: AI Integration  
→ llm-integration.md skill  
→ @compliance-validator for nudges  

**Week 6-7**: Dashboard  
→ @react-ui-developer for components  
→ Git worktrees for parallel work (optional)  

**Week 8**: Testing & Docs  
→ Comprehensive testing with agents  
→ Final CLAUDE.md refinement  

---

## Troubleshooting

**Issue**: "Claude isn't using the skills"  
**Fix**: Skills auto-load based on keywords. Try more specific requests (e.g., "Create incremental dbt model" triggers dbt-transformations skill)

**Issue**: "Subagent isn't working"  
**Fix**: Use explicit syntax: `@agent-name` or "Use subagents, have @agent-name do X"

**Issue**: "Workflow too rigid"  
**Fix**: Workflows are guides, not scripts. Adapt steps as needed for your specific task

---

## Version History

- **v1.0** (2026-02-01): Initial configuration based on Boris's best practices
- **v1.1** (TBD): Post-Week 4 refinement with lessons learned

---

**For full project context, start with**: `CLAUDE.md` (root configuration)
