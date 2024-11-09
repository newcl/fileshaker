from django.db import models

# Create your models here.

class DedupeSource(models.Model):
    path = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file_path

class FileRecord(models.Model):
    file_path = models.CharField(max_length=255)
    file_hash = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file_path