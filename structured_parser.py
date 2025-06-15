import json
import logging
from typing import Dict, List, Optional, Any
from llm_analyzer import LLMAnalyzer

class StructuredDocumentParser:
    """Parses policy documents to extract structured elements like definitions, requirements, actions, and deadlines"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.llm_analyzer = LLMAnalyzer()
    
    def parse_document(self, text: str, title: str = "") -> Dict[str, Any]:
        """
        Parse a document to extract structured elements
        
        Args:
            text: Document text
            title: Document title
            
        Returns:
            Dictionary with structured elements
        """
        try:
            # Extract different document elements
            definitions = self._extract_definitions(text)
            requirements = self._extract_requirements(text)
            actions = self._extract_actions(text)
            deadlines = self._extract_deadlines(text)
            summary = self._generate_summary(text, title)
            
            return {
                'title': title,
                'summary': summary,
                'definitions': definitions,
                'requirements': requirements,
                'actions': actions,
                'deadlines': deadlines,
                'word_count': len(text.split()),
                'section_count': len([line for line in text.split('\n') if line.strip() and any(keyword in line.upper() for keyword in ['SECTION', 'ARTICLE', 'PART', 'CHAPTER'])])
            }
            
        except Exception as e:
            self.logger.error(f"Error parsing document: {str(e)}")
            return self._create_fallback_structure(text, title)
    
    def _extract_definitions(self, text: str) -> List[Dict[str, str]]:
        """Extract definitions from the document"""
        prompt = """
        Extract all definitions from this policy document. Look for terms that are explicitly defined, 
        often appearing after phrases like "means", "is defined as", "refers to", or in dedicated definition sections.
        
        Return a JSON list of objects with this structure:
        [{"term": "term name", "definition": "definition text", "context": "surrounding context"}]
        
        Only include actual definitions, not general descriptions. If no definitions are found, return an empty list.
        
        Document text:
        """
        
        try:
            response = self.llm_analyzer.generate_response(prompt, text)
            definitions = self._parse_json_response(response, [])
            
            # Validate and clean definitions
            cleaned_definitions = []
            for defn in definitions:
                if isinstance(defn, dict) and 'term' in defn and 'definition' in defn:
                    cleaned_definitions.append({
                        'term': str(defn.get('term', '')).strip(),
                        'definition': str(defn.get('definition', '')).strip(),
                        'context': str(defn.get('context', '')).strip()
                    })
            
            return cleaned_definitions[:10]  # Limit to 10 definitions
            
        except Exception as e:
            self.logger.error(f"Error extracting definitions: {str(e)}")
            return []
    
    def _extract_requirements(self, text: str) -> List[Dict[str, str]]:
        """Extract requirements and obligations from the document"""
        prompt = """
        Extract all requirements, obligations, and mandatory actions from this policy document.
        Look for phrases like "must", "shall", "required to", "obligated to", "mandatory".
        
        Return a JSON list of objects with this structure:
        [{"requirement": "requirement text", "applies_to": "who it applies to", "priority": "high/medium/low"}]
        
        If no requirements are found, return an empty list.
        
        Document text:
        """
        
        try:
            response = self.llm_analyzer.generate_response(prompt, text)
            requirements = self._parse_json_response(response, [])
            
            # Validate and clean requirements
            cleaned_requirements = []
            for req in requirements:
                if isinstance(req, dict) and 'requirement' in req:
                    cleaned_requirements.append({
                        'requirement': str(req.get('requirement', '')).strip(),
                        'applies_to': str(req.get('applies_to', 'All parties')).strip(),
                        'priority': str(req.get('priority', 'medium')).strip().lower()
                    })
            
            return cleaned_requirements[:15]  # Limit to 15 requirements
            
        except Exception as e:
            self.logger.error(f"Error extracting requirements: {str(e)}")
            return []
    
    def _extract_actions(self, text: str) -> List[Dict[str, str]]:
        """Extract specific actions and procedures from the document"""
        prompt = """
        Extract specific actions, procedures, and steps outlined in this policy document.
        Look for actionable items, processes, and procedures that need to be followed.
        
        Return a JSON list of objects with this structure:
        [{"action": "action description", "responsible_party": "who is responsible", "timeline": "when it should be done"}]
        
        If no specific actions are found, return an empty list.
        
        Document text:
        """
        
        try:
            response = self.llm_analyzer.generate_response(prompt, text)
            actions = self._parse_json_response(response, [])
            
            # Validate and clean actions
            cleaned_actions = []
            for action in actions:
                if isinstance(action, dict) and 'action' in action:
                    cleaned_actions.append({
                        'action': str(action.get('action', '')).strip(),
                        'responsible_party': str(action.get('responsible_party', 'Not specified')).strip(),
                        'timeline': str(action.get('timeline', 'Not specified')).strip()
                    })
            
            return cleaned_actions[:12]  # Limit to 12 actions
            
        except Exception as e:
            self.logger.error(f"Error extracting actions: {str(e)}")
            return []
    
    def _extract_deadlines(self, text: str) -> List[Dict[str, str]]:
        """Extract deadlines and time-sensitive information"""
        prompt = """
        Extract all deadlines, dates, and time-sensitive information from this policy document.
        Look for specific dates, timeframes, and deadlines mentioned in the text.
        
        Return a JSON list of objects with this structure:
        [{"deadline": "date or timeframe", "description": "what needs to be done", "consequence": "what happens if missed"}]
        
        If no deadlines are found, return an empty list.
        
        Document text:
        """
        
        try:
            response = self.llm_analyzer.generate_response(prompt, text)
            deadlines = self._parse_json_response(response, [])
            
            # Validate and clean deadlines
            cleaned_deadlines = []
            for deadline in deadlines:
                if isinstance(deadline, dict) and 'deadline' in deadline:
                    cleaned_deadlines.append({
                        'deadline': str(deadline.get('deadline', '')).strip(),
                        'description': str(deadline.get('description', '')).strip(),
                        'consequence': str(deadline.get('consequence', 'Not specified')).strip()
                    })
            
            return cleaned_deadlines[:8]  # Limit to 8 deadlines
            
        except Exception as e:
            self.logger.error(f"Error extracting deadlines: {str(e)}")
            return []
    
    def _generate_summary(self, text: str, title: str) -> str:
        """Generate a comprehensive summary of the document"""
        prompt = f"""
        Provide a comprehensive summary of this policy document titled "{title}".
        Include the main purpose, key changes or updates, who it affects, and important implementation details.
        Keep the summary between 150-300 words and focus on practical implications.
        
        Document text:
        """
        
        try:
            summary = self.llm_analyzer.generate_response(prompt, text)
            if summary and summary.strip() and "LLM analysis unavailable" not in summary:
                return summary.strip()
            else:
                # Fallback to basic analysis
                return self._create_basic_summary(text, title)
        except Exception as e:
            self.logger.error(f"Error generating summary: {str(e)}")
            return self._create_basic_summary(text, title)
    
    def _create_basic_summary(self, text: str, title: str) -> str:
        """Create a basic summary when LLM is unavailable"""
        words = text.split()
        word_count = len(words)
        
        # Extract first few sentences for basic summary
        sentences = text.split('.')[:3]
        preview = '. '.join(sentences).strip()
        if len(preview) > 300:
            preview = preview[:300] + "..."
        
        return f"Document: {title}\n\nPreview: {preview}\n\nDocument contains {word_count} words. Full AI analysis will be available when LLM service is connected."
    
    def _parse_json_response(self, response: str, fallback: Any) -> Any:
        """Parse JSON response from LLM, with fallback"""
        try:
            # Try to find JSON in the response
            start_idx = response.find('[')
            end_idx = response.rfind(']')
            
            if start_idx != -1 and end_idx != -1:
                json_str = response[start_idx:end_idx + 1]
                return json.loads(json_str)
            else:
                # Try parsing the entire response
                return json.loads(response)
        except (json.JSONDecodeError, ValueError):
            self.logger.warning("Failed to parse JSON response from LLM")
            return fallback
    
    def _create_fallback_structure(self, text: str, title: str) -> Dict[str, Any]:
        """Create a basic structure when LLM parsing fails"""
        return {
            'title': title,
            'summary': f"Document analysis of {title}. Contains {len(text.split())} words.",
            'definitions': [],
            'requirements': [],
            'actions': [],
            'deadlines': [],
            'word_count': len(text.split()),
            'section_count': 1
        }
    
    def compare_structured_documents(self, doc1_structure: Dict, doc2_structure: Dict) -> Dict[str, Any]:
        """Compare two structured documents"""
        try:
            comparison = {
                'summary_comparison': self._compare_summaries(
                    doc1_structure.get('summary', ''),
                    doc2_structure.get('summary', ''),
                    doc1_structure.get('title', 'Document 1'),
                    doc2_structure.get('title', 'Document 2')
                ),
                'definitions_comparison': self._compare_definitions(
                    doc1_structure.get('definitions', []),
                    doc2_structure.get('definitions', [])
                ),
                'requirements_comparison': self._compare_requirements(
                    doc1_structure.get('requirements', []),
                    doc2_structure.get('requirements', [])
                ),
                'actions_comparison': self._compare_actions(
                    doc1_structure.get('actions', []),
                    doc2_structure.get('actions', [])
                ),
                'deadlines_comparison': self._compare_deadlines(
                    doc1_structure.get('deadlines', []),
                    doc2_structure.get('deadlines', [])
                ),
                'metadata': {
                    'doc1_word_count': doc1_structure.get('word_count', 0),
                    'doc2_word_count': doc2_structure.get('word_count', 0),
                    'doc1_section_count': doc1_structure.get('section_count', 0),
                    'doc2_section_count': doc2_structure.get('section_count', 0)
                }
            }
            
            return comparison
            
        except Exception as e:
            self.logger.error(f"Error comparing structured documents: {str(e)}")
            return {'error': str(e)}
    
    def _compare_summaries(self, summary1: str, summary2: str, title1: str, title2: str) -> Dict[str, str]:
        """Compare document summaries"""
        prompt = f"""
        Compare these two policy document summaries and identify key differences:
        
        {title1} Summary:
        {summary1}
        
        {title2} Summary:
        {summary2}
        
        Provide a comparison focusing on:
        1. Major policy changes
        2. Scope differences
        3. Implementation changes
        4. Impact on stakeholders
        
        Keep the comparison concise but comprehensive.
        """
        
        try:
            comparison = self.llm_analyzer.generate_response(prompt, "")
            return {
                'comparison_text': comparison,
                'doc1_length': len(summary1.split()),
                'doc2_length': len(summary2.split())
            }
        except Exception as e:
            return {'comparison_text': f"Error comparing summaries: {str(e)}", 'doc1_length': 0, 'doc2_length': 0}
    
    def _compare_definitions(self, definitions1: List, definitions2: List) -> Dict[str, Any]:
        """Compare definitions between documents"""
        # Find matching, added, and removed definitions
        terms1 = {d.get('term', '').lower(): d for d in definitions1}
        terms2 = {d.get('term', '').lower(): d for d in definitions2}
        
        matched = []
        added = []
        removed = []
        
        # Find matches and changes
        for term, defn1 in terms1.items():
            if term in terms2:
                defn2 = terms2[term]
                matched.append({
                    'term': defn1.get('term', ''),
                    'old_definition': defn1.get('definition', ''),
                    'new_definition': defn2.get('definition', ''),
                    'changed': defn1.get('definition', '') != defn2.get('definition', '')
                })
            else:
                removed.append(defn1)
        
        # Find new definitions
        for term, defn2 in terms2.items():
            if term not in terms1:
                added.append(defn2)
        
        return {
            'matched_definitions': matched,
            'added_definitions': added,
            'removed_definitions': removed,
            'total_doc1': len(definitions1),
            'total_doc2': len(definitions2)
        }
    
    def _compare_requirements(self, requirements1: List, requirements2: List) -> Dict[str, Any]:
        """Compare requirements between documents"""
        return {
            'doc1_requirements': requirements1,
            'doc2_requirements': requirements2,
            'total_doc1': len(requirements1),
            'total_doc2': len(requirements2),
            'change_summary': f"Requirements changed from {len(requirements1)} to {len(requirements2)} items"
        }
    
    def _compare_actions(self, actions1: List, actions2: List) -> Dict[str, Any]:
        """Compare actions between documents"""
        return {
            'doc1_actions': actions1,
            'doc2_actions': actions2,
            'total_doc1': len(actions1),
            'total_doc2': len(actions2),
            'change_summary': f"Actions changed from {len(actions1)} to {len(actions2)} items"
        }
    
    def _compare_deadlines(self, deadlines1: List, deadlines2: List) -> Dict[str, Any]:
        """Compare deadlines between documents"""
        return {
            'doc1_deadlines': deadlines1,
            'doc2_deadlines': deadlines2,
            'total_doc1': len(deadlines1),
            'total_doc2': len(deadlines2),
            'change_summary': f"Deadlines changed from {len(deadlines1)} to {len(deadlines2)} items"
        }