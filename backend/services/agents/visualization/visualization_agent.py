"""
Medical Visualization Agent

Generates self-contained React visualizations with embedded data.
Creates compelling, data-driven visualizations that tell a complete story.
"""

import json
import logging
import asyncio
import re
from typing import Dict, List, Any, AsyncGenerator, Tuple, Optional
from dataclasses import dataclass

from anthropic import Anthropic

from services.agents.specialist.specialist_agent import SpecialistResult
from services.agents.visualization.prompts import VisualizationPrompts
from utils.anthropic_client import AnthropicStreamingClient
from utils.anthropic_streaming import StreamingMode

logger = logging.getLogger(__name__)


class MedicalVisualizationAgent:
    """
    Medical Visualization Agent - Generates self-contained React visualizations
    
    Key features:
    - Embeds data directly in the visualization code
    - Extracts specific data points from specialist results and synthesis
    - Creates visualizations that directly match the CMO synthesis
    """
    
    def __init__(
        self, 
        anthropic_client: Anthropic,
        model: str,
        max_tokens: int = 16384
    ):
        self.client = anthropic_client
        self.model = model
        self.max_tokens = max_tokens
        self.prompts = VisualizationPrompts()
        self.streaming_client = AnthropicStreamingClient(anthropic_client)
        
    async def stream_visualization(
        self,
        query: str,
        specialist_results: List[SpecialistResult],
        synthesis_text: str = ""
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream self-contained visualization code with embedded data"""
        
        # Extract key data points from specialist results and synthesis
        key_data_points = self._extract_key_data_points(specialist_results, synthesis_text)
        
        # Detect query type
        query_type = self._detect_query_type(query)
        
        # Count total results for context
        total_results = sum(
            len(data.get('results', [])) 
            for result in specialist_results 
            for data in result.data_points.values() 
            if 'results' in data
        )
        
        # Generate the visualization prompt
        prompt = self.prompts.get_generation_prompt(
            query=query,
            query_type=query_type,
            synthesis_text=synthesis_text,
            key_data_points=key_data_points,
            result_count=total_results
        )
        
        # Log the visualization prompt for debugging
        logger.info("\n" + "=" * 80)
        logger.info("VISUALIZATION PROMPT")
        logger.info("=" * 80)
        logger.info(prompt[:1000] + "..." if len(prompt) > 1000 else prompt)
        logger.info("=" * 80 + "\n")

        # Use streaming utility for visualization generation
        async for chunk in self.streaming_client.stream_visualization(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=self.max_tokens,
            context_label="Visualization generation"
        ):
            yield chunk
    
    def _extract_key_data_points(
        self, 
        specialist_results: List[SpecialistResult], 
        synthesis_text: str
    ) -> Dict[str, Any]:
        """Extract key data points mentioned in the synthesis"""
        
        key_data = {
            "mentioned_values": [],
            "date_ranges": [],
            "trends": [],
            "comparisons": [],
            "medications": [],
            "abnormal_results": []
        }
        
        # Extract numeric values with their context from synthesis
        # Pattern: number followed by unit and context
        value_pattern = r'(\d+(?:\.\d+)?)\s*(mg/dL|%|lbs|kg|mmHg|/min|bpm)\s*(?:\(([^)]+)\))?'
        for match in re.finditer(value_pattern, synthesis_text):
            value = float(match.group(1))
            unit = match.group(2)
            context = match.group(3) or ""
            
            # Try to identify what this value represents
            # Look at surrounding text (50 chars before and after)
            start = max(0, match.start() - 50)
            end = min(len(synthesis_text), match.end() + 50)
            surrounding_text = synthesis_text[start:end]
            
            key_data["mentioned_values"].append({
                "value": value,
                "unit": unit,
                "context": context,
                "surrounding_text": surrounding_text
            })
        
        # Extract date mentions
        date_pattern = r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b|\b\d{4}\b|\b\d{1,2}/\d{1,2}/\d{2,4}\b'
        for match in re.finditer(date_pattern, synthesis_text):
            key_data["date_ranges"].append(match.group())
        
        # Extract trend descriptions
        trend_keywords = [
            "increased", "decreased", "improved", "worsened", "stable", "rising", 
            "falling", "dropped", "climbed", "unchanged", "deteriorated"
        ]
        for keyword in trend_keywords:
            if keyword in synthesis_text.lower():
                # Get context around the trend
                pattern = rf'([^.]+{keyword}[^.]+)'
                for match in re.finditer(pattern, synthesis_text, re.IGNORECASE):
                    key_data["trends"].append(match.group(1).strip())
        
        # Extract medication mentions
        med_pattern = r'\b(metformin|rosuvastatin|ezetimibe|atorvastatin|simvastatin|pravastatin|insulin|glipizide|lisinopril|amlodipine|losartan)\b'
        for match in re.finditer(med_pattern, synthesis_text, re.IGNORECASE):
            medication = match.group(1).lower()
            if medication not in [m["name"] for m in key_data["medications"]]:
                # Get dosage if mentioned nearby
                dose_pattern = rf'{medication}\s*(?:dose|dosage)?\s*(?:of)?\s*(\d+(?:\.\d+)?)\s*(mg|mcg|units?)'
                dose_match = re.search(dose_pattern, synthesis_text, re.IGNORECASE)
                
                key_data["medications"].append({
                    "name": medication,
                    "dose": f"{dose_match.group(1)} {dose_match.group(2)}" if dose_match else None
                })
        
        # Extract abnormal results mentioned
        abnormal_keywords = ["abnormal", "elevated", "high", "low", "concerning", "critical", "above normal", "below normal"]
        for keyword in abnormal_keywords:
            pattern = rf'([^.]+{keyword}[^.]+)'
            for match in re.finditer(pattern, synthesis_text, re.IGNORECASE):
                key_data["abnormal_results"].append(match.group(1).strip())
        
        # Also extract structured data from specialist results
        for result in specialist_results:
            for key, data_point in result.data_points.items():
                if 'results' in data_point and data_point['results']:
                    # Add to our extraction
                    for record in data_point['results'][:20]:  # Sample to avoid too much data
                        # Extract relevant fields based on record structure
                        if 'TEST_NAME' in record and 'RESULT_VALUE' in record:
                            key_data["mentioned_values"].append({
                                "test": record.get('TEST_NAME'),
                                "value": record.get('RESULT_VALUE'),
                                "unit": record.get('RESULT_UNIT'),
                                "date": record.get('RECORD_DATE'),
                                "reference": record.get('REFERENCE_RANGE')
                            })
        
        return key_data
    
    def _detect_query_type(self, query: str) -> str:
        """Detect the type of query for appropriate visualization"""
        query_lower = query.lower()
        
        # Time series patterns
        if any(word in query_lower for word in ['trend', 'over time', 'history', 'progression', 'timeline']):
            return 'time_series'
        
        # Abnormal results patterns
        if any(word in query_lower for word in ['abnormal', 'high', 'low', 'critical', 'concerning', 'out of range']):
            return 'abnormal_results'
        
        # Medication patterns
        if any(word in query_lower for word in ['medication', 'drug', 'prescription', 'adherence', 'compliance']):
            return 'medication_adherence'
        
        # Correlation patterns
        if any(word in query_lower for word in ['correlation', 'relationship', 'impact', 'affect', 'influence']):
            return 'correlation'
        
        # Before/after patterns
        if any(word in query_lower for word in ['before', 'after', 'change', 'improvement', 'difference']):
            return 'before_after'
        
        # Default to time series for general queries
        return 'time_series'