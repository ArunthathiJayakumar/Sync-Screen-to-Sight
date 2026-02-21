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
