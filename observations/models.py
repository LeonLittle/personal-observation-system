from django.db import models
from datetime import date

class DailyRecord(models.Model):
    """
    DailyRecord 代表某一天的个人状态记录

    这个模型是"个人观察助手"的核心之一
    它不是记录任务,而是记录这一天的:
    1.今天心情如何
    2.今天精力如何
    3.今天发生了什么
    verbose_name参数:显示名称
    """

    date = models.DateField(
        default=date.today,
        unique=True,
        verbose_name="日期"
    )

    mood =models.CharField(
        max_length=20,
        blank=True,
        verbose_name="心情"
    )

    energy = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="精力分"
    )

    summary = models.TextField(
        blank=True,
        verbose_name = "今日总结"
    )

    updated_at=models.DateTimeField(
        auto_now_add=True,
        verbose_name="创建时间"
    )

    def __str__(self):
        """
        在后台调试时,显示这条记录对应的日期
        """
        return str(self.date)


class Task(models.Model):
    """
    Task 代表一条每日任务

    现在是第一版，所以字段先保持简单：
    1. title:任务标题
    2. is_done:是否完成
    3. created_at:创建时间
    """

    title = models.CharField(
        max_length=100,verbose_name="任务标题"
    )

    is_done = models.BooleanField(
        default=False,verbose_name="是否完成"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,verbose_name="创建时间"
    )

    def __str__(self):
        """
        当Django后台或调试时显示这个对象,
        直接显示任务标题，方便我们识别。
        """
        return self.title