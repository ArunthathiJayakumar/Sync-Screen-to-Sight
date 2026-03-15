"""
AI Exam Preparation Module
Handles content processing, flashcard generation, quiz creation, and resource recommendations.
"""

import re
import random
import os
from typing import List, Dict, Tuple, Optional
from collections import Counter
import numpy as np

# Try to import optional dependencies
try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


class ContentProcessor:
    """Process and extract content from various document formats."""
    
    @staticmethod
    def extract_text_from_document(file_path: str) -> str:
        """Extract text from PDF, DOCX, or TXT files."""
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.txt':
            return ContentProcessor._extract_from_txt(file_path)
        elif ext == '.docx' and DOCX_AVAILABLE:
            return ContentProcessor._extract_from_docx(file_path)
        elif ext == '.pdf' and PDF_AVAILABLE:
            return ContentProcessor._extract_from_pdf(file_path)
        else:
            # Fallback: try to read as text
            try:
                return ContentProcessor._extract_from_txt(file_path)
            except:
                return ""
    
    @staticmethod
    def _extract_from_txt(file_path: str) -> str:
        """Extract text from TXT file."""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    
    @staticmethod
    def _extract_from_docx(file_path: str) -> str:
        """Extract text from DOCX file."""
        doc = Document(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return '\n'.join(paragraphs)
    
    @staticmethod
    def _extract_from_pdf(file_path: str) -> str:
        """Extract text from PDF file."""
        text = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text.append(page_text)
        return '\n'.join(text)


class TextAnalyzer:
    """Analyze text content for key concepts and summaries."""
    
    # Common stop words to filter out
    STOP_WORDS = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
        'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
        'would', 'could', 'should', 'may', 'might', 'must', 'shall', 'can',
        'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it',
        'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your',
        'his', 'her', 'its', 'our', 'their'
    }
    
    @staticmethod
    def summarize_content(text: str, num_sentences: int = 3) -> str:
        """Generate a simple extractive summary of the text."""
        sentences = TextAnalyzer._split_sentences(text)
        if len(sentences) <= num_sentences:
            return text
        
        # Score sentences based on word frequency
        word_freq = TextAnalyzer._calculate_word_frequency(text)
        sentence_scores = []
        
        for sentence in sentences:
            score = sum(word_freq.get(word.lower(), 0) for word in sentence.split())
            sentence_scores.append((score, sentence))
        
        # Get top sentences
        sentence_scores.sort(reverse=True)
        top_sentences = [s[1] for s in sentence_scores[:num_sentences]]
        
        # Maintain original order
        top_sentences.sort(key=lambda s: sentences.index(s))
        
        return ' '.join(top_sentences)
    
    @staticmethod
    def extract_key_concepts(text: str, num_concepts: int = 10) -> List[str]:
        """Extract key concepts/topics from text."""
        # Clean and tokenize
        words = re.findall(r'\b[A-Za-z][a-zA-Z]*\b', text.lower())
        
        # Filter stop words and short words
        filtered_words = [
            w for w in words 
            if w not in TextAnalyzer.STOP_WORDS and len(w) > 3
        ]
        
        # Count frequency
        word_counts = Counter(filtered_words)
        
        # Get most common words as concepts
        concepts = [word for word, count in word_counts.most_common(num_concepts)]
        
        return concepts
    
    @staticmethod
    def extract_important_sentences(text: str, num_sentences: int = 15) -> List[str]:
        """Extract important sentences for flashcard/quiz generation."""
        sentences = TextAnalyzer._split_sentences(text)
        
        if len(sentences) <= num_sentences:
            return sentences
        
        # Score sentences
        word_freq = TextAnalyzer._calculate_word_frequency(text)
        scored_sentences = []
        
        for sentence in sentences:
            words = sentence.split()
            if len(words) > 5:  # Filter very short sentences
                score = sum(word_freq.get(word.lower(), 0) for word in words)
                scored_sentences.append((score, sentence))
        
        # Sort by score and return top sentences
        scored_sentences.sort(reverse=True)
        return [s[1] for s in scored_sentences[:num_sentences]]
    
    @staticmethod
    def _split_sentences(text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    @staticmethod
    def _calculate_word_frequency(text: str) -> Dict[str, int]:
        """Calculate word frequency in text."""
        words = re.findall(r'\b[a-z]+\b', text.lower())
        filtered_words = [w for w in words if w not in TextAnalyzer.STOP_WORDS]
        return Counter(filtered_words)


class FlashcardGenerator:
    """Generate flashcards from text content."""
    
    @staticmethod
    def generate_flashcards(text: str, num_cards: int = 10) -> List[Dict[str, str]]:
        """Generate flashcards from text content."""
        sentences = TextAnalyzer.extract_important_sentences(text, num_cards * 2)
        flashcards = []
        
        for sentence in sentences:
            if len(flashcards) >= num_cards:
                break
            
            card = FlashcardGenerator._create_card_from_sentence(sentence)
            if card:
                flashcards.append(card)
        
        return flashcards
    
    @staticmethod
    def _create_card_from_sentence(sentence: str) -> Optional[Dict[str, str]]:
        """Create a flashcard from a single sentence."""
        sentence = sentence.strip()
        
        # Skip very short or very long sentences
        words = sentence.split()
        if len(words) < 5 or len(words) > 50:
            return None
        
        # Try to create definition-style cards
        definition_patterns = [
            r'(.+?)\s+(?:is|are|was|were)\s+(?:defined as|a|an|the)\s+(.+)',
            r'(.+?)\s+refers to\s+(.+)',
            r'(.+?)\s+means\s+(.+)',
        ]
        
        for pattern in definition_patterns:
            match = re.search(pattern, sentence, re.IGNORECASE)
            if match:
                return {
                    'question': f"What is {match.group(1).strip()}?",
                    'answer': match.group(2).strip(),
                    'context': sentence
                }
        
        # Create question from sentence
        # Look for key phrases
        key_phrases = re.findall(r'\b[A-Z][a-zA-Z]*(?:\s+[A-Z][a-zA-Z]*)*\b', sentence)
        
        if key_phrases:
            # Use the first key phrase as the subject
            subject = key_phrases[0]
            question = f"What do you know about {subject}?"
            return {
                'question': question,
                'answer': sentence,
                'context': sentence
            }
        
        # Generic question
        return {
            'question': f"Explain: {' '.join(words[:5])}...",
            'answer': sentence,
            'context': sentence
        }


class QuizGenerator:
    """Generate quiz questions from text content."""
    
    QUESTION_TYPES = ['mcq', 'true_false', 'fill_blank']
    
    @staticmethod
    def generate_quiz_questions(text: str, num_questions: int = 5) -> List[Dict]:
        """Generate a mix of quiz questions from text."""
        sentences = TextAnalyzer.extract_important_sentences(text, num_questions * 3)
        questions = []
        
        for i, sentence in enumerate(sentences):
            if len(questions) >= num_questions:
                break
            
            q_type = QuizGenerator.QUESTION_TYPES[i % len(QuizGenerator.QUESTION_TYPES)]
            question = QuizGenerator._create_question(sentence, q_type, text)
            
            if question:
                questions.append(question)
        
        return questions
    
    @staticmethod
    def _create_question(sentence: str, q_type: str, full_text: str) -> Optional[Dict]:
        """Create a question based on type."""
        if q_type == 'mcq':
            return QuizGenerator._create_mcq(sentence, full_text)
        elif q_type == 'true_false':
            return QuizGenerator._create_true_false(sentence)
        elif q_type == 'fill_blank':
            return QuizGenerator._create_fill_blank(sentence)
        return None
    
    @staticmethod
    def _create_mcq(sentence: str, full_text: str) -> Optional[Dict]:
        """Create a multiple choice question."""
        # Extract key concept
        words = sentence.split()
        if len(words) < 5:
            return None
        
        # Find a key term to ask about
        key_terms = re.findall(r'\b[A-Z][a-zA-Z]{3,}\b', sentence)
        
        if not key_terms:
            key_terms = [w for w in words if len(w) > 5 and w.lower() not in TextAnalyzer.STOP_WORDS]
        
        if not key_terms:
            return None
        
        key_term = random.choice(key_terms[:3])
        
        # Create question
        question_text = sentence.replace(key_term, '_______')
        
        # Generate distractors
        all_words = re.findall(r'\b[A-Za-z]{4,}\b', full_text)
        distractors = [w for w in all_words if w.lower() != key_term.lower() and len(w) > 4]
        distractors = list(set(distractors))[:3]
        
        # Ensure we have enough distractors
        while len(distractors) < 3:
            distractors.append(f"Option {len(distractors) + 1}")
        
        options = [key_term] + distractors[:3]
        random.shuffle(options)
        
        return {
            'type': 'mcq',
            'question': f"Fill in the blank: {question_text}",
            'options': options,
            'correct_answer': key_term,
            'explanation': sentence
        }
    
    @staticmethod
    def _create_true_false(sentence: str) -> Optional[Dict]:
        """Create a true/false question."""
        # Use the sentence as a true statement
        # Occasionally negate it for false
        is_true = random.choice([True, False])
        
        if is_true:
            statement = sentence
            answer = True
        else:
            # Create a false statement by modifying the sentence
            statement = QuizGenerator._negate_statement(sentence)
            answer = False
        
        return {
            'type': 'true_false',
            'question': f"True or False: {statement}",
            'correct_answer': answer,
            'explanation': f"The correct statement is: {sentence}"
        }
    
    @staticmethod
    def _create_fill_blank(sentence: str) -> Optional[Dict]:
        """Create a fill-in-the-blank question."""
        words = sentence.split()
        if len(words) < 5:
            return None
        
        # Choose a significant word to blank out
        content_words = [w for w in words if len(w) > 4 and w.lower() not in TextAnalyzer.STOP_WORDS]
        
        if not content_words:
            content_words = words
        
        blank_word = random.choice(content_words)
        question = sentence.replace(blank_word, '________', 1)
        
        return {
            'type': 'fill_blank',
            'question': f"Fill in the blank: {question}",
            'correct_answer': blank_word,
            'explanation': sentence
        }
    
    @staticmethod
    def _negate_statement(sentence: str) -> str:
        """Create a negated version of a statement for false questions."""
        # Simple negation strategies
        negations = [
            (r'\bis\b', 'is not'),
            (r'\bare\b', 'are not'),
            (r'\bwas\b', 'was not'),
            (r'\bwere\b', 'were not'),
            (r'\bcan\b', 'cannot'),
            (r'\bwill\b', 'will not'),
            (r'\ball\b', 'no'),
            (r'\balways\b', 'never'),
        ]
        
        for pattern, replacement in negations:
            if re.search(pattern, sentence, re.IGNORECASE):
                return re.sub(pattern, replacement, sentence, count=1, flags=re.IGNORECASE)
        
        # If no pattern matches, prepend with "Not"
        return f"Not {sentence[0].lower()}{sentence[1:]}"


class ResourceRecommender:
    """Recommend learning resources based on topics."""
    
    RESOURCE_DATABASE = {
        'programming': [
            {'title': 'Python Documentation', 'url': 'https://docs.python.org/3/', 'type': 'documentation'},
            {'title': 'W3Schools Python Tutorial', 'url': 'https://www.w3schools.com/python/', 'type': 'tutorial'},
            {'title': 'Codecademy Python Course', 'url': 'https://www.codecademy.com/learn/learn-python-3', 'type': 'course'},
        ],
        'python': [
            {'title': 'Real Python Tutorials', 'url': 'https://realpython.com/', 'type': 'tutorial'},
            {'title': 'Python for Beginners - YouTube', 'url': 'https://www.youtube.com/watch?v=rfscVS0vtbw', 'type': 'video'},
        ],
        'machine learning': [
            {'title': 'Machine Learning by Andrew Ng - Coursera', 'url': 'https://www.coursera.org/learn/machine-learning', 'type': 'course'},
            {'title': 'TensorFlow Documentation', 'url': 'https://www.tensorflow.org/learn', 'type': 'documentation'},
            {'title': 'Kaggle Learn', 'url': 'https://www.kaggle.com/learn', 'type': 'tutorial'},
        ],
        'data science': [
            {'title': 'Data Science Handbook', 'url': 'https://jakevdp.github.io/PythonDataScienceHandbook/', 'type': 'book'},
            {'title': 'Khan Academy Statistics', 'url': 'https://www.khanacademy.org/math/statistics-probability', 'type': 'course'},
        ],
        'web development': [
            {'title': 'MDN Web Docs', 'url': 'https://developer.mozilla.org/', 'type': 'documentation'},
            {'title': 'freeCodeCamp', 'url': 'https://www.freecodecamp.org/', 'type': 'course'},
        ],
        'database': [
            {'title': 'SQLZoo', 'url': 'https://sqlzoo.net/', 'type': 'tutorial'},
            {'title': 'PostgreSQL Documentation', 'url': 'https://www.postgresql.org/docs/', 'type': 'documentation'},
        ],
        'mathematics': [
            {'title': 'Khan Academy Math', 'url': 'https://www.khanacademy.org/math', 'type': 'course'},
            {'title': '3Blue1Brown YouTube', 'url': 'https://www.youtube.com/c/3blue1brown', 'type': 'video'},
        ],
        'science': [
            {'title': 'Khan Academy Science', 'url': 'https://www.khanacademy.org/science', 'type': 'course'},
            {'title': 'CrashCourse YouTube', 'url': 'https://www.youtube.com/c/crashcourse', 'type': 'video'},
        ],
        'history': [
            {'title': 'CrashCourse History', 'url': 'https://www.youtube.com/playlist?list=PLBDA2E52FB1EF80C9', 'type': 'video'},
            {'title': 'History.com', 'url': 'https://www.history.com/', 'type': 'article'},
        ],
        'english': [
            {'title': 'Grammarly Blog', 'url': 'https://www.grammarly.com/blog/', 'type': 'article'},
            {'title': 'Purdue OWL', 'url': 'https://owl.purdue.edu/', 'type': 'documentation'},
        ],
    }
    
    @staticmethod
    def recommend_resources(topics: List[str]) -> List[Dict]:
        """Recommend resources based on topics."""
        recommendations = []
        
        for topic in topics:
            topic_lower = topic.lower()
            
            # Direct match
            if topic_lower in ResourceRecommender.RESOURCE_DATABASE:
                recommendations.extend(ResourceRecommender.RESOURCE_DATABASE[topic_lower])
            else:
                # Partial match
                for key, resources in ResourceRecommender.RESOURCE_DATABASE.items():
                    if key in topic_lower or topic_lower in key:
                        recommendations.extend(resources)
        
        # Remove duplicates
        seen = set()
        unique_recommendations = []
        for rec in recommendations:
            if rec['url'] not in seen:
                seen.add(rec['url'])
                unique_recommendations.append(rec)
        
        return unique_recommendations[:10]  # Return top 10
    
    @staticmethod
    def analyze_weak_areas(quiz_attempts: List[Dict]) -> List[str]:
        """Analyze quiz attempts to identify weak areas."""
        if not quiz_attempts:
            return []
        
        # Count incorrect answers by topic
        topic_errors = Counter()
        
        for attempt in quiz_attempts:
            if not attempt.get('is_correct', True):
                # Extract topics from question
                question = attempt.get('question', '')
                words = re.findall(r'\b[A-Za-z]{4,}\b', question.lower())
                for word in words:
                    if word not in TextAnalyzer.STOP_WORDS:
                        topic_errors[word] += 1
        
        # Return topics with most errors
        return [topic for topic, count in topic_errors.most_common(5)]


# Convenience functions for easy import
def extract_text_from_document(file_path: str) -> str:
    """Extract text from a document file."""
    return ContentProcessor.extract_text_from_document(file_path)

def summarize_content(text: str, num_sentences: int = 3) -> str:
    """Generate a summary of the text."""
    return TextAnalyzer.summarize_content(text, num_sentences)

def extract_key_concepts(text: str, num_concepts: int = 10) -> List[str]:
    """Extract key concepts from text."""
    return TextAnalyzer.extract_key_concepts(text, num_concepts)

def generate_flashcards(text: str, num_cards: int = 10) -> List[Dict[str, str]]:
    """Generate flashcards from text."""
    return FlashcardGenerator.generate_flashcards(text, num_cards)

def generate_quiz_questions(text: str, num_questions: int = 5) -> List[Dict]:
    """Generate quiz questions from text."""
    return QuizGenerator.generate_quiz_questions(text, num_questions)

def recommend_resources(topics: List[str]) -> List[Dict]:
    """Recommend learning resources for topics."""
    return ResourceRecommender.recommend_resources(topics)

def analyze_weak_areas(quiz_attempts: List[Dict]) -> List[str]:
    """Analyze weak areas from quiz attempts."""
    return ResourceRecommender.analyze_weak_areas(quiz_attempts)


class StudyPlanner:
    """AI-powered study planner that creates adaptive daily schedules."""
    
    @staticmethod
    def generate_study_schedule(syllabus: str, exam_date, daily_hours: float = 2.0, 
                                 weak_topics: List[str] = None, 
                                 completed_topics: List[str] = None) -> List[Dict]:
        """
        Generate a daily study schedule based on syllabus and exam date.
        
        Args:
            syllabus: Text containing all topics to study
            exam_date: Target exam date
            daily_hours: Hours available per day for studying
            weak_topics: Topics the student struggles with (needs more time)
            completed_topics: Topics already completed
            
        Returns:
            List of daily schedule items
        """
        from datetime import date, timedelta
        
        if weak_topics is None:
            weak_topics = []
        if completed_topics is None:
            completed_topics = []
        
        # Extract topics from syllabus
        topics = StudyPlanner._extract_topics_from_syllabus(syllabus)
        
        # Filter out completed topics
        topics = [t for t in topics if t.lower() not in [c.lower() for c in completed_topics]]
        
        # Calculate days until exam
        today = date.today()
        if isinstance(exam_date, str):
            exam_date = date.fromisoformat(exam_date)
        days_until_exam = (exam_date - today).days
        
        if days_until_exam <= 0:
            days_until_exam = 7  # Default to 1 week if exam date is past
        
        # Prioritize weak topics (allocate 1.5x time)
        topic_weights = {}
        for topic in topics:
            if any(wt.lower() in topic.lower() or topic.lower() in wt.lower() for wt in weak_topics):
                topic_weights[topic] = 1.5  # Weak topics need more time
            else:
                topic_weights[topic] = 1.0
        
        # Calculate total weighted topics
        total_weight = sum(topic_weights.values())
        
        # Calculate minutes per day
        daily_minutes = daily_hours * 60
        
        # Distribute topics across days
        schedule = []
        current_day = today
        topic_index = 0
        topics_list = list(topics)
        
        while topic_index < len(topics_list) and current_day < exam_date:
            day_topics = []
            day_minutes_used = 0
            
            while topic_index < len(topics_list) and day_minutes_used < daily_minutes:
                topic = topics_list[topic_index]
                weight = topic_weights[topic]
                
                # Allocate time based on weight (weak topics get more time)
                minutes_for_topic = int((daily_minutes / total_weight) * weight * (len(topics_list) / days_until_exam))
                minutes_for_topic = max(30, min(minutes_for_topic, 120))  # Between 30-120 minutes
                
                if day_minutes_used + minutes_for_topic <= daily_minutes:
                    day_topics.append({
                        'topic': topic,
                        'description': f"Study {topic} - focus on key concepts and practice questions",
                        'estimated_minutes': minutes_for_topic
                    })
                    day_minutes_used += minutes_for_topic
                    topic_index += 1
                else:
                    break
            
            if day_topics:
                schedule.append({
                    'date': current_day.isoformat(),
                    'items': day_topics,
                    'total_minutes': day_minutes_used
                })
            
            current_day += timedelta(days=1)
        
        # If we have remaining topics, distribute them more aggressively
        remaining_topics = topics_list[topic_index:]
        if remaining_topics and schedule:
            # Add remaining topics to existing days
            for i, topic in enumerate(remaining_topics):
                day_index = i % len(schedule)
                schedule[day_index]['items'].append({
                    'topic': topic,
                    'description': f"Review {topic} - quick revision session",
                    'estimated_minutes': 30
                })
                schedule[day_index]['total_minutes'] += 30
        
        return schedule
    
    @staticmethod
    def _extract_topics_from_syllabus(syllabus: str) -> List[str]:
        """Extract individual topics from syllabus text."""
        # Split by common delimiters
        import re
        
        # Try to find numbered or bulleted lists
        topics = []
        
        # Look for numbered items (1., 2., etc.)
        numbered = re.findall(r'\d+\.\s*([^\n]+)', syllabus)
        if numbered:
            topics.extend([t.strip() for t in numbered])
        
        # Look for bullet points
        bullets = re.findall(r'[\-\*•]\s*([^\n]+)', syllabus)
        if bullets:
            topics.extend([t.strip() for t in bullets])
        
        # If no structured list found, split by lines and clean
        if not topics:
            lines = syllabus.split('\n')
            topics = [line.strip() for line in lines if line.strip() and len(line.strip()) > 3]
        
        # Remove duplicates while preserving order
        seen = set()
        unique_topics = []
        for topic in topics:
            topic_lower = topic.lower()
            if topic_lower not in seen and len(topic) > 3:
                seen.add(topic_lower)
                unique_topics.append(topic)
        
        return unique_topics[:30]  # Limit to 30 topics max
    
    @staticmethod
    def adjust_schedule_for_skipped_topics(schedule: List[Dict], skipped_topics: List[str],
                                           weak_topics: List[str] = None) -> List[Dict]:
        """
        Adjust schedule when student skips topics.
        Skipped topics get rescheduled, weak topics get priority.
        """
        if weak_topics is None:
            weak_topics = []
        
        from datetime import date, timedelta
        
        # Find skipped items and remove them
        skipped_items = []
        for day in schedule:
            for item in day['items'][:]:
                if any(st.lower() in item['topic'].lower() for st in skipped_topics):
                    skipped_items.append(item)
                    day['items'].remove(item)
                    day['total_minutes'] -= item['estimated_minutes']
        
        # Re-add skipped items to future days with more time allocated
        if skipped_items:
            last_date = date.fromisoformat(schedule[-1]['date']) if schedule else date.today()
            
            for item in skipped_items:
                # Check if it's a weak topic
                is_weak = any(wt.lower() in item['topic'].lower() for wt in weak_topics)
                
                # Add extra time for weak/skipped topics
                item['estimated_minutes'] = int(item['estimated_minutes'] * (1.5 if is_weak else 1.2))
                item['description'] += " (Rescheduled - priority review)"
                
                # Add to a new day or existing day with space
                last_date += timedelta(days=1)
                schedule.append({
                    'date': last_date.isoformat(),
                    'items': [item],
                    'total_minutes': item['estimated_minutes']
                })
        
        return schedule
    
    @staticmethod
    def get_study_recommendations(weak_topics: List[str], upcoming_topics: List[str]) -> Dict:
        """Generate study recommendations based on performance."""
        recommendations = {
            'priority_topics': weak_topics[:5] if weak_topics else [],
            'suggested_resources': [],
            'study_tips': []
        }
        
        # Generate study tips based on weak areas
        if weak_topics:
            recommendations['study_tips'].extend([
                "Focus on understanding fundamental concepts before moving to advanced topics",
                "Use active recall - test yourself frequently on weak areas",
                "Space out review sessions for better retention",
                "Create flashcards for key terms and concepts"
            ])
        
        if len(upcoming_topics) > 10:
            recommendations['study_tips'].append(
                "You have many topics remaining - consider increasing daily study time"
            )
        
        return recommendations


class ExamPatternAnalyzer:
    """Analyze previous exam patterns to predict important topics."""
    
    @staticmethod
    def analyze_topic_frequency(questions: List[Dict]) -> Dict[str, Dict]:
        """
        Analyze frequency of topics in previous exam questions.
        Returns topics sorted by importance score.
        """
        topic_stats = {}
        
        for question in questions:
            topic = question.get('topic', '')
            if not topic:
                continue
                
            if topic not in topic_stats:
                topic_stats[topic] = {
                    'count': 0,
                    'years': [],
                    'total_marks': 0,
                    'question_types': [],
                    'difficulty_sum': 0
                }
            
            stats = topic_stats[topic]
            stats['count'] += question.get('frequency_count', 1)
            stats['years'].append(question.get('year', 0))
            stats['total_marks'] += question.get('marks', 5)
            stats['question_types'].append(question.get('question_type', 'unknown'))
            stats['difficulty_sum'] += question.get('difficulty_level', 3)
        
        # Calculate importance score for each topic
        for topic, stats in topic_stats.items():
            # Importance = frequency * recency_weight * marks_weight
            avg_year = sum(stats['years']) / len(stats['years']) if stats['years'] else 2020
            recency_weight = (avg_year - 2015) / 10  # More recent = higher weight
            marks_weight = stats['total_marks'] / 100
            
            stats['importance_score'] = (
                stats['count'] * 0.4 +
                recency_weight * 0.3 +
                marks_weight * 0.3
            )
            stats['avg_difficulty'] = stats['difficulty_sum'] / stats['count'] if stats['count'] > 0 else 3
            stats['question_types'] = list(set(stats['question_types']))
        
        # Sort by importance score
        sorted_topics = dict(sorted(
            topic_stats.items(),
            key=lambda x: x[1]['importance_score'],
            reverse=True
        ))
        
        return sorted_topics
    
    @staticmethod
    def predict_important_topics(questions: List[Dict], top_n: int = 10) -> List[Dict]:
        """Predict which topics are most likely to appear in upcoming exam."""
        topic_stats = ExamPatternAnalyzer.analyze_topic_frequency(questions)
        
        predictions = []
        for topic, stats in list(topic_stats.items())[:top_n]:
            predictions.append({
                'topic': topic,
                'probability': min(stats['importance_score'] * 10, 95),  # Cap at 95%
                'expected_marks': stats['total_marks'],
                'likely_question_types': stats['question_types'][:3],
                'difficulty': 'Hard' if stats['avg_difficulty'] >= 3 else 'Medium' if stats['avg_difficulty'] >= 2 else 'Easy'
            })
        
        return predictions
    
    @staticmethod
    def generate_pattern_report(questions: List[Dict]) -> Dict:
        """Generate comprehensive exam pattern analysis report."""
        if not questions:
            return {'error': 'No previous exam questions available'}
        
        topic_stats = ExamPatternAnalyzer.analyze_topic_frequency(questions)
        
        # Calculate overall statistics
        total_questions = len(questions)
        years_covered = list(set(q.get('year', 0) for q in questions))
        subjects = list(set(q.get('subject', '') for q in questions))
        
        # Question type distribution
        type_dist = {}
        for q in questions:
            qtype = q.get('question_type', 'unknown')
            type_dist[qtype] = type_dist.get(qtype, 0) + 1
        
        # Difficulty distribution
        difficulty_dist = {1: 0, 2: 0, 3: 0, 4: 0}
        for q in questions:
            diff = q.get('difficulty_level', 3)
            difficulty_dist[diff] = difficulty_dist.get(diff, 0) + 1
        
        return {
            'total_questions': total_questions,
            'years_covered': sorted(years_covered, reverse=True),
            'subjects': subjects,
            'top_topics': list(topic_stats.keys())[:15],
            'topic_details': topic_stats,
            'question_type_distribution': type_dist,
            'difficulty_distribution': difficulty_dist,
            'predictions': ExamPatternAnalyzer.predict_important_topics(questions, 10)
        }


class SpacedRepetitionEngine:
    """
    Implementation of SM-2 Spaced Repetition Algorithm.
    Shows topics at optimal intervals before the student forgets them.
    """
    
    @staticmethod
    def calculate_next_review(quality: int, current_interval: int, ease_factor: float) -> Tuple[int, float]:
        """
        Calculate next review interval using SM-2 algorithm.
        
        Args:
            quality: 0-5 rating of how well the topic was recalled
            current_interval: Current interval in days
            ease_factor: Current ease factor (starts at 2.5)
            
        Returns:
            (new_interval_days, new_ease_factor)
        """
        # SM-2 Algorithm
        if quality < 3:
            # If response was difficult, reset to 1 day
            new_interval = 1
        else:
            # Calculate new interval
            if current_interval == 0:
                new_interval = 1
            elif current_interval == 1:
                new_interval = 6
            else:
                new_interval = int(current_interval * ease_factor)
        
        # Update ease factor
        new_ease_factor = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        
        # Keep ease factor within bounds
        new_ease_factor = max(1.3, new_ease_factor)
        
        return new_interval, new_ease_factor
    
    @staticmethod
    def get_due_revisions(revisions: List[Dict], date=None) -> List[Dict]:
        """Get all revisions that are due for review today or earlier."""
        from datetime import date as dt_date
        
        if date is None:
            date = dt_date.today()
        
        due_revisions = []
        for rev in revisions:
            next_review = rev.get('next_review')
            if isinstance(next_review, str):
                next_review = dt_date.fromisoformat(next_review)
            
            if next_review and next_review <= date and not rev.get('is_mastered', False):
                due_revisions.append(rev)
        
        # Sort by urgency (overdue first, then by next_review date)
        due_revisions.sort(key=lambda x: x.get('next_review', date))
        
        return due_revisions
    
    @staticmethod
    def get_revision_schedule(revisions: List[Dict], days_ahead: int = 30) -> Dict:
        """
        Get revision schedule for the next N days.
        Shows when each topic should be reviewed.
        """
        from datetime import date as dt_date, timedelta
        
        schedule = {}
        today = dt_date.today()
        
        for i in range(days_ahead):
            date = today + timedelta(days=i)
            date_str = date.isoformat()
            schedule[date_str] = []
        
        for rev in revisions:
            next_review = rev.get('next_review')
            if isinstance(next_review, str):
                next_review = dt_date.fromisoformat(next_review)
            
            if next_review and not rev.get('is_mastered', False):
                days_diff = (next_review - today).days
                if 0 <= days_diff < days_ahead:
                    date_str = next_review.isoformat()
                    if date_str in schedule:
                        schedule[date_str].append({
                            'topic': rev.get('topic'),
                            'subject': rev.get('subject'),
                            'review_count': rev.get('review_count', 0),
                            'interval_days': rev.get('interval_days', 1)
                        })
        
        return schedule
    
    @staticmethod
    def estimate_mastery_level(revision_sessions: List[Dict]) -> Dict:
        """Estimate mastery level based on revision history."""
        if not revision_sessions:
            return {'level': 'new', 'confidence': 0}
        
        # Calculate average quality
        avg_quality = sum(s.get('quality', 3) for s in revision_sessions) / len(revision_sessions)
        
        # Count consecutive successful reviews (quality >= 4)
        consecutive_success = 0
        for session in reversed(revision_sessions):
            if session.get('quality', 0) >= 4:
                consecutive_success += 1
            else:
                break
        
        # Determine mastery level
        if avg_quality >= 4.5 and consecutive_success >= 3:
            level = 'mastered'
        elif avg_quality >= 3.5 and consecutive_success >= 2:
            level = 'proficient'
        elif avg_quality >= 2.5:
            level = 'learning'
        else:
            level = 'struggling'
        
        return {
            'level': level,
            'confidence': min(avg_quality / 5 * 100, 100),
            'avg_quality': round(avg_quality, 2),
            'total_reviews': len(revision_sessions),
            'consecutive_success': consecutive_success
        }


class DoubtSolverAI:
    """AI-powered doubt solving chatbot with image understanding."""
    
    @staticmethod
    def analyze_question_image(image_path: str) -> Dict:
        """
        Analyze an image containing a question.
        Returns extracted text and detected question type.
        """
        try:
            from PIL import Image
            import pytesseract
            
            # Open image
            img = Image.open(image_path)
            
            # Extract text using OCR
            extracted_text = pytesseract.image_to_string(img)
            
            # Detect question type
            question_type = DoubtSolverAI._detect_question_type(extracted_text)
            
            # Detect subject
            subject = DoubtSolverAI._detect_subject(extracted_text)
            
            return {
                'extracted_text': extracted_text.strip(),
                'question_type': question_type,
                'subject': subject,
                'has_image': True
            }
        except Exception as e:
            return {
                'extracted_text': '',
                'question_type': 'general',
                'subject': 'general',
                'has_image': False,
                'error': str(e)
            }
    
    @staticmethod
    def _detect_question_type(text: str) -> str:
        """Detect the type of question from text."""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['solve', 'calculate', 'find', 'compute', 'evaluate']):
            return 'problem_solving'
        elif any(word in text_lower for word in ['explain', 'describe', 'what is', 'define']):
            return 'explanatory'
        elif any(word in text_lower for word in ['prove', 'show that', 'demonstrate']):
            return 'proof'
        elif any(word in text_lower for word in ['differentiate', 'integrate', 'derivative', 'limit']):
            return 'calculus'
        elif any(word in text_lower for word in ['equation', 'solve for', 'find x', 'find y']):
            return 'algebra'
        else:
            return 'general'
    
    @staticmethod
    def _detect_subject(text: str) -> str:
        """Detect the subject from question text."""
        text_lower = text.lower()
        
        # Mathematics indicators
        math_terms = ['integral', 'derivative', 'equation', 'function', 'matrix', 'vector', 
                      'probability', 'statistics', 'calculus', 'algebra', 'geometry']
        if any(term in text_lower for term in math_terms):
            return 'Mathematics'
        
        # Physics indicators
        physics_terms = ['force', 'energy', 'velocity', 'acceleration', 'mass', 'gravity',
                         'electric', 'magnetic', 'current', 'voltage', 'resistance']
        if any(term in text_lower for term in physics_terms):
            return 'Physics'
        
        # Chemistry indicators
        chem_terms = ['molecule', 'compound', 'reaction', 'acid', 'base', 'element',
                      'organic', 'inorganic', 'chemical', 'bond']
        if any(term in text_lower for term in chem_terms):
            return 'Chemistry'
        
        # Biology indicators
        bio_terms = ['cell', 'organism', 'species', 'gene', 'dna', 'protein', 'enzyme',
                     'tissue', 'organ', 'system']
        if any(term in text_lower for term in bio_terms):
            return 'Biology'
        
        # Computer Science indicators
        cs_terms = ['algorithm', 'programming', 'code', 'function', 'variable', 'loop',
                    'database', 'network', 'software', 'hardware']
        if any(term in text_lower for term in cs_terms):
            return 'Computer Science'
        
        return 'General'
    
    @staticmethod
    def generate_explanation(question: str, question_type: str, subject: str) -> str:
        """Generate a detailed explanation for the question."""
        
        # Try to get AI-powered response first
        ai_response = DoubtSolverAI._get_ai_response(question, question_type, subject)
        if ai_response:
            return ai_response
        
        # Fallback to template-based response
        if question_type == 'problem_solving':
            explanation = DoubtSolverAI._generate_problem_explanation(question, subject)
        elif question_type == 'explanatory':
            explanation = DoubtSolverAI._generate_concept_explanation(question, subject)
        elif question_type == 'proof':
            explanation = DoubtSolverAI._generate_proof_explanation(question, subject)
        else:
            explanation = DoubtSolverAI._generate_general_explanation(question, subject)
        
        return explanation
    
    @staticmethod
    def _get_ai_response(question: str, question_type: str, subject: str) -> str:
        """
        Get AI-powered response using external API if available.
        Returns None if no API is configured.
        """
        import os
        
        # Hardcoded API key (for demo purposes)
        GEMINI_API_KEY = "AIzaSyCQyWJ8McA8996M1wHBs2gRy33L9isVrhE"
        
        # Try Gemini API first with hardcoded key
        try:
            return DoubtSolverAI._call_gemini(question, question_type, subject, GEMINI_API_KEY)
        except Exception as e:
            print(f"Gemini API error: {e}")
            pass
        
        # Check for environment variable as fallback
        gemini_key = os.environ.get('GEMINI_API_KEY')
        if gemini_key:
            try:
                return DoubtSolverAI._call_gemini(question, question_type, subject, gemini_key)
            except:
                pass
        
        # Check for OpenAI API key
        openai_key = os.environ.get('OPENAI_API_KEY')
        if openai_key:
            try:
                return DoubtSolverAI._call_openai(question, question_type, subject, openai_key)
            except:
                pass
        
        # No API available, return None to use template
        return None
    
    @staticmethod
    def _call_openai(question: str, question_type: str, subject: str, api_key: str) -> str:
        """Call OpenAI API for intelligent response."""
        import requests
        
        prompt = f"""You are an expert {subject} tutor helping a student. 
        
The student asked: {question}

Question Type: {question_type}
Subject: {subject}

Provide a helpful, educational response that:
1. Directly addresses their specific question
2. Explains concepts clearly with examples
3. Provides step-by-step guidance if it's a problem
4. Includes relevant formulas or methods
5. Gives study tips specific to this topic

Format your response in markdown with clear headings."""

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': 'gpt-3.5-turbo',
            'messages': [
                {'role': 'system', 'content': 'You are a helpful educational tutor.'},
                {'role': 'user', 'content': prompt}
            ],
            'max_tokens': 1000,
            'temperature': 0.7
        }
        
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        return None
    
    @staticmethod
    def _call_gemini(question: str, question_type: str, subject: str, api_key: str) -> str:
        """Call Google Gemini API for intelligent response."""
        import requests
        
        prompt = f"""You are an expert {subject} tutor helping a student with their studies.

Student's Question: {question}

Question Type: {question_type}
Subject: {subject}

Please provide a comprehensive, educational response that:
1. Directly answers the specific question asked
2. Explains the underlying concepts clearly
3. Provides step-by-step reasoning if it's a problem
4. Includes relevant examples
5. Gives practical study tips

Format your response in markdown with clear headings."""

        # Use the correct Gemini API endpoint with gemini-1.5-flash model
        url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}'
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        data = {
            'contents': [{
                'role': 'user',
                'parts': [{'text': prompt}]
            }],
            'generationConfig': {
                'temperature': 0.7,
                'maxOutputTokens': 2048,
                'topP': 0.8,
                'topK': 40
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    candidate = result['candidates'][0]
                    if 'content' in candidate and 'parts' in candidate['content']:
                        return candidate['content']['parts'][0]['text']
            else:
                print(f"Gemini API Error: Status {response.status_code}")
                print(f"Response: {response.text}")
        except Exception as e:
            print(f"Gemini API Exception: {str(e)}")
        
        return None
    
    @staticmethod
    def _generate_problem_explanation(question: str, subject: str) -> str:
        """Generate step-by-step problem solving explanation."""
        # Extract key terms and context from the question
        question_lower = question.lower()
        
        # Identify specific topic keywords
        topic_keywords = []
        math_topics = ['integral', 'derivative', 'limit', 'equation', 'function', 'matrix', 'vector', 'probability', 'statistics']
        physics_topics = ['force', 'energy', 'velocity', 'acceleration', 'electric', 'magnetic', 'current', 'voltage']
        chem_topics = ['reaction', 'molecule', 'compound', 'acid', 'base', 'element', 'mole', 'concentration']
        
        all_topics = math_topics + physics_topics + chem_topics
        for topic in all_topics:
            if topic in question_lower:
                topic_keywords.append(topic)
        
        topics_str = ', '.join(topic_keywords[:3]) if topic_keywords else 'the relevant concepts'
        
        # Determine problem type
        if any(word in question_lower for word in ['find', 'calculate', 'determine', 'compute', 'evaluate']):
            action = "calculate the answer"
        elif any(word in question_lower for word in ['prove', 'show', 'demonstrate']):
            action = "prove the statement"
        elif any(word in question_lower for word in ['explain', 'describe', 'what is']):
            action = "explain the concept"
        else:
            action = "solve this problem"
        
        # Create contextual response
        response = f"""## Solution for Your {subject} Problem

**Your Question:**
{question}

### Understanding the Problem
This problem involves **{topics_str}** in {subject}. Let me break down how to {action}.

### Step-by-Step Approach

**Step 1: Identify What's Given**
Carefully read the problem and extract:
- All numerical values and units
- Conditions or constraints mentioned
- What exactly is being asked

**Step 2: Recall Relevant Concepts**
For this type of {subject} problem, you'll need to apply:
- Fundamental principles related to {topics_str}
- Appropriate formulas and equations
- Standard problem-solving techniques

**Step 3: Formulate a Strategy**
Based on the problem structure:
1. Start by writing down what you know
2. Identify the unknown you need to find
3. Choose the most direct method to connect knowns to unknowns
4. Work through the solution systematically

**Step 4: Execute and Verify**
- Show all your work clearly
- Include proper units throughout
- Check if your answer is reasonable
- Verify by substituting back if possible

### Specific Guidance for This Problem

Since your question involves {topics_str}, here are key points to remember:

"""
        
        # Add subject-specific guidance
        if subject == 'Mathematics':
            response += """
**For Mathematics Problems:**
- Write down all given information clearly
- Identify the appropriate formula or theorem
- Check for special cases or conditions
- Use diagrams when they help visualization
- Verify your calculations step by step
"""
        elif subject == 'Physics':
            response += """
**For Physics Problems:**
- Draw a clear diagram of the situation
- List all given quantities with units
- Identify the physical principles involved
- Check that your final answer has correct units
- Consider whether the magnitude makes physical sense
"""
        elif subject == 'Chemistry':
            response += """
**For Chemistry Problems:**
- Write balanced chemical equations if applicable
- Track units carefully (moles, grams, liters, etc.)
- Use stoichiometry relationships correctly
- Consider limiting reagents if multiple reactants
- Check significant figures in final answers
"""
        else:
            response += f"""
**For {subject} Problems:**
- Review the relevant chapter in your textbook
- Look for similar solved examples
- Break complex problems into smaller steps
- Practice with variations of this problem type
"""
        
        response += f"""
### Practice Recommendations

To master problems like this:
1. ✓ Solve 3-5 similar problems from your textbook
2. ✓ Try to explain the solution to someone else
3. ✓ Create your own variation of this problem
4. ✓ Review any mistakes to understand where you went wrong

### Need More Help?

If you're still stuck on a specific step:
- Tell me exactly where you're having trouble
- Share what you've tried so far
- Ask about a specific concept you're unsure about

Would you like me to elaborate on any particular aspect of this problem?"""
        
        return response
    
    @staticmethod
    def _generate_concept_explanation(question: str, subject: str) -> str:
        """Generate concept explanation."""
        return f"""## Explanation

Great question about {subject}! Let me help you understand this concept.

### Your Question
{question}

### Understanding the Concept
This is an important topic in {subject}. Here's what you need to know:

**Core Idea:**
The concept you're asking about is fundamental to {subject}. It involves understanding the principles and how they apply to various situations.

**Key Aspects:**
1. **Definition & Basics**: Start with the fundamental definition and basic principles
2. **How it Works**: Understand the mechanism or process behind this concept
3. **Applications**: See how this applies in real-world scenarios and problems
4. **Connections**: Learn how this relates to other topics in {subject}

### Learning Approach
To master this concept in {subject}:
- ✓ Read the relevant chapter in your textbook
- ✓ Work through solved examples
- ✓ Practice with different variations of problems
- ✓ Try to explain it in your own words

### Common Areas of Confusion
Students often struggle with:
- Understanding when to apply this concept
- Remembering the key formulas or principles
- Connecting it to related topics

### How to Remember
- Create your own examples
- Use flashcards for key definitions
- Teach the concept to someone else
- Practice regularly with different problem types

Does this help clarify your doubt? Feel free to ask follow-up questions or request specific examples!"""
    
    @staticmethod
    def _generate_proof_explanation(question: str, subject: str) -> str:
        """Generate proof explanation."""
        return f"""## Proof Guide

Let me help you approach this {subject} proof systematically.

### Your Question
{question}

### Understanding Proof Structure
In {subject}, a good proof requires clear logical steps. Here's how to approach it:

### Step 1: Analyze What You Need to Prove
- **Read carefully**: Understand exactly what statement needs to be proved
- **Identify given information**: Note all conditions, assumptions, and known facts
- **Define terms**: Make sure you understand all mathematical/scientific terms used

### Step 2: Plan Your Approach
Common proof techniques in {subject}:
- **Direct Proof**: Start from given information and logically reach the conclusion
- **Proof by Contradiction**: Assume the opposite and show it leads to a contradiction
- **Induction**: Prove for base case, then show if true for n, true for n+1
- **Contrapositive**: Prove "if not Q then not P" instead of "if P then Q"

### Step 3: Write the Proof
**Structure your proof clearly:**
1. State what you're proving
2. List given information
3. Show each logical step with justification
4. State your conclusion clearly

### Step 4: Review and Verify
- ✓ Is each step logically valid?
- ✓ Did you use all given information appropriately?
- ✓ Is the conclusion what you needed to prove?
- ✓ Would someone else be able to follow your reasoning?

### Tips for {subject} Proofs
- Start with the definitions of all terms involved
- Look for similar proofs in your textbook
- Practice writing proofs in your own words
- Ask yourself "why" at each step

Would you like me to explain any specific proof technique or help with a particular part of your proof?"""
    
    @staticmethod
    def _generate_general_explanation(question: str, subject: str) -> str:
        """Generate general explanation."""
        return f"""## Answer

Thank you for your question about {subject}!

### Your Question
{question}

### How I Can Help
I've analyzed your question about {subject}. Here's my guidance:

**Understanding Your Query:**
Your question relates to an important area of {subject}. Let me provide you with a structured approach to understanding this topic.

**Key Points to Consider:**
1. **Context**: Understanding where this fits in the broader {subject} curriculum
2. **Fundamentals**: Grasping the basic principles before moving to advanced topics
3. **Application**: Seeing how this knowledge applies to practical problems
4. **Practice**: Working through examples to reinforce understanding

**Recommended Approach:**
- Start by reviewing the relevant chapter or section in your textbook
- Look for solved examples that are similar to your question
- Try to break down the problem into smaller, manageable parts
- If you're stuck, identify exactly which step or concept is unclear

**Next Steps:**
- Practice similar problems to build confidence
- Create summary notes for quick revision
- Discuss with classmates or teachers if you need different perspectives
- Use the Smart Revision feature to schedule regular review of this topic

### How to Get Better Help
To get more specific assistance, you could:
- Share a specific example or problem you're working on
- Ask about a particular step or concept that's confusing
- Upload an image of the question or your work so far

Is there a specific part of this topic you'd like me to explain in more detail?"""
    
    @staticmethod
    def suggest_follow_up_questions(question: str, subject: str) -> List[str]:
        """Suggest follow-up questions for deeper understanding."""
        return [
            f"Can you explain the fundamental concept behind this {subject} problem?",
            "What are common mistakes students make with this type of question?",
            "Could you suggest similar practice problems?",
            "How does this relate to other topics in the syllabus?",
            "What are some real-world applications of this concept?"
        ]
    
    @staticmethod
    def get_study_tips(subject: str, topic: str = '') -> List[str]:
        """Get personalized study tips based on subject and topic."""
        tips = {
            'Mathematics': [
                "Practice regularly - math skills improve with consistent practice",
                "Understand the derivation of formulas, don't just memorize them",
                "Solve problems step-by-step, showing all your work",
                "Review mistakes to understand where you went wrong"
            ],
            'Physics': [
                "Focus on understanding concepts before solving numericals",
                "Draw diagrams to visualize problems",
                "Learn units and dimensions thoroughly",
                "Connect theory with real-world phenomena"
            ],
            'Chemistry': [
                "Create flowcharts for organic chemistry reactions",
                "Practice balancing equations regularly",
                "Understand periodic trends and their applications",
                "Make flashcards for chemical formulas and reactions"
            ],
            'Biology': [
                "Use diagrams and flowcharts for processes",
                "Create mnemonics for classification and names",
                "Understand rather than memorize",
                "Connect topics to see the bigger picture"
            ],
            'Computer Science': [
                "Write code by hand to practice syntax",
                "Understand algorithms before implementing",
                "Practice debugging - it's a crucial skill",
                "Build small projects to apply concepts"
            ],
            'General': [
                "Create a study schedule and stick to it",
                "Take regular breaks to maintain focus",
                "Teach concepts to others to reinforce learning",
                "Use active recall instead of passive reading"
            ]
        }
        
        return tips.get(subject, tips['General'])


class AutoNotesGenerator:
    """AI-powered notes generator that converts PDFs and lecture notes into short notes and mind maps."""
    
    @staticmethod
    def extract_text_from_file(file_path: str, file_type: str) -> str:
        """Extract text from various file formats."""
        try:
            print(f"Extracting text from {file_type} file: {file_path}")
            
            if file_type == 'pdf':
                return AutoNotesGenerator._extract_from_pdf(file_path)
            elif file_type == 'docx':
                return AutoNotesGenerator._extract_from_docx(file_path)
            elif file_type == 'txt':
                return AutoNotesGenerator._extract_from_txt(file_path)
            elif file_type == 'image':
                return AutoNotesGenerator._extract_from_image(file_path)
            else:
                print(f"Unsupported file type: {file_type}")
                return ""
        except Exception as e:
            import traceback
            print(f"Error extracting text: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            return ""
    
    @staticmethod
    def _extract_from_pdf(file_path: str) -> str:
        """Extract text from PDF using multiple methods."""
        text = ""
        
        # Try pdfplumber first
        try:
            print(f"Trying pdfplumber for: {file_path}")
            with pdfplumber.open(file_path) as pdf:
                print(f"PDF has {len(pdf.pages)} pages")
                for i, page in enumerate(pdf.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text and len(page_text.strip()) > 10:
                            text += page_text + "\n\n"
                            print(f"Page {i+1}: extracted {len(page_text)} characters")
                        else:
                            print(f"Page {i+1}: no text found")
                    except Exception as e:
                        print(f"Error on page {i+1}: {e}")
                        continue
            
            if len(text.strip()) > 50:
                print(f"pdfplumber success: {len(text)} characters")
                return text.strip()
        except Exception as e:
            print(f"pdfplumber failed: {e}")
        
        # Fallback: Try PyPDF2
        try:
            print("Trying PyPDF2 fallback...")
            import PyPDF2
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for i, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n\n"
                    except:
                        continue
            
            if len(text.strip()) > 50:
                print(f"PyPDF2 success: {len(text)} characters")
                return text.strip()
        except Exception as e:
            print(f"PyPDF2 failed: {e}")
        
        # If no text extracted, PDF might be scanned images
        print("No text extracted - PDF might be scanned images")
        return text.strip()
    
    @staticmethod
    def _extract_from_docx(file_path: str) -> str:
        """Extract text from Word document."""
        try:
            doc = Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip()])
            return text.strip()
        except Exception as e:
            print(f"DOCX extraction error: {e}")
            return ""
    
    @staticmethod
    def _extract_from_txt(file_path: str) -> str:
        """Extract text from text file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read().strip()
        except Exception as e:
            print(f"TXT extraction error: {e}")
            return ""
    
    @staticmethod
    def _extract_from_image(file_path: str) -> str:
        """Extract text from image using OCR."""
        try:
            from PIL import Image
            import pytesseract
            
            print(f"Processing image with OCR: {file_path}")
            img = Image.open(file_path)
            
            # Configure pytesseract for better accuracy
            custom_config = r'--oem 3 --psm 6'
            text = pytesseract.image_to_string(img, config=custom_config)
            
            print(f"OCR extracted: {len(text)} characters")
            return text.strip()
        except Exception as e:
            print(f"OCR error: {e}")
            return ""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and preprocess extracted text."""
        import re
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove page numbers (standalone numbers)
        text = re.sub(r'\n\s*\d+\s*\n', '\n', text)
        
        # Remove common headers/footers patterns
        text = re.sub(r'\b(page|pg)\s*\d+\b', '', text, flags=re.IGNORECASE)
        
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        # Fix multiple newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\.\,\;\:\!\?\-\(\)\[\]\"\'\n]', ' ', text)
        
        return text.strip()
    
    @staticmethod
    def extractive_summarize(text: str, num_sentences: int = 10) -> str:
        """Extractive summarization using TextRank-like approach."""
        import re
        from collections import Counter
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        if len(sentences) <= num_sentences:
            return text
        
        # Score sentences based on word frequency
        word_freq = Counter()
        for sentence in sentences:
            words = re.findall(r'\w+', sentence.lower())
            word_freq.update(words)
        
        # Score each sentence
        sentence_scores = []
        for sentence in sentences:
            words = re.findall(r'\w+', sentence.lower())
            if words:
                score = sum(word_freq[word] for word in words) / len(words)
                # Boost score for sentences with important keywords
                important_words = ['definition', 'important', 'key', 'main', 'concept', 'example', 'therefore', 'thus', 'conclusion']
                for word in important_words:
                    if word in sentence.lower():
                        score *= 1.5
                sentence_scores.append((sentence, score))
        
        # Sort by score and take top sentences
        sentence_scores.sort(key=lambda x: x[1], reverse=True)
        top_sentences = [s[0] for s in sentence_scores[:num_sentences]]
        
        # Reorder by original position
        top_sentences.sort(key=lambda s: text.find(s))
        
        return '. '.join(top_sentences) + '.'
    
    @staticmethod
    def identify_key_concepts(text: str) -> List[Dict]:
        """Identify key concepts and definitions from text."""
        import re
        
        concepts = []
        sentences = re.split(r'[.!?]+', text)
        
        # Pattern 1: "X is/are/was/were Y" definitions
        definition_pattern = r'([A-Z][a-zA-Z\s]+)\s+(?:is|are|was|were|refers to|means|defined as)\s+([^\.]+)'
        
        for sentence in sentences:
            matches = re.findall(definition_pattern, sentence, re.IGNORECASE)
            for match in matches:
                term = match[0].strip()
                definition = match[1].strip()
                if len(term) > 2 and len(definition) > 10:
                    concepts.append({
                        'term': term[:100],
                        'definition': definition[:500]
                    })
        
        # Pattern 2: Capitalized phrases that might be important terms
        capitalized = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', text)
        common_words = {'The', 'This', 'That', 'These', 'Those', 'There', 'They', 'Their', 'What', 'When', 'Where', 'Which', 'Who', 'Why', 'How', 'And', 'But', 'Or', 'For', 'Nor', 'Yet', 'So'}
        
        for term in set(capitalized):
            if term not in common_words and len(term) > 3:
                # Check if term appears multiple times (indicates importance)
                count = text.count(term)
                if count >= 2:
                    # Find context sentence
                    for sentence in sentences:
                        if term in sentence and len(sentence) > 50:
                            if not any(c['term'] == term for c in concepts):
                                concepts.append({
                                    'term': term,
                                    'definition': sentence[:300]
                                })
                            break
        
        return concepts[:15]  # Limit to top 15 concepts
    
    @staticmethod
    def extract_formulas(text: str) -> List[str]:
        """Extract mathematical formulas and equations."""
        import re
        
        formulas = []
        
        # Pattern 1: Equations with = sign and variables
        equation_pattern = r'[a-zA-Z]+\s*=\s*[^\n]+(?:\+|-|\*|/|\^)[^\n]+'
        formulas.extend(re.findall(equation_pattern, text))
        
        # Pattern 2: Mathematical expressions in parentheses
        math_pattern = r'\([^)]*(?:\+|-|\*|/|=)[^)]*\)'
        formulas.extend(re.findall(math_pattern, text))
        
        # Pattern 3: Lines that look like formulas (contain = and numbers/variables)
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if '=' in line and any(c.isalpha() for c in line) and len(line) < 150:
                # Check if it looks like a formula
                if re.search(r'[a-zA-Z]\s*=\s*\d', line) or re.search(r'[\+\-\*/\^]', line):
                    formulas.append(line)
        
        # Remove duplicates and clean
        unique_formulas = []
        for f in formulas:
            f_clean = f.strip()
            if f_clean and f_clean not in unique_formulas and len(f_clean) > 5:
                unique_formulas.append(f_clean)
        
        return unique_formulas[:20]  # Limit to top 20 formulas
    
    @staticmethod
    def generate_short_notes(text: str) -> Dict:
        """Generate concise short notes from text using AI and extractive methods."""
        # Step 1: Clean the text
        cleaned_text = AutoNotesGenerator.clean_text(text)
        print(f"Cleaned text length: {len(cleaned_text)} characters")
        
        if len(cleaned_text) < 100:
            return {
                'summary': cleaned_text,
                'key_points': ['Text too short for summarization'],
                'definitions': [],
                'formulas': [],
                'topics': []
            }
        
        # Step 2: Try AI-powered generation first
        ai_notes = AutoNotesGenerator._get_ai_notes(cleaned_text)
        if ai_notes and len(ai_notes.get('summary', '')) > 100:
            print("Using AI-generated notes")
            return ai_notes
        
        # Step 3: Fallback to extractive summarization
        print("Using extractive summarization")
        return AutoNotesGenerator._generate_extractive_notes(cleaned_text)
    
    @staticmethod
    def _generate_extractive_notes(text: str) -> Dict:
        """Generate notes using extractive summarization."""
        # Generate summary
        summary = AutoNotesGenerator.extractive_summarize(text, num_sentences=10)
        
        # Extract key concepts/definitions
        definitions = AutoNotesGenerator.identify_key_concepts(text)
        
        # Extract formulas
        formulas = AutoNotesGenerator.extract_formulas(text)
        
        # Generate key points from summary sentences
        key_points = []
        sentences = text.replace('!', '.').replace('?', '.').split('.')
        sentences = [s.strip() for s in sentences if len(s.strip()) > 30]
        
        # Score and select important sentences as key points
        for sentence in sentences[:15]:
            # Look for indicator words
            indicators = ['important', 'key', 'main', 'crucial', 'essential', 'significant', 
                         'note', 'remember', 'therefore', 'thus', 'conclusion', 'summary',
                         'first', 'second', 'third', 'finally', 'example', 'such as']
            if any(ind in sentence.lower() for ind in indicators):
                key_points.append(sentence)
        
        # If not enough key points, add more sentences
        if len(key_points) < 5:
            for sentence in sentences:
                if sentence not in key_points and len(key_points) < 10:
                    key_points.append(sentence)
        
        # Extract topics (capitalized phrases that appear multiple times)
        import re
        capitalized = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', text)
        common_words = {'The', 'This', 'That', 'These', 'Those', 'There', 'They', 'Their'}
        topics = []
        for term in set(capitalized):
            if term not in common_words and len(term) > 3 and text.count(term) >= 2:
                topics.append(term)
        
        return {
            'summary': summary,
            'key_points': key_points[:10],
            'definitions': definitions[:10],
            'formulas': formulas[:10],
            'topics': topics[:10]
        }
    
    @staticmethod
    def _get_ai_notes(text: str) -> Dict:
        """Get AI-generated notes using Gemini API."""
        GEMINI_API_KEY = "AIzaSyCQyWJ8McA8996M1wHBs2gRy33L9isVrhE"
        
        prompt = f"""You are an expert study assistant. Convert the following lecture notes into structured study materials.

Content:
{text[:8000]}  # Limit text to avoid token limits

Please provide:
1. A concise summary (3-5 paragraphs)
2. 5-10 key points as bullet points
3. Important definitions with explanations
4. Any formulas or equations mentioned
5. Main topics covered

Format as JSON with keys: summary, key_points, definitions, formulas, topics"""

        try:
            import requests
            import json
            
            url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}'
            
            headers = {'Content-Type': 'application/json'}
            data = {
                'contents': [{
                    'role': 'user',
                    'parts': [{'text': prompt}]
                }],
                'generationConfig': {
                    'temperature': 0.3,
                    'maxOutputTokens': 2048,
                }
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result:
                    ai_text = result['candidates'][0]['content']['parts'][0]['text']
                    # Parse AI response
                    return AutoNotesGenerator._parse_ai_notes_response(ai_text, text)
        except Exception as e:
            print(f"AI notes generation error: {e}")
        
        return None
    
    @staticmethod
    def _parse_ai_notes_response(ai_text: str, original_text: str) -> Dict:
        """Parse AI response into structured notes."""
        import re
        
        notes = {
            'summary': '',
            'key_points': [],
            'definitions': [],
            'formulas': [],
            'topics': []
        }
        
        # Extract summary (look for paragraphs before any headers)
        summary_match = re.search(r'^(.*?)(?=\n\n|\n#|\n\*\*|$)', ai_text, re.DOTALL)
        if summary_match:
            notes['summary'] = summary_match.group(1).strip()
        
        # Extract key points
        key_points_section = re.search(r'(?:key points?|main points?|bullet points?):?\s*\n((?:\*\s*.*?\n)+)', ai_text, re.IGNORECASE)
        if key_points_section:
            points = re.findall(r'\*\s*(.+)', key_points_section.group(1))
            notes['key_points'] = points[:10]
        
        # Extract definitions
        def_section = re.search(r'(?:definitions?|important terms?):?\s*\n(.*?)(?=\n\n|\n#|$)', ai_text, re.IGNORECASE | re.DOTALL)
        if def_section:
            defs = re.findall(r'[\*\-]\s*([^:]+):\s*(.+)', def_section.group(1))
            notes['definitions'] = [{'term': d[0].strip(), 'definition': d[1].strip()} for d in defs]
        
        # Extract formulas
        formulas = re.findall(r'(?:formula|equation):?\s*([^\n]+)', ai_text, re.IGNORECASE)
        notes['formulas'] = formulas[:10]
        
        # Extract topics
        topics_section = re.search(r'(?:topics?|subjects?):?\s*\n((?:\*\s*.*?\n)+)', ai_text, re.IGNORECASE)
        if topics_section:
            topics = re.findall(r'\*\s*(.+)', topics_section.group(1))
            notes['topics'] = topics[:10]
        
        return notes
    
    @staticmethod
    def _generate_template_notes(text: str) -> Dict:
        """Generate notes using template-based approach."""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        # Generate summary from first few and last few sentences
        summary_sentences = sentences[:3] + sentences[-2:] if len(sentences) > 5 else sentences[:5]
        summary = ' '.join(summary_sentences)
        
        # Extract key points (sentences with important keywords)
        important_keywords = ['important', 'key', 'main', 'crucial', 'essential', 'significant', 
                             'definition', 'means', 'refers', 'is called', 'consists of']
        key_points = [s for s in sentences if any(kw in s.lower() for kw in important_keywords)]
        key_points = key_points[:10] if key_points else sentences[:10]
        
        # Extract potential definitions
        definitions = []
        for sentence in sentences:
            if ' is ' in sentence or ' are ' in sentence or ' means ' in sentence:
                if len(sentence) < 200:
                    parts = re.split(r'\s+(?:is|are|means|refers to)\s+', sentence, maxsplit=1)
                    if len(parts) == 2:
                        definitions.append({
                            'term': parts[0].strip(),
                            'definition': parts[1].strip()
                        })
        
        # Extract potential formulas (lines with =, +, -, *, /, numbers)
        formulas = []
        lines = text.split('\n')
        for line in lines:
            if '=' in line and any(c.isdigit() for c in line):
                clean_line = line.strip()
                if 5 < len(clean_line) < 100:
                    formulas.append(clean_line)
        
        return {
            'summary': summary[:1000],
            'key_points': key_points[:10],
            'definitions': definitions[:10],
            'formulas': formulas[:10],
            'topics': []
        }
    
    @staticmethod
    def generate_mind_map(text: str, notes_data: Dict) -> Dict:
        """Generate mind map structure from notes."""
        # Try AI-powered mind map generation
        ai_mind_map = AutoNotesGenerator._get_ai_mind_map(text, notes_data)
        if ai_mind_map:
            return ai_mind_map
        
        # Fallback to template-based generation
        return AutoNotesGenerator._generate_template_mind_map(text, notes_data)
    
    @staticmethod
    def _get_ai_mind_map(text: str, notes_data: Dict) -> Dict:
        """Get AI-generated mind map structure."""
        GEMINI_API_KEY = "AIzaSyCQyWJ8McA8996M1wHBs2gRy33L9isVrhE"
        
        prompt = f"""Create a mind map structure from these notes.

Content:
{text[:5000]}

Create a hierarchical mind map with:
- Central topic as root
- Main branches (3-7 main topics)
- Sub-branches for each main topic

Return as JSON with this structure:
{{
    "root": "Central Topic",
    "branches": [
        {{
            "label": "Main Topic 1",
            "children": ["Sub-topic 1", "Sub-topic 2"]
        }}
    ]
}}"""

        try:
            import requests
            import json
            
            url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}'
            
            headers = {'Content-Type': 'application/json'}
            data = {
                'contents': [{
                    'role': 'user',
                    'parts': [{'text': prompt}]
                }],
                'generationConfig': {
                    'temperature': 0.3,
                    'maxOutputTokens': 2048,
                }
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result:
                    ai_text = result['candidates'][0]['content']['parts'][0]['text']
                    # Try to extract JSON
                    json_match = re.search(r'\{.*\}', ai_text, re.DOTALL)
                    if json_match:
                        return json.loads(json_match.group())
        except Exception as e:
            print(f"AI mind map generation error: {e}")
        
        return None
    
    @staticmethod
    def _generate_template_mind_map(text: str, notes_data: Dict) -> Dict:
        """Generate mind map using template-based approach."""
        # Extract main topics from text
        lines = text.split('\n')
        headings = [line.strip() for line in lines if line.strip() and len(line.strip()) < 100]
        
        # Use first sentence or heading as root
        root = "Main Topic"
        if headings:
            root = headings[0][:50]
        
        # Create branches from key points
        branches = []
        key_points = notes_data.get('key_points', [])[:7]
        
        for i, point in enumerate(key_points):
            branch = {
                'label': point[:50] if isinstance(point, str) else str(point)[:50],
                'children': []
            }
            # Add some sub-children based on text
            words = text.split()
            for j in range(3):
                if i * 10 + j < len(words):
                    branch['children'].append(words[i * 10 + j])
            branches.append(branch)
        
        return {
            'root': root,
            'branches': branches
        }
    
    @staticmethod
    def generate_mind_map_svg(mind_map_data: Dict) -> str:
        """Generate SVG representation of mind map."""
        if not mind_map_data or 'root' not in mind_map_data:
            return ""
        
        root = mind_map_data.get('root', 'Topic')
        branches = mind_map_data.get('branches', [])
        
        # SVG dimensions
        width = 800
        height = 600
        center_x = width // 2
        center_y = height // 2
        
        # Colors for branches
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F', '#BB8FCE']
        
        svg_parts = [
            f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">',
            '<rect width="100%" height="100%" fill="#f8f9fa"/>',
            f'<circle cx="{center_x}" cy="{center_y}" r="60" fill="#667eea"/>',
            f'<text x="{center_x}" y="{center_y}" text-anchor="middle" fill="white" font-size="14" font-family="Arial">{root[:20]}</text>'
        ]
        
        # Add branches
        num_branches = len(branches)
        if num_branches > 0:
            angle_step = 360 / num_branches
            
            for i, branch in enumerate(branches):
                angle = math.radians(i * angle_step)
                color = colors[i % len(colors)]
                
                # Calculate branch position
                branch_x = center_x + int(200 * math.cos(angle))
                branch_y = center_y + int(200 * math.sin(angle))
                
                # Draw line from center to branch
                svg_parts.append(f'<line x1="{center_x}" y1="{center_y}" x2="{branch_x}" y2="{branch_y}" stroke="{color}" stroke-width="3"/>')
                
                # Draw branch node
                svg_parts.append(f'<circle cx="{branch_x}" cy="{branch_y}" r="40" fill="{color}"/>')
                label = branch.get('label', f'Topic {i+1}')[:15]
                svg_parts.append(f'<text x="{branch_x}" y="{branch_y}" text-anchor="middle" fill="white" font-size="11" font-family="Arial">{label}</text>')
                
                # Add sub-children
                children = branch.get('children', [])
                for j, child in enumerate(children[:3]):
                    child_angle = angle + math.radians((j - 1) * 30)
                    child_x = branch_x + int(80 * math.cos(child_angle))
                    child_y = branch_y + int(80 * math.sin(child_angle))
                    
                    svg_parts.append(f'<line x1="{branch_x}" y1="{branch_y}" x2="{child_x}" y2="{child_y}" stroke="{color}" stroke-width="2"/>')
                    svg_parts.append(f'<circle cx="{child_x}" cy="{child_y}" r="25" fill="white" stroke="{color}" stroke-width="2"/>')
                    child_label = str(child)[:10]
                    svg_parts.append(f'<text x="{child_x}" y="{child_y}" text-anchor="middle" fill="#333" font-size="9" font-family="Arial">{child_label}</text>')
        
        svg_parts.append('</svg>')
        return '\n'.join(svg_parts)
