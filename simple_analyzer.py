import logging
import difflib
from typing import Dict, List, Any

class SimpleLLMAnalyzer:
    """Simplified analyzer that works without external LLM dependencies"""
    
    def __init__(self, model_name: str = 'llama3.2'):
        self.model_name = model_name
        self.logger = logging.getLogger(__name__)
        self.logger.info("Using simplified analysis (external LLM not available)")
    
    def generate_response(self, query: str, context: str) -> str:
        """Generate a basic response without LLM"""
        return f"Analysis of context: {context[:200]}..."
    
    def analyze_section_change(self, old_text: str, new_text: str) -> str:
        """Analyze changes between two text sections using basic diff"""
        if old_text.strip() == new_text.strip():
            return "No changes detected in this section."
        
        # Basic change analysis using difflib
        diff = list(difflib.unified_diff(
            old_text.splitlines(keepends=True),
            new_text.splitlines(keepends=True),
            lineterm='',
            n=3
        ))
        
        added_lines = len([line for line in diff if line.startswith('+')])
        removed_lines = len([line for line in diff if line.startswith('-')])
        
        if added_lines > removed_lines:
            change_type = "Content added"
        elif removed_lines > added_lines:
            change_type = "Content removed"
        else:
            change_type = "Content modified"
        
        return f"{change_type}. Approximately {added_lines} lines added, {removed_lines} lines removed."
    
    def generate_section_summary(self, section_text: str, change_type: str) -> str:
        """Generate a basic summary for a section"""
        word_count = len(section_text.split())
        first_line = section_text.split('\n')[0][:100]
        
        if change_type == 'added':
            return f"New section added with {word_count} words. Starts with: {first_line}..."
        elif change_type == 'removed':
            return f"Section removed ({word_count} words). Previously started with: {first_line}..."
        else:
            return f"Section content ({word_count} words). Starts with: {first_line}..."
    
    def generate_overall_summary(self, comparison_result: Dict, doc1_title: str, doc2_title: str) -> str:
        """Generate an overall summary of document changes"""
        stats = comparison_result.get('statistics', {})
        total = stats.get('total_sections', 0)
        added = stats.get('added', 0)
        removed = stats.get('removed', 0)
        modified = stats.get('modified', 0)
        unchanged = stats.get('unchanged', 0)
        
        summary = f"Comparison between {doc1_title} and {doc2_title}:\n\n"
        summary += f"Total sections analyzed: {total}\n"
        summary += f"• {unchanged} sections unchanged\n"
        summary += f"• {modified} sections modified\n"
        summary += f"• {added} sections added\n"
        summary += f"• {removed} sections removed\n\n"
        
        if modified + added + removed > 0:
            change_percentage = round(((modified + added + removed) / max(1, total)) * 100, 1)
            summary += f"Overall change rate: {change_percentage}%\n\n"
            
            if added > 0:
                summary += f"Notable additions detected in {added} sections. "
            if removed > 0:
                summary += f"Content removed from {removed} sections. "
            if modified > 0:
                summary += f"Modifications found in {modified} sections."
        else:
            summary += "Documents appear to be identical or very similar."
        
        return summary
    
    def classify_change_impact(self, old_text: str, new_text: str) -> Dict[str, str]:
        """Classify the impact level and type of a change"""
        old_words = len(old_text.split())
        new_words = len(new_text.split())
        word_diff = abs(new_words - old_words)
        
        # Simple impact classification based on text length changes
        if word_diff > 100:
            impact_level = 'high'
        elif word_diff > 20:
            impact_level = 'medium'
        else:
            impact_level = 'low'
        
        # Basic categorization
        if 'requirement' in old_text.lower() or 'requirement' in new_text.lower():
            change_category = 'requirements'
        elif 'definition' in old_text.lower() or 'definition' in new_text.lower():
            change_category = 'definitions'
        elif 'procedure' in old_text.lower() or 'procedure' in new_text.lower():
            change_category = 'procedural'
        else:
            change_category = 'other'
        
        return {
            'impact_level': impact_level,
            'change_category': change_category,
            'stakeholder_impact': f'Text length changed by {word_diff} words, categorized as {change_category}'
        }