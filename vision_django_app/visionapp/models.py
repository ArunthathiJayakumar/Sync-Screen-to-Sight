from django.db import models
from django.contrib.auth.models import User

class UserVisionData(models.Model):
    """Store user's vision test results for future use."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='vision_data')
    left_v = models.FloatField(default=1.0, help_text="Left eye visual acuity")
    right_v = models.FloatField(default=1.0, help_text="Right eye visual acuity")
    left_d = models.FloatField(default=0.0, help_text="Left eye diopter")
    right_d = models.FloatField(default=0.0, help_text="Right eye diopter")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - L:{self.left_d} R:{self.right_d}"

    class Meta:
        verbose_name = "User Vision Data"
        verbose_name_plural = "User Vision Data"


# ==================== AI EXAM PREPARATION MODELS ====================

class StudyMaterial(models.Model):
    """Stores uploaded study content with extracted text."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='study_materials')
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='study_materials/')
    extracted_text = models.TextField(blank=True)
    summary = models.TextField(blank=True)
    key_concepts = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.user.username}"

    class Meta:
        ordering = ['-created_at']


class Flashcard(models.Model):
    """Generated or manually created flashcards."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='flashcards')
    material = models.ForeignKey(StudyMaterial, on_delete=models.CASCADE, related_name='flashcards', null=True, blank=True)
    question = models.TextField()
    answer = models.TextField()
    context = models.TextField(blank=True, help_text="Source context for the flashcard")
    mastery_level = models.IntegerField(default=0, help_text="0-5 scale of mastery")
    review_count = models.IntegerField(default=0)
    last_reviewed = models.DateTimeField(null=True, blank=True)
    next_review = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Flashcard: {self.question[:50]}..."

    class Meta:
        ordering = ['-created_at']


class Quiz(models.Model):
    """Generated or custom quizzes."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quizzes')
    material = models.ForeignKey(StudyMaterial, on_delete=models.CASCADE, related_name='quizzes', null=True, blank=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    time_limit = models.IntegerField(default=10, help_text="Time limit in minutes")
    is_auto_generated = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = 'Quizzes'
        ordering = ['-created_at']


class QuizQuestion(models.Model):
    """Individual quiz questions."""
    QUESTION_TYPES = [
        ('mcq', 'Multiple Choice'),
        ('true_false', 'True/False'),
        ('fill_blank', 'Fill in the Blank'),
    ]

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    question_text = models.TextField()
    options = models.JSONField(default=list, blank=True, help_text="Options for MCQ questions")
    correct_answer = models.TextField()
    explanation = models.TextField(blank=True)
    order = models.IntegerField(default=0)

    def __str__(self):
        return f"Q{self.order}: {self.question_text[:50]}..."

    class Meta:
        ordering = ['order']


class QuizAttempt(models.Model):
    """User quiz attempts with scores and time tracking."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_attempts')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    score = models.IntegerField(default=0)
    total_questions = models.IntegerField(default=0)
    percentage = models.FloatField(default=0.0)
    time_taken = models.IntegerField(default=0, help_text="Time taken in seconds")
    answers = models.JSONField(default=dict, help_text="User's answers stored as JSON")
    completed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.quiz.title} - {self.percentage}%"

    class Meta:
        ordering = ['-completed_at']


class StudySession(models.Model):
    """Tracks study progress and sessions."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='study_sessions')
    material = models.ForeignKey(StudyMaterial, on_delete=models.CASCADE, related_name='study_sessions', null=True, blank=True)
    session_type = models.CharField(max_length=50, choices=[
        ('flashcard_review', 'Flashcard Review'),
        ('quiz', 'Quiz'),
        ('reading', 'Reading'),
    ])
    duration = models.IntegerField(default=0, help_text="Duration in minutes")
    items_reviewed = models.IntegerField(default=0)
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.session_type} - {self.duration}min"

    class Meta:
        ordering = ['-date']


class LearningResource(models.Model):
    """Recommended learning resources for topics."""
    RESOURCE_TYPES = [
        ('video', 'Video'),
        ('article', 'Article'),
        ('course', 'Course'),
        ('documentation', 'Documentation'),
        ('book', 'Book'),
        ('tutorial', 'Tutorial'),
    ]

    topic = models.CharField(max_length=100)
    title = models.CharField(max_length=255)
    url = models.URLField()
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPES)
    description = models.TextField(blank=True)
    rating = models.FloatField(default=0.0, help_text="Rating from 0-5")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.resource_type})"

    class Meta:
        ordering = ['-rating', '-created_at']


