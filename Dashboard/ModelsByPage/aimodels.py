from django.db import models
from authenticate.models import PortalUser
from Analysis.models import MultipleFileUpload, Analysis
from OnBoard.Ban.models import BaseDataTable
class BotChats(models.Model):
    user = models.ForeignKey(PortalUser, on_delete=models.CASCADE, related_name="user_chats")
    M_analysisChat = models.ForeignKey(MultipleFileUpload, on_delete=models.CASCADE, related_name="M_analysis_chats",null=True,blank=True)
    S_analysisChat = models.ForeignKey(Analysis, on_delete=models.CASCADE, related_name="S_analysis_chats",null=True,blank=True)
    billChat = models.ForeignKey(BaseDataTable, on_delete=models.CASCADE, related_name="view_chats",null=True,blank=True)
    question = models.TextField(null=False)
    response = models.TextField(null=True, blank=True)
    is_query_generated = models.BooleanField(default=False)
    is_query_ran = models.BooleanField(default=False)
    is_df_empty = models.BooleanField(default=False)
    recommended_questions = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'BotChats'

    def save(self, *args, **kwargs):
        if not self.is_query_generated:
            self.is_query_ran = False
            self.is_df_empty = True
        else:
            self.is_df_empty = False
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Chat by {self.user} at {self.created_at}"