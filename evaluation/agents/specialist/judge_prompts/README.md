# Specialist Judge Prompts

This directory contains prompts for LLM Judge evaluation of specialist agents.

## Directory Structure

- `scoring/` - Prompts that return numeric scores (0.0-1.0) for specific evaluation dimensions
- `failure_analysis/` - Prompts that analyze failures and provide detailed recommendations for improvement

## Usage

### Scoring Prompts
Used during evaluation to score individual components of specialist performance:
- Medical accuracy
- Evidence quality  
- Clinical reasoning
- Specialty expertise
- Patient safety

### Failure Analysis Prompts
Used when a specialist fails to meet evaluation thresholds to:
- Identify root causes
- Provide specific recommendations
- Suggest prompt improvements

## Adding New Prompts

1. Scoring prompts should:
   - Request a single decimal score (0.0-1.0)
   - Focus on one specific aspect
   - Be concise and clear

2. Failure analysis prompts should:
   - Return structured JSON
   - Include root cause analysis
   - Provide actionable recommendations
   - Identify specific areas for improvement