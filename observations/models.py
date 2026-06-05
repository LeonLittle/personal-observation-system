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

    show_on_home = models.BooleanField(
        default=False,
        verbose_name="是否在首页重点关注"
    )

    planned_start = models.TimeField(
        null=True,
        blank=True,
        verbose_name="计划开始时间"
    )

    planned_end = models.TimeField(
        null=True,
        blank=True,
        verbose_name="计划结束时间"
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="实际完成时间"
    )

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
    
class Habit(models.Model):
    """
    Habit 代表一个长期重复的习惯

    这里的Habit不是今天的一条任务,
    而是一个长期存在的"习惯模版"
    
    例如:
    1.早上学习python
    2.晚上英语练习
    3.运动30分钟

    Habit本身不直接代表某一天有没有完成.
    它后续会每天生成一条Task到今日行动里.

    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="所属用户"
    )
    #每个习惯都必须属于一个用户
    #这样不同用户之间的习惯不会混在一起
    #on_delete=models.CASCADE 便是用户被删除时,这个用户的习惯也一起删除

    title = models.CharField(
        max_length=100,
        verbose_name="习惯标题"
    )
    #习惯名称
    #例如:早上学习python/晚上英语练习/运动30分钟

    is_active = models.BooleanField(
        default=True,
        verbose_name="是否启用"
    )
    #True表示启用中
    #Flase表示已暂停

    default_focus = models.BooleanField(
        default=False,
        verbose_name="是否默认重点关注"
    )
    #后续习惯生在今日行动时,是否默认显示到首页终点关注
    #当前先保留这个字段,第一版页面暂时不做开关
    #默认False,避免首页被自动塞满

    created_at = models.DateTimeField(
        auto_now_add = True,
        verbose_name = "创建时间"
    )
    #记录这个习惯第一次创建的时间

    def __str__(self):
        """
        在Django后台或调试时,
        直接显示习惯标题,方便识别
        """
        return self.title
    

class HabitPeriod(models.Model):
    """
    HabitPeriod代表一个习惯的启用周期

    为什么需要这个模型?

    因为一个习惯可能经历:
    启用 -> 暂停 -> 恢复 -> 再暂停

    HabitPeriod就是用来保存这些历史周期的.
    后续ai分析时,可以知道用户什么时候持续了,
    什么时候暂停了,什么时候又恢复了.
    
    """

    habit = models.ForeignKey(
        Habit,
        on_delete = models.CASCADE,
        related_name="periods",
        verbose_name = "所属习惯"
    )
    #每一段周期都属于一个Habit
    #related_name="periods" 表示以后可以通过habit.periods 找到这个习惯的所有周期

    start_date  = models.DateField(
        default = date.today,
        verbose_name="开始日期"
    )
    #这一段习惯用哪一天开始启用

    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="结束日期"
    )
    #这一段习惯在哪一天结束
    #null=True/blank=Truue 表示可以为空
    #如果end_date为空,说明这一段习惯还在持续中

    created_at = models.DateTimeField(
        auto_now_add = True,
        verbose_name = "创建时间"
    )
    #记录这条周期数据第一次创建的时间

    def __str__(self):
            """
            在 Django 后台或调试时,
            显示这个周期属于哪个习惯。
            """
            return f"{self.habit.title}:{self.start_date} - {self.end_date or '持续中'}"