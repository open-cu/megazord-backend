from django.db import models

from accounts.models import Account


class MiniInterview(models.Model):
    name = models.CharField(max_length=200, blank=False)
    description = models.TextField(blank=False)
    intended_to = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="intended_to"
    )  # потенциальный наемный сотрудник
    employee = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="employee"
    )  # работадатель


class YesOrNoQ(models.Model):
    mini_interview = models.ForeignKey(MiniInterview, on_delete=models.CASCADE)
    q_text = models.CharField(max_length=200, blank=False)
    answer = models.BooleanField(default=False)


class CheckBoxQ(models.Model):
    mini_interview = models.ForeignKey(MiniInterview, on_delete=models.CASCADE)
    q_text = models.CharField(max_length=200, blank=False)
    is_checked = models.BooleanField(default=False)


class TextQ(models.Model):
    mini_interview = models.ForeignKey(MiniInterview, on_delete=models.CASCADE)
    q_text = models.TextField(blank=False)
    q_answer = models.TextField(blank=False)
