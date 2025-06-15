import logging
import re
from typing import List, Dict, Tuple

# Try to import advanced libraries, fall back to basic implementations
try:
    import numpy as np
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    ADVANCED_MATCHING = True
except ImportError:
    ADVANCED_MATCHING = False

class SemanticMatcher:
    """Handles semantic matching of document sections using embeddings"""
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        self.logger = logging.getLogger(__name__)
        self.model = None
        
        if ADVANCED_MATCHING:
            try:
                self.model = SentenceTransformer(model_name)
                self.logger.info(f"Loaded semantic model: {model_name}")
            except Exception as e:
                self.logger.error(f"Failed to load semantic model: {str(e)}")
                self.model = None
        else:
            self.logger.info("Using fallback text-based matching (advanced libraries not available)")
    
    def extract_sections(self, text: str) -> List[Dict]:
        """
        Extract sections from document text using various heuristics
        
        Args:
            text: Document text
            
        Returns:
            List of section dictionaries
        """
        sections = []
        
        # Split by common section indicators
        section_patterns = [
            r'\n(?=\d+\.\s+[A-Z])',  # Numbered sections
            r'\n(?=[A-Z][A-Z\s]{3,})',  # All caps headers
            r'\n(?=SECTION\s+\d+)',  # Section headers
            r'\n(?=[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*:)',  # Title case with colon
        ]
        
        # Try each pattern and use the one that creates the most reasonable sections
        best_sections = []
        best_score = 0
        
        for pattern in section_patterns:
            try:
                parts = re.split(pattern, text)
                if len(parts) > 1:
                    temp_sections = []
                    for i, part in enumerate(parts):
                        if part.strip():
                            lines = part.strip().split('\n')
                            title = lines[0].strip() if lines else f"Section {i+1}"
                            content = '\n'.join(lines[1:]).strip() if len(lines) > 1 else part.strip()
                            
                            temp_sections.append({
                                'title': title,
                                'content': content,
                                'section_id': i
                            })
                    
                    # Score based on reasonable section lengths and titles
                    score = self._score_sections(temp_sections)
                    if score > best_score:
                        best_score = score
                        best_sections = temp_sections
                        
            except Exception as e:
                self.logger.debug(f"Pattern failed: {pattern}, error: {str(e)}")
                continue
        
        # If no good sections found, split by paragraphs
        if not best_sections:
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
            for i, paragraph in enumerate(paragraphs[:20]):  # Limit to 20 paragraphs
                if len(paragraph) > 50:  # Only meaningful paragraphs
                    first_line = paragraph.split('\n')[0][:100]
                    sections.append({
                        'title': first_line + ('...' if len(first_line) == 100 else ''),
                        'content': paragraph,
                        'section_id': i
                    })
        else:
            sections = best_sections
        
        # Ensure we have at least one section
        if not sections:
            sections = [{
                'title': 'Full Document',
                'content': text,
                'section_id': 0
            }]
        
        self.logger.info(f"Extracted {len(sections)} sections")
        return sections
    
    def _score_sections(self, sections: List[Dict]) -> float:
        """Score section quality based on various criteria"""
        if not sections:
            return 0
        
        score = 0
        total_length = sum(len(s['content']) for s in sections)
        
        for section in sections:
            # Prefer sections with reasonable length
            content_len = len(section['content'])
            if 100 < content_len < 5000:
                score += 2
            elif 50 < content_len < 10000:
                score += 1
            
            # Prefer sections with meaningful titles
            title = section['title'].lower()
            if any(keyword in title for keyword in ['section', 'article', 'chapter', 'part']):
                score += 1
            
            # Penalize very short or very long sections
            if content_len < 20 or content_len > 10000:
                score -= 1
        
        # Prefer reasonable number of sections
        num_sections = len(sections)
        if 3 <= num_sections <= 15:
            score += 2
        elif 2 <= num_sections <= 25:
            score += 1
        
        return score / max(1, num_sections)
    
    def match_sections(self, sections1: List[Dict], sections2: List[Dict]) -> List[Dict]:
        """
        Match sections between two documents using semantic similarity
        
        Args:
            sections1: Sections from first document
            sections2: Sections from second document
            
        Returns:
            List of matches with similarity scores
        """
        if not self.model:
            # Fallback to simple text matching
            return self._fallback_matching(sections1, sections2)
        
        try:
            # Generate embeddings for all sections
            texts1 = [f"{s['title']} {s['content']}" for s in sections1]
            texts2 = [f"{s['title']} {s['content']}" for s in sections2]
            
            embeddings1 = self.model.encode(texts1)
            embeddings2 = self.model.encode(texts2)
            
            # Calculate similarity matrix
            similarity_matrix = cosine_similarity(embeddings1, embeddings2)
            
            matches = []
            used_indices2 = set()
            
            # Find best matches for each section in doc1
            for i, section1 in enumerate(sections1):
                best_match_idx = -1
                best_similarity = 0.3  # Minimum threshold
                
                for j, section2 in enumerate(sections2):
                    if j not in used_indices2 and similarity_matrix[i][j] > best_similarity:
                        best_similarity = similarity_matrix[i][j]
                        best_match_idx = j
                
                if best_match_idx != -1:
                    used_indices2.add(best_match_idx)
                    matches.append({
                        'section1': section1,
                        'section2': sections2[best_match_idx],
                        'similarity': float(best_similarity),
                        'match_type': 'matched'
                    })
                else:
                    matches.append({
                        'section1': section1,
                        'section2': None,
                        'similarity': 0.0,
                        'match_type': 'removed'
                    })
            
            # Add unmatched sections from doc2 as new sections
            for j, section2 in enumerate(sections2):
                if j not in used_indices2:
                    matches.append({
                        'section1': None,
                        'section2': section2,
                        'similarity': 0.0,
                        'match_type': 'added'
                    })
            
            self.logger.info(f"Generated {len(matches)} section matches")
            return matches
            
        except Exception as e:
            self.logger.error(f"Error in semantic matching: {str(e)}")
            return self._fallback_matching(sections1, sections2)
    
    def _fallback_matching(self, sections1: List[Dict], sections2: List[Dict]) -> List[Dict]:
        """Simple fallback matching based on title similarity"""
        matches = []
        used_indices2 = set()
        
        for section1 in sections1:
            best_match_idx = -1
            best_score = 0
            
            for j, section2 in enumerate(sections2):
                if j not in used_indices2:
                    # Simple title similarity
                    title1_words = set(section1['title'].lower().split())
                    title2_words = set(section2['title'].lower().split())
                    
                    if title1_words and title2_words:
                        similarity = len(title1_words & title2_words) / len(title1_words | title2_words)
                        if similarity > best_score and similarity > 0.3:
                            best_score = similarity
                            best_match_idx = j
            
            if best_match_idx != -1:
                used_indices2.add(best_match_idx)
                matches.append({
                    'section1': section1,
                    'section2': sections2[best_match_idx],
                    'similarity': best_score,
                    'match_type': 'matched'
                })
            else:
                matches.append({
                    'section1': section1,
                    'section2': None,
                    'similarity': 0.0,
                    'match_type': 'removed'
                })
        
        # Add unmatched sections from doc2
        for j, section2 in enumerate(sections2):
            if j not in used_indices2:
                matches.append({
                    'section1': None,
                    'section2': section2,
                    'similarity': 0.0,
                    'match_type': 'added'
                })
        
        return matches
