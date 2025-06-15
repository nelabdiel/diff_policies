import logging
import difflib
from typing import Dict, List, Any
try:
    from llm_analyzer import LLMAnalyzer
except ImportError:
    from simple_analyzer import SimpleLLMAnalyzer as LLMAnalyzer

class DiffGenerator:
    """Generates detailed comparison results between documents"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.llm_analyzer = LLMAnalyzer()
    
    def generate_comparison(self, text1: str, text2: str, matches: List[Dict], 
                          sections1: List[Dict], sections2: List[Dict]) -> Dict[str, Any]:
        """
        Generate comprehensive comparison results
        
        Args:
            text1: Full text of first document
            text2: Full text of second document
            matches: Section matches from semantic matcher
            sections1: Sections from first document
            sections2: Sections from second document
            
        Returns:
            Comprehensive comparison result
        """
        try:
            comparison_result = {
                'sections': [],
                'statistics': {},
                'overall_changes': [],
                'metadata': {
                    'total_sections_doc1': len(sections1),
                    'total_sections_doc2': len(sections2),
                    'total_matches': len(matches)
                }
            }
            
            # Process each match
            for match in matches:
                section_result = self._process_section_match(match)
                comparison_result['sections'].append(section_result)
            
            # Generate statistics
            comparison_result['statistics'] = self._calculate_statistics(comparison_result['sections'])
            
            # Identify major changes
            comparison_result['overall_changes'] = self._identify_major_changes(comparison_result['sections'])
            
            self.logger.info("Generated comprehensive comparison result")
            return comparison_result
            
        except Exception as e:
            self.logger.error(f"Error generating comparison: {str(e)}")
            return {
                'sections': [],
                'statistics': {'error': str(e)},
                'overall_changes': [],
                'metadata': {'error': str(e)}
            }
    
    def _process_section_match(self, match: Dict) -> Dict[str, Any]:
        """Process a single section match"""
        try:
            section1 = match.get('section1')
            section2 = match.get('section2')
            match_type = match.get('match_type', 'unknown')
            similarity = match.get('similarity', 0.0)
            
            result = {
                'match_type': match_type,
                'similarity': similarity,
                'title1': section1['title'] if section1 else None,
                'title2': section2['title'] if section2 else None,
                'content1': section1['content'] if section1 else None,
                'content2': section2['content'] if section2 else None,
                'change_type': match_type,
                'diff_html': '',
                'summary': '',
                'impact_analysis': {}
            }
            
            # Generate detailed analysis based on match type
            if match_type == 'matched' and section1 and section2:
                result.update(self._analyze_matched_sections(section1, section2))
            elif match_type == 'added' and section2:
                result.update(self._analyze_added_section(section2))
            elif match_type == 'removed' and section1:
                result.update(self._analyze_removed_section(section1))
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing section match: {str(e)}")
            return {
                'match_type': 'error',
                'error': str(e),
                'change_type': 'error'
            }
    
    def _analyze_matched_sections(self, section1: Dict, section2: Dict) -> Dict[str, Any]:
        """Analyze matched sections for differences"""
        content1 = section1['content']
        content2 = section2['content']
        
        # Generate HTML diff
        diff_html = self._generate_html_diff(content1, content2)
        
        # Determine if there are significant changes
        if content1.strip() == content2.strip():
            change_type = 'unchanged'
            summary = "No changes detected in this section."
        else:
            change_type = 'modified'
            # Get LLM analysis of changes
            summary = self.llm_analyzer.analyze_section_change(content1, content2)
        
        # Get impact analysis for modified sections
        impact_analysis = {}
        if change_type == 'modified':
            impact_analysis = self.llm_analyzer.classify_change_impact(content1, content2)
        
        return {
            'change_type': change_type,
            'diff_html': diff_html,
            'summary': summary,
            'impact_analysis': impact_analysis
        }
    
    def _analyze_added_section(self, section: Dict) -> Dict[str, Any]:
        """Analyze a newly added section"""
        summary = self.llm_analyzer.generate_section_summary(section['content'], 'added')
        
        return {
            'change_type': 'added',
            'diff_html': f'<div class="diff-added">{self._escape_html(section["content"])}</div>',
            'summary': summary,
            'impact_analysis': {
                'impact_level': 'medium',
                'change_category': 'addition',
                'stakeholder_impact': 'New requirements or provisions added'
            }
        }
    
    def _analyze_removed_section(self, section: Dict) -> Dict[str, Any]:
        """Analyze a removed section"""
        summary = self.llm_analyzer.generate_section_summary(section['content'], 'removed')
        
        return {
            'change_type': 'removed',
            'diff_html': f'<div class="diff-removed">{self._escape_html(section["content"])}</div>',
            'summary': summary,
            'impact_analysis': {
                'impact_level': 'high',
                'change_category': 'removal',
                'stakeholder_impact': 'Previous requirements or provisions removed'
            }
        }
    
    def _generate_html_diff(self, text1: str, text2: str) -> str:
        """Generate HTML diff between two texts"""
        try:
            # Split into words for better granularity
            words1 = text1.split()
            words2 = text2.split()
            
            # Generate diff
            diff = difflib.unified_diff(words1, words2, lineterm='', n=3)
            
            html_parts = []
            for line in diff:
                if line.startswith('+++') or line.startswith('---') or line.startswith('@@'):
                    continue
                elif line.startswith('+'):
                    html_parts.append(f'<span class="diff-added">{self._escape_html(line[1:])}</span>')
                elif line.startswith('-'):
                    html_parts.append(f'<span class="diff-removed">{self._escape_html(line[1:])}</span>')
                else:
                    html_parts.append(self._escape_html(line))
            
            return ' '.join(html_parts) if html_parts else self._escape_html(text2)
            
        except Exception as e:
            self.logger.error(f"Error generating HTML diff: {str(e)}")
            return f"<div>Diff generation failed: {str(e)}</div>"
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML characters"""
        import html
        return html.escape(text)
    
    def _calculate_statistics(self, sections: List[Dict]) -> Dict[str, Any]:
        """Calculate comparison statistics"""
        stats = {
            'total_sections': len(sections),
            'unchanged': 0,
            'modified': 0,
            'added': 0,
            'removed': 0,
            'high_impact_changes': 0,
            'medium_impact_changes': 0,
            'low_impact_changes': 0
        }
        
        for section in sections:
            change_type = section.get('change_type', 'unknown')
            if change_type in stats:
                stats[change_type] += 1
            
            # Count impact levels
            impact_level = section.get('impact_analysis', {}).get('impact_level', 'unknown')
            impact_key = f"{impact_level}_impact_changes"
            if impact_key in stats:
                stats[impact_key] += 1
        
        # Calculate percentages
        total = stats['total_sections']
        if total > 0:
            stats['percent_changed'] = round(((total - stats['unchanged']) / total) * 100, 1)
            stats['percent_unchanged'] = round((stats['unchanged'] / total) * 100, 1)
        else:
            stats['percent_changed'] = 0
            stats['percent_unchanged'] = 0
        
        return stats
    
    def _identify_major_changes(self, sections: List[Dict]) -> List[Dict]:
        """Identify the most significant changes"""
        major_changes = []
        
        for section in sections:
            change_type = section.get('change_type')
            impact_level = section.get('impact_analysis', {}).get('impact_level', 'low')
            
            # Include high-impact changes and all additions/removals
            if (impact_level == 'high' or 
                change_type in ['added', 'removed'] or
                (change_type == 'modified' and impact_level == 'medium')):
                
                major_changes.append({
                    'title': section.get('title1') or section.get('title2', 'Unnamed Section'),
                    'change_type': change_type,
                    'impact_level': impact_level,
                    'summary': section.get('summary', ''),
                    'category': section.get('impact_analysis', {}).get('change_category', 'unknown')
                })
        
        # Sort by impact level (high first) and limit to top 10
        priority_order = {'high': 3, 'medium': 2, 'low': 1, 'unknown': 0}
        major_changes.sort(key=lambda x: priority_order.get(x['impact_level'], 0), reverse=True)
        
        return major_changes[:10]
