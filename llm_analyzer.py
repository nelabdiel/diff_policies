import logging
import os
from typing import Dict, List, Optional

# Try to import Ollama, use fallback if not available
try:
    from ollama import Client
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

class LLMAnalyzer:
    """Handles LLM analysis for document comparison and summarization"""
    
    def __init__(self, model_name: str = 'llama3.2'):
        self.model_name = model_name
        self.logger = logging.getLogger(__name__)
        self.client = None
        
        if OLLAMA_AVAILABLE:
            try:
                # Initialize Ollama client following your pattern
                self.client = Client(host='http://localhost:11434')
                
                # Test connection with system message
                self.client.chat(model=self.model_name, messages=[
                    {'role': 'system', 'content': "You are a highly skilled policy analysis expert."}
                ])
                self.logger.info(f"Connected to Ollama with model: {model_name}")
                
            except Exception as e:
                self.logger.error(f"Failed to connect to Ollama: {str(e)}")
                self.client = None
        else:
            self.logger.info("Ollama not available, using fallback analysis")
    
    def generate_response(self, query: str, context: str) -> str:
        """
        Generate response using your preferred pattern
        
        Args:
            query: The question or analysis request
            context: The context or content to analyze
            
        Returns:
            Generated response
        """
        if not self.client:
            return self._generate_fallback_response(query, context)
        
        try:
            response = self.client.chat(model=self.model_name, messages=[
                {'role': 'user', 'content': f"Context:\n{context}\n\nQuestion: {query}\nAnswer:"}
            ])
            return response['message']['content']
        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            return self._generate_fallback_response(query, context)
    
    def _generate_fallback_response(self, query: str, context: str) -> str:
        """Generate a basic response when LLM is unavailable"""
        if "summary" in query.lower():
            words = context.split()[:50]
            sentences = context.split('.')[:2]
            preview = '. '.join(sentences).strip()
            return f"Document Preview: {preview}... Contains {len(context.split())} words. Full analysis available when connected to local AI service."
        elif "compare" in query.lower():
            return "Document comparison analysis requires AI service. Basic text differences available in detailed view."
        elif "analyze" in query.lower():
            word_count = len(context.split())
            return f"Document contains {word_count} words. Detailed analysis available when AI service is connected."
        else:
            return "Analysis requires AI service connection. Document processing completed with basic features."
    
    def analyze_section_change(self, old_text: str, new_text: str) -> str:
        """
        Analyze changes between two text sections
        
        Args:
            old_text: Original text
            new_text: Updated text
            
        Returns:
            Plain language summary of changes
        """
        if not self.client:
            return "LLM analysis unavailable - service not connected"
        
        try:
            prompt = f"""
            Analyze the changes between these two policy text sections and provide a clear, concise summary in plain language.

            ORIGINAL VERSION:
            {old_text[:2000]}

            NEW VERSION:
            {new_text[:2000]}

            Please provide:
            1. What changed (additions, removals, modifications)
            2. The significance of these changes
            3. Who might be affected by these changes
            4. Any terminology or requirement changes

            Keep your response focused and under 200 words.
            """
            
            response = self.client.chat(model=self.model_name, messages=[
                {
                    'role': 'system',
                    'content': 'You are a policy analysis expert who explains government document changes in clear, accessible language.'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ])
            
            return response['message']['content']
            
        except Exception as e:
            self.logger.error(f"Error analyzing section change: {str(e)}")
            return f"Analysis failed: {str(e)}"
    
    def generate_section_summary(self, section_text: str, change_type: str) -> str:
        """
        Generate a summary for a section based on its change type
        
        Args:
            section_text: The section text
            change_type: Type of change (added, removed, modified)
            
        Returns:
            Summary of the section
        """
        if not self.client:
            return f"Section {change_type} - LLM analysis unavailable"
        
        try:
            if change_type == 'added':
                prompt = f"Summarize this new policy section in 1-2 sentences: {section_text[:1000]}"
            elif change_type == 'removed':
                prompt = f"Summarize what was removed from this policy section in 1-2 sentences: {section_text[:1000]}"
            else:
                prompt = f"Summarize the key points of this policy section in 1-2 sentences: {section_text[:1000]}"
            
            response = self.client.chat(model=self.model_name, messages=[
                {
                    'role': 'system',
                    'content': 'You are a policy expert who creates concise summaries of government document sections.'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ])
            
            return response['message']['content']
            
        except Exception as e:
            self.logger.error(f"Error generating section summary: {str(e)}")
            return f"Summary generation failed for {change_type} section"
    
    def generate_overall_summary(self, comparison_result: Dict, doc1_title: str, doc2_title: str) -> str:
        """
        Generate an overall summary of document changes
        
        Args:
            comparison_result: The comparison result data
            doc1_title: Title of first document
            doc2_title: Title of second document
            
        Returns:
            Overall summary of changes
        """
        if not self.client:
            return "Overall analysis unavailable - LLM service not connected"
        
        try:
            # Extract key statistics
            total_sections = len(comparison_result.get('sections', []))
            added_sections = sum(1 for s in comparison_result.get('sections', []) if s.get('change_type') == 'added')
            removed_sections = sum(1 for s in comparison_result.get('sections', []) if s.get('change_type') == 'removed')
            modified_sections = sum(1 for s in comparison_result.get('sections', []) if s.get('change_type') == 'modified')
            
            # Create summary of major changes
            major_changes = []
            for section in comparison_result.get('sections', [])[:5]:  # Top 5 sections
                if section.get('change_type') in ['added', 'removed', 'modified']:
                    major_changes.append(f"- {section.get('title', 'Unnamed section')}: {section.get('change_type', 'changed')}")
            
            prompt = f"""
            Provide an executive summary comparing these two policy documents:

            Document 1: {doc1_title}
            Document 2: {doc2_title}

            Statistics:
            - Total sections analyzed: {total_sections}
            - New sections: {added_sections}
            - Removed sections: {removed_sections}
            - Modified sections: {modified_sections}

            Major changes:
            {chr(10).join(major_changes[:5])}

            Please provide:
            1. Overall assessment of the policy changes
            2. Key areas of impact
            3. Significance for stakeholders
            4. Notable trends or patterns in the changes

            Keep the summary under 300 words and focus on actionable insights.
            """
            
            response = self.client.chat(model=self.model_name, messages=[
                {
                    'role': 'system',
                    'content': 'You are a senior policy analyst who creates executive summaries of government document changes for decision-makers.'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ])
            
            return response['message']['content']
            
        except Exception as e:
            self.logger.error(f"Error generating overall summary: {str(e)}")
            return f"Overall summary generation failed: {str(e)}"
    
    def classify_change_impact(self, old_text: str, new_text: str) -> Dict[str, str]:
        """
        Classify the impact level and type of a change
        
        Args:
            old_text: Original text
            new_text: Updated text
            
        Returns:
            Dictionary with impact classification
        """
        if not self.client:
            return {
                'impact_level': 'unknown',
                'change_category': 'unknown',
                'stakeholder_impact': 'Unable to analyze - LLM service unavailable'
            }
        
        try:
            prompt = f"""
            Analyze this policy change and classify it:

            BEFORE: {old_text[:500]}
            AFTER: {new_text[:500]}

            Provide a JSON response with:
            - impact_level: "low", "medium", or "high"
            - change_category: "procedural", "requirements", "definitions", "scope", "compliance", or "other"
            - stakeholder_impact: brief description of who is most affected

            Respond only with valid JSON.
            """
            
            response = self.client.chat(model=self.model_name, messages=[
                {
                    'role': 'system',
                    'content': 'You are a policy analyst. Respond only with valid JSON.'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ])
            
            # Try to parse JSON response
            import json
            try:
                return json.loads(response['message']['content'])
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                content = response['message']['content']
                return {
                    'impact_level': 'medium',
                    'change_category': 'requirements',
                    'stakeholder_impact': content[:100] + '...' if len(content) > 100 else content
                }
            
        except Exception as e:
            self.logger.error(f"Error classifying change impact: {str(e)}")
            return {
                'impact_level': 'unknown',
                'change_category': 'error',
                'stakeholder_impact': f"Classification failed: {str(e)}"
            }
