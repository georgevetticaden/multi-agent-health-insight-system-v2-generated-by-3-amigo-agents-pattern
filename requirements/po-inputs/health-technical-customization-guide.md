# Health Insight System Technical Customization Guide

## Overview
This document provides health-specific technical requirements for the PM Agent when creating specifications for the Multi-Agent Health Insight System.

## Health-Specific Agent Configuration

### CMO (Chief Medical Officer) - Orchestrator
**Role**: Orchestrates medical specialist agents based on health query complexity
**Responsibilities**:
- Assess medical query complexity
- Determine which specialists are needed
- Coordinate specialist responses
- Synthesize medical insights
- Ensure comprehensive health analysis

### Medical Specialist Agents (Workers)

1. **Cardiology Specialist**
   - Analyzes cardiovascular health data
   - Interprets blood pressure, cholesterol, heart rate
   - Identifies cardiovascular risk factors

2. **Endocrinology Specialist**
   - Focuses on diabetes and metabolic health
   - Analyzes glucose, HbA1c, thyroid markers
   - Hormonal balance assessment

3. **Laboratory Medicine Specialist**
   - Interprets lab test results
   - Identifies abnormal values and trends
   - Correlates multiple test results

4. **Nutrition Specialist**
   - Analyzes dietary impacts on health
   - Provides nutritional recommendations
   - Assesses vitamin/mineral levels

5. **Pharmacy Specialist**
   - Reviews medications and interactions
   - Assesses medication effectiveness
   - Identifies potential side effects

6. **Preventive Medicine Specialist**
   - Calculates health risk scores
   - Recommends screening schedules
   - Focuses on disease prevention

7. **General Practice Specialist**
   - Provides holistic health view
   - Integrates findings from other specialists
   - Primary care perspective

8. **Data Analysis Specialist**
   - Statistical analysis of health trends
   - Pattern recognition in health data
   - Predictive health modeling

## Health Data Tools

### Pre-built Tool: execute_health_query_v2
**Purpose**: Natural language querying of health data
**Input Schema**:
```json
{
  "query": "string - natural language health question",
  "time_range": "optional - specific time period",
  "data_types": "optional - specific health metrics"
}
```
**Returns**: Structured health data based on query

### Pre-built Tool: snowflake_import_analyze_health_records_v2  
**Purpose**: Import and analyze comprehensive health records
**Input Schema**:
```json
{
  "patient_id": "string - patient identifier",
  "record_types": "array - types of records to import",
  "analysis_depth": "string - basic|comprehensive"
}
```
**Returns**: Imported health data with initial analysis

## Health-Specific Data Models

### HealthMetric
```json
{
  "metric_type": "lab_result|vital_sign|medication",
  "name": "string",
  "value": "number",
  "unit": "string",
  "reference_range": {
    "min": "number",
    "max": "number"
  },
  "status": "normal|borderline|critical",
  "date": "ISO 8601 timestamp"
}
```

### MedicalSpecialistTask
```json
{
  "specialist": "cardiology|endocrinology|etc",
  "task_description": "string",
  "priority": "high|medium|low",
  "data_required": ["array of data types"],
  "expected_duration": "seconds"
}
```

### HealthInsight
```json
{
  "specialist": "string",
  "finding": "string",
  "confidence": "number 0-1",
  "severity": "info|warning|critical",
  "recommendations": ["array of strings"],
  "supporting_data": ["array of metrics"]
}
```

## Health Query Complexity Rules

### Simple (1 specialist, <5 seconds)
- Single metric lookup ("What's my blood pressure?")
- Recent test results
- Current medications

### Standard (2-3 specialists, <15 seconds)
- Condition-specific analysis ("How's my diabetes?")
- Medication effectiveness
- Trend analysis

### Complex (4-6 specialists, <30 seconds)
- Comprehensive health assessment
- Multi-condition interactions
- Predictive health analysis

### Critical (All relevant specialists, priority processing)
- Urgent health concerns
- Multiple abnormal values
- Drug interaction warnings

## Health-Specific API Endpoints

### Health Analysis Stream
```
GET /api/health/analyze/stream?query={encoded_query}
```
- Streams real-time analysis from medical team
- Shows specialist activation and progress
- Returns synthesized health insights

### Health Data Import
```
POST /api/health/import
```
- Triggers health record import
- Processes various health data formats
- Returns import status and summary

### Health Metrics
```
GET /api/health/metrics?type={metric_type}&range={time_range}
```
- Retrieves specific health metrics
- Supports filtering and time ranges
- Returns structured metric data

## Health Visualization Requirements

### Required Chart Types
1. **Time Series**
   - Lab results over time
   - Vital sign trends
   - Medication timelines

2. **Comparison Charts**
   - Before/after medication changes
   - Multiple metric correlations
   - Reference range comparisons

3. **Risk Assessment**
   - Cardiovascular risk gauges
   - Diabetes risk indicators
   - Overall health scores

4. **Distribution Charts**
   - Blood pressure distributions
   - Glucose pattern analysis
   - Sleep quality patterns

## Health-Specific Performance Requirements

### Response Times
- Critical health queries: <2 seconds to start
- Simple lookups: <5 seconds total
- Complex analysis: <30 seconds total
- Emergency alerts: Immediate

### Data Processing
- Support 10+ years of health history
- Handle 50+ different lab test types
- Process medication interactions in real-time
- Correlate multiple health conditions

## Compliance and Security Notes

### HIPAA Considerations
- No PII in logs or error messages
- Encrypted data transmission
- Audit trails for data access
- Secure API endpoints

### Medical Disclaimers
- Not a replacement for medical advice
- Always consult healthcare providers
- Emergency situations require immediate medical attention

## Integration with Health Systems

### Data Sources (via tools)
- Electronic Health Records (EHR)
- Lab information systems
- Pharmacy records
- Wearable device data
- Patient-reported outcomes

### Export Capabilities
- PDF reports for physicians
- Structured data for EHR import
- Shareable visualizations
- Printable summaries

This customization guide should be provided to the PM Agent along with the generic multi-agent requirements to create health-specific technical specifications while maintaining the flexibility of the core agent system.