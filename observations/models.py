from django.db import models

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