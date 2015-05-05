from django.db import models

class APISession(models.Model):
  login_uri = models.CharField("Login URI", max_length=1024, primary_key=True)
  modified = models.DateTimeField("Last modified", auto_now=True)
  # Serialized representation of the session
  serialized = models.BinaryField("Serialized session")
