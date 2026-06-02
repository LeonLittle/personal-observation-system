from django.db import models
#从django数据模块里拿models功能来用
from datetime import date
#datetime=python自带时间管理工具箱
#date是datetime时间管理工具箱里面的纯日期
from django.contrib.auth.models import User

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

    # 记录这一天属于哪个用户
    # null=True / blank=True 是为了兼容之前已经存在的测试数据
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="所属用户"
    )

    date = models.DateField(
        default=date.today, #default=默认值 date.today=今天的日期 default=date.today=如果没有指定日期,就默认为今天的日期
        # unique=True,    #unique=唯一 unique+True  =  唯一+开启 =  这个日期不能重复
        verbose_name="日期"
    )
    #models.DateField=纯日期字段

    mood =models.CharField(
        max_length=20,  #这个字段最长为20
        blank=True, 
        verbose_name="心情"
    )
    #models.CharField=短文本字段

    energy = models.IntegerField(
        null=True,  #null=数据库 null+True=允许数据库为空,用户非必须填写精力值
        blank=True, #blank=表单 允许为空
        verbose_name="精力值"
    )
    #models.IntegerField=整数数字字段

    summary = models.TextField(
        blank=True,  #blank=表单 blank+True=允许字段'表单'为空,用户非必须填写
        verbose_name = "今日总结"
    )
    #长文本不限制长度

    updated_at=models.DateTimeField(
        auto_now_add=True, #auto_now_add=只在创建时记录一次时间 anto_now_add+True=默认在创建时生成一次时间.
        verbose_name="创建时间"
    )
    #DateTimeField=日期+时间字段   django---定义数据库字段类型

    def __str__(self):
        """
        在后台调试时,显示这条记录对应的日期
        """
        return str(self.date)


class Task(models.Model):
    """
    Task 代表一条每日任务

    1. title:任务内容
    2. is_done:是否完成
    3. created_at:创建时间
    4. models.CharField是 django里的函数 models.CharField后面的参数都是django里的参数
    5.CharField短文本字段
    6.BooleanField布尔字段
    7.DateTimeField日期+时间字段
    8.verbose_name命名参数
    9.default默认参数
    10.auto_now_add记录第一次创建时间
    11.str 对象默认显示名称
    12..CASCADE级联删除,一起删除
    13..Foreignkey建立关系 指向一对多关系
    14.DailyRecord被指向的对象
    14.on_delete指向关联对象删除时状态
    15.related_name反向查找任务
    16.tasks以后可以从一条 DailyRecord 反过来找到它下面的所有 Task,名字叫 tasks
    """

    daily_record = models.ForeignKey(
        DailyRecord,
        on_delete = models.CASCADE,
        null=True,
        blank=True,
        related_name="tasks",
        verbose_name="所属日期记录"
    )
    #ForeignKey每一条Task任务,都指向一条DailyRecord每日记录 
    #on_delete = models.CASCADE阿如果被指向的DailyRecord被删除,那么指向它的Task也一起删除
    #related_name


    title = models.CharField(
        max_length=100,verbose_name="任务标题"
    )
    #CharField=短文本字段 max_length=100 最大字符100  verbose_name是django里面的命名参数


    is_done = models.BooleanField(
        default=False,verbose_name="是否完成"
    )
    #BooleanField布尔字段 只有True/False这两种状态  default=False默认是空,手动完成

    created_at = models.DateTimeField(
        auto_now_add=True,verbose_name="创建时间"
    )
    #DateTimeField日期+时间字段 auto_now_add=True 自动生成第一次创建时间 verbose_name=django里的命名参数

    def __str__(self):
        """
        当Django后台超级管理网站或调试时显示这个Task对象,
        直接显示title任务标题,方便我们识别,不然django默认显示Task object (1)。
        """
        return self.title