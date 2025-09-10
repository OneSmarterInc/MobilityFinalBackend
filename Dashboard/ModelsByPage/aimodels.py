from django.db import models
from authenticate.models import PortalUser
class BotChats(models.Model):
    user = models.ForeignKey(PortalUser, on_delete=models.CASCADE, related_name="user_chats")
    question = models.TextField(null=False)
    response = models.TextField(null=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'BotChats'

    def __str__(self):
        return f"Chat by {self.user} at {self.created_at}"