class StudyPlan(models.Model):
    """AI-generated study plan for exam preparation."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='study_plans')
    title = models.CharField(max_length=255)
    exam_date = models.DateField()
    syllabus = models.TextField(help_text="Topics to cover for the exam")
    daily_study_hours = models.FloatField(default=2.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.title} - {self.user.username}"

    class Meta:
        ordering = ['-created_at']


class StudySchedule(models.Model):
    """Daily study schedule items."""
    study_plan = models.ForeignKey(StudyPlan, on_delete=models.CASCADE, related_name='schedule_items')
    date = models.DateField()
    topic = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    estimated_minutes = models.IntegerField(default=60)
    is_completed = models.BooleanField(default=False)
    is_skipped = models.BooleanField(default=False)
    completion_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.topic} - {self.date}"

    class Meta:
        ordering = ['date', 'created_at']


class PreviousExamQuestion(models.Model):
    """Previous year exam questions for pattern analysis."""
    QUESTION_TYPES = [
        ('mcq', 'Multiple Choice'),
        ('short', 'Short Answer'),
        ('long', 'Long Answer'),
        ('essay', 'Essay'),
        ('problem', 'Problem Solving'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='previous_exam_questions')
    subject = models.CharField(max_length=100)
    year = models.IntegerField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    question_text = models.TextField()
    topic = models.CharField(max_length=200, help_text="Topic/Chapter this question belongs to")
    marks = models.IntegerField(default=5)
    frequency_count = models.IntegerField(default=1, help_text="How many times this topic appeared")
    difficulty_level = models.IntegerField(default=3, choices=[(1, 'Easy'), (2, 'Medium'), (3, 'Hard'), (4, 'Very Hard')])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.subject} - {self.year} - {self.topic}"

    class Meta:
        ordering = ['-year', 'subject', 'topic']


class SmartRevision(models.Model):
    """Spaced repetition tracking for topics."""
    INTERVAL_CHOICES = [
        (1, '1 day'),
        (2, '2 days'),
        (3, '3 days'),
        (7, '1 week'),
        (14, '2 weeks'),
        (30, '1 month'),
        (60, '2 months'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='smart_revisions')
    topic = models.CharField(max_length=255)
    subject = models.CharField(max_length=100, blank=True)
    last_reviewed = models.DateField(null=True, blank=True)
    next_review = models.DateField()
    review_count = models.IntegerField(default=0)
    interval_days = models.IntegerField(default=1, choices=INTERVAL_CHOICES)
    ease_factor = models.FloatField(default=2.5, help_text="SM-2 algorithm ease factor")
    is_mastered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.topic} - Next: {self.next_review}"

    class Meta:
        ordering = ['next_review', 'topic']


class RevisionSession(models.Model):
    """Track individual revision sessions."""
    QUALITY_CHOICES = [
        (0, 'Complete blackout'),
        (1, 'Incorrect response, correct one remembered'),
        (2, 'Incorrect response, easy to recall correct'),
        (3, 'Correct with serious difficulty'),
        (4, 'Correct with hesitation'),
        (5, 'Perfect response'),
    ]
    
    revision = models.ForeignKey(SmartRevision, on_delete=models.CASCADE, related_name='sessions')
    reviewed_at = models.DateTimeField(auto_now_add=True)
    quality = models.IntegerField(choices=QUALITY_CHOICES, default=3)
    time_spent_minutes = models.IntegerField(default=0)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.revision.topic} - {self.reviewed_at.date()}"

    class Meta:
        ordering = ['-reviewed_at']


class DoubtSession(models.Model):
    """Chat session for AI doubt solving."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='doubt_sessions')
    title = models.CharField(max_length=255, blank=True)
    subject = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Doubt Session {self.id} - {self.user.username}"

    class Meta:
        ordering = ['-updated_at']


class DoubtMessage(models.Model):
    """Individual messages in a doubt session."""
    MESSAGE_TYPES = [
        ('user', 'User'),
        ('ai', 'AI'),
        ('system', 'System'),
    ]
    
    session = models.ForeignKey(DoubtSession, on_delete=models.CASCADE, related_name='messages')
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES)
    text = models.TextField()
    image = models.ImageField(upload_to='doubt_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.message_type}: {self.text[:50]}..."

    class Meta:
        ordering = ['created_at']


# ==================== AUTO NOTES GENERATOR MODELS ====================

class GeneratedNotes(models.Model):
    """Stores AI-generated notes from uploaded materials."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='generated_notes')
    title = models.CharField(max_length=255)
    original_file = models.FileField(upload_to='notes_uploads/')
    file_type = models.CharField(max_length=20, choices=[
        ('pdf', 'PDF'),
        ('docx', 'Word Document'),
        ('txt', 'Text File'),
        ('image', 'Image'),
    ])
    
    # Short Notes
    short_notes = models.TextField(help_text="Concise summary notes")
    key_points = models.JSONField(default=list, help_text="List of key points")
    important_definitions = models.JSONField(default=list, help_text="Key definitions extracted")
    formulas = models.JSONField(default=list, help_text="Formulas and equations")
    
    # Mind Map Data
    mind_map_data = models.JSONField(default=dict, help_text="Mind map structure in JSON")
    mind_map_svg = models.TextField(blank=True, help_text="SVG representation of mind map")
    
    # Metadata
    extracted_text = models.TextField(blank=True, help_text="Raw text extracted from file")
    page_count = models.IntegerField(default=1)
    processing_status = models.CharField(max_length=20, default='pending', choices=[
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.user.username}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Generated Notes"
        verbose_name_plural = "Generated Notes"


class MindMapNode(models.Model):
    """Individual nodes in a mind map for more complex structures."""
    notes = models.ForeignKey(GeneratedNotes, on_delete=models.CASCADE, related_name='mind_map_nodes')
    node_id = models.CharField(max_length=50)
    label = models.CharField(max_length=255)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    level = models.IntegerField(default=0, help_text="Hierarchy level (0 = root)")
    color = models.CharField(max_length=20, default='#667eea')
    description = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.label} ({self.notes.title})"
