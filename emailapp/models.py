from django.db import models

class Email(models.Model):
    uid = models.CharField(max_length=255, default='default_value_here')

    subject = models.CharField(max_length=255)
    sender = models.CharField(max_length=255)
    received_date = models.DateTimeField()
    body = models.TextField()

    def __str__(self):
        return self.subject
