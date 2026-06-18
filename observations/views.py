from django.shortcuts import render,redirect,get_object_or_404
from django.utils import timezone
from datetime import datetime
from .models import Task,DailyRecord,Habit,HabitPeriod
#1. render作用:把数据交给HTML页面,然后生成网页返回给浏览器 意思:生成网页
#2. redirect作用:跳转到另一个页面  意思:保存完任务后,重新回到首页 
#3. get_object_or_404作用:代码安全维护  意思:去数据库找某条数据;找不到就显示404错误页
#4. from datetime import datetime是在python里的datetime时间管理模块 导入datetime日期+时间工具
#5. shortcuts是django快捷工具箱
from django.contrib.auth.decorators import login_required

@login_required
def home(request):
    """ 首页视图函数。

    当前页面只负责展示今日摘要

    主要做几件事
    1. 获取今天日期
    2. 获取或创建今天的 DailyRecord
    3. 读取今天所有任务
    4. 统计待完成、已完成、总行动数
    5. 把数据交给 home.html 页面显示
    6. 筛选首页重点关注任务
    7. 把数据交给 home.html 页面显示
    """
    
    today = datetime.now()
    #命名了一个today变量来获取今日日期+时间

    today_record,created = DailyRecord.objects.get_or_create(
        user=request.user,
        date=today.date()
    )

    #今天的所有任务
    tasks = Task.objects.filter(
        daily_record=today_record,
        is_cancelled=False
    ).order_by("-created_at")

    # 今天未完成任务
    undone_tasks = tasks.filter(is_done=False)

    # 今天已完成任务
    done_tasks = tasks.filter(is_done=True)

    # 今天标记的重点任务
    next_tasks = undone_tasks.filter(
        show_on_home=True
    )

    # .count数量统计
    undone_count = undone_tasks.count()
    done_count = done_tasks.count()
    total_count = tasks.count()

    context = {
        #左边是html里使用的名字
        #右边Python里的真实变量
        #.strftime()把日期时间05/31格式化成指定名字05月/31日
        #.weekday()计算星期几,并返回对应编号
        "title":"个人观察助手",
        "date_text" : today.strftime("%m月%d日"),
        "weekday_text":["星期一","星期二","星期三","星期四","星期五","星期六","星期日"][today.weekday()],
        "next_tasks": next_tasks,#今天重点任务
        "undone_count": undone_count,#今天未完成任务统计
        "done_count": done_count,#今天已完成任务统计
        "total_count": total_count,#今天所有任务统计
        "today_record":today_record,#今天的状态
    }

    return render(request,"observations/home.html",context)
    #把context的数据交给"observations/home.html" render生成到最终页面

@login_required
def task_list_view(request):
    """
    今日行动页视图函数

    这个页面专门负责:
    1.显示今天全部任务
    2.区分未完成任务和已完成任务
    3.添加新任务
    """

    today=datetime.now()

    today_record,created = DailyRecord.objects.get_or_create(
        user=request.user,
        date=today.date()
    )


    # 读取当前用户所有启用中的习惯。
    # 这些习惯会自动生成到今天的“今日行动”里。
    active_habits = Habit.objects.filter(
        user=request.user,
        is_active=True,  #已启用的行动
        is_deleted=False
    )

    for habit in active_habits:
        # 先检查今天是否已经有这条习惯生成过的 Task。
        # 如果已经存在，就不再重复生成。
        has_generated_task = Task.objects.filter(
            daily_record=today_record,   #今天的daily_record_id
            source_habit=habit,           #soure_habit_id
            is_cancelled=False
        ).exists()
        #.exists() 判断筛选数据返回True/False

        if has_generated_task:
            continue

        # 如果今天还没有这条习惯对应的 Task，
        # 就自动创建一条新的今日行动。
        Task.objects.create(
            title=habit.title,
            daily_record=today_record,
            source_habit=habit,
            show_on_home=habit.default_focus
        )
        #左边是字段名,右边是值



    #添加今日任务
    if request.method == "POST":
        title = request.POST.get("title")
        planned_start = request.POST.get("planned_start") or None
        planned_end = request.POST.get("planned_end") or None

        if title:
            Task.objects.create(
                title=title,
                daily_record=today_record,
                planned_start=planned_start,
                planned_end=planned_end
            )

        return redirect("task_list")
    
    #未完成任务
    undone_tasks = Task.objects.filter(
        daily_record=today_record,
        is_done=False,
        is_cancelled=False
    ).order_by("-created_at")

    #已完成任务
    done_tasks = Task.objects.filter(
        daily_record=today_record,
        is_done=True,
        is_cancelled=False
    ).order_by("-created_at")

    #统计未完成/已完成/总和数量
    undone_count =undone_tasks.count()
    done_count = done_tasks.count()
    total_count = undone_count+done_count

    context = {
        "title":"今日任务",
        "date_text" : today.strftime("%m月%d日"),
        "weekday_text":["星期一","星期二","星期三","星期四","星期五","星期六","星期日"][today.weekday()],
        "today_record":today_record,
        "undone_tasks":undone_tasks,
        "done_tasks":done_tasks,
        "undone_count":undone_count,
        "done_count":done_count,
        "total_count":total_count,
    }
    return render(request,"observations/tasks.html",context)

@login_required
def record_view(request):
    """
    今日状态页视图函数。

    这个页面专门负责：
    1. 显示今天的心情、精力、总结
    2. 保存今日状态记录
    3. 保存后回到首页
    """
    today = datetime.now()

    today_record,created =DailyRecord.objects.get_or_create(
        user=request.user,
        date=today.date()
    )

    if request.method == "POST":
        today_record.mood = request.POST.get("mood","")
        #把提交的表单里的mood数据(空的也可以)给到模型里的mood字段

        energy = request.POST.get("energy")
        #把提交的表单里的energy数据给到模型里的energy变量

        today_record.summary = request.POST.get("summary","")
        #把提交的表单里的summary数据(空的也可以)给到模型里的summary字段

        #energy变量转换成整型给到energy字段 else提交时如果没有数据可以起到把旧值清空作用
        if energy:
            today_record.energy = int(energy)
        else:
            today_record.energy = None

        today_record.save()
        #保存数据入库SQLite

        return redirect("record")
        #保存后回到本页

        
    ticket_data = today_ticket(today_record)
    

    context = {
        "title":"今日状态记录",
        "date_text" : today.strftime("%m月%d日"),
        "weekday_text":["星期一","星期二","星期三","星期四","星期五","星期六","星期日"][today.weekday()],
        "today_record":today_record,
        "ticket_data":ticket_data,
    }
    
    return render(request,"observations/record.html",context)

@login_required
def history_view(request):
    """
    最近观察视图函数

    作用:
    1.读取最近7天的DailyRecord 状态还是任务?
    2.计算每一天的任务完成数量 
    3.把整理好的历史数据交给history.html显示
    """

    #找到当前网页登录的用户数据根据日期倒序排列,只显示前七天的一组数据给到records(列表)
    records = DailyRecord.objects.filter(
        user=request.user
    ).order_by("-date")[:7]

    history_items = []

    #循环records列表逐条给到record变量
    for record in records:
        #反向查询当前record变量下相关DailyRecord_id的Task.daily_record_id数据,根据创建时间倒序,给到左边变量tasks
        tasks=record.tasks.filter(
            is_cancelled=False
        ).order_by("created_at")

        #根据tasks变量的数据统计数量
        total_count= tasks.count()

        #筛选tasks里的Task.daily_record_id的is_done=True的数据统计 给到左边变量为已完成的任务
        done_count = tasks.filter(is_done=True).count()

        #total_count列表
        history_items.append({
            "record": record,#一组DailyRecord对象
            "tasks": tasks,#相关daily_record_id列表
            "total_count": total_count,#daily_record_id数量
            "done_count": done_count,#daily_record_id里is_done为True的数量
        })

    context={
        "title":"最近观察",
        "history_items":history_items,
    }

    return render(request,"observations/history.html",context)

@login_required
def habits_view(request):
    """
    习惯页面视图函数

    这个页面目前只做3件事:
    1.添加一个新的习惯
    2.显示当前启用中的习惯
    3.显示已经暂停的习惯
    """

    today = datetime.now().date()
    #获取今天的日期
    #这里使用date(),只要年月日,不要具体时分秒

    if request.method == "POST":
        #如果用户提交了表单,说明用户想新增一个习惯.

        title = request.POST.get("title")
        #从表单里拿到用户输入的习惯标题

        if title:
            #如果用户确实输入了内容,才创建习惯

            habit = Habit.objects.create(
                user=request.user,
                title=title,
                is_active=True # is_active=True 表示新建后默认启用
            )
            #创建Habit,
            #user=request.user表示这个习惯属于当前登录用户
            # title=title 表示习惯名称
            

            HabitPeriod.objects.create(
                habit=habit,
                start_date=today
            )
            #创建HabitPeriod,
            # 每新增一个启用中的习惯，就同步创建一段“持续周期”
            #start_date=today 表示这个习惯从今天开始持续
            # end_date 默认是空，表示还在持续中

        return redirect("habits")
        # 添加完成后，重新回到习惯页面。

    active_habits = Habit.objects.filter(
        #查询当前用户已经启用的习惯
        user=request.user,
        is_active=True,
        is_deleted=False
    ).order_by("-created_at")

    paused_habits = Habit.objects.filter(
        #查询当前用户已经暂停的习惯
        user=request.user,
        is_active=False,
        is_deleted=False
    ).order_by("-created_at")


    active_habit_items = []
    # 这里专门整理启用中的习惯数据。
    # 因为页面要显示“已持续多少天”，所以不能只把 habit 原样传过去。

    for habit in active_habits:
        #找到这个习惯当前正在持续的周期
        #end_date为空,表示这一段还没结束
        current_period = habit.periods.filter(
            end_date__isnull = True  #__isnull这里要用查询 不能直接=True
        ).order_by("-start_date").first()

        if current_period:
            #计算启用时间
            active_days = (today - current_period.start_date).days +1
            
            active_habit_items.append({
                "habit": habit,
                "active_days":active_days,
            })

    context={
        "title":"习惯",
        "active_habit_items":active_habit_items,
        "paused_habits":paused_habits,
    }
    
    return render(request,"observations/habits.html",context)

@login_required
def delete_task(request, task_id):
    """
    删除任务视图函数。

    当前规则：
    1. 删除任务只属于“今日任务页”的管理行为
    2. 删除完成后返回今日任务页
    3. 首页不再承担删除任务功能
    """

    # 根据任务 id 找到对应任务
    # 如果找不到，就返回 404，避免程序直接报错
    task =  get_object_or_404(Task, id=task_id)
    # Task.objects.get(id=task_id) 

    # 删除这条任务
    task.delete()

    # 删除后回到今日任务页，而不是首页
    return redirect("task_list")


@login_required
def pause_habit(request, habit_id):
    """
    暂停习惯

    做三件事：
    1. 把 Habit.is_active 改成 False
    2. 把当前正在持续的 HabitPeriod 结束日期设为今天
    3. 把今天未完成的习惯任务标记为取消，而不是直接删除

    这样做的原因：
    个人观察助手需要保留长期真实数据。
    直接 delete Task 会丢失“这个习惯今天曾经生成过任务”的历史痕迹。
    """

    today = datetime.now().date()

    habit = get_object_or_404(
        Habit,
        id=habit_id,
        user=request.user,
        is_deleted=False
    )

    habit.is_active = False
    habit.save()

    current_period = habit.periods.filter(
        end_date__isnull=True
    ).order_by("-start_date").first()

    if current_period:
        current_period.end_date = today
        current_period.save()

    today_record = DailyRecord.objects.filter(
        user=request.user,
        date=today
    ).first()

    if today_record:
        Task.objects.filter(
            daily_record=today_record,
            source_habit=habit,
            is_done=False,
            is_cancelled=False
        ).update(
            is_cancelled=True,
            cancelled_at=timezone.now(),
            show_on_home=False
        )

    return redirect("habits")


@login_required
def resume_habit(request, habit_id):
    """
    恢复习惯

    做两件事：
    1. 把 Habit.is_active 改成 True
    2. 如果当前没有未结束周期，就新建一条 HabitPeriod

    注意：
    已经软删除的习惯不能恢复。
    """

    today = datetime.now().date()

    habit = get_object_or_404(
        Habit,
        id=habit_id,
        user=request.user,
        is_active=False,
        is_deleted=False
    )

    habit.is_active = True
    habit.save()

    has_open_period = habit.periods.filter(
        end_date__isnull=True
    ).exists()

    if not has_open_period:
        HabitPeriod.objects.create(
            habit=habit,
            start_date=today
        )

    return redirect("habits")

@login_required
def delete_habit(request, habit_id):
    """
    删除习惯

    注意：
    这里不做数据库真删除，而是软删除。

    原因：
    个人观察助手需要长期保存真实数据。
    如果直接 habit.delete():
    1. Habit 会消失
    2. HabitPeriod 会被 CASCADE 一起删除
    3. Task.source_habit 会因为 SET_NULL 变成空
    4. 后续 AI 分析会失去“任务来源于哪个习惯”的依据
    """

    today = datetime.now().date()

    habit = get_object_or_404(
        Habit,
        id=habit_id,
        user=request.user,
        is_active=False,
        is_deleted=False
    )

    habit.is_active = False
    habit.is_deleted = True
    habit.deleted_at = timezone.now()
    habit.save()

    current_period = habit.periods.filter(
        end_date__isnull=True
    ).order_by("-start_date").first()

    if current_period:
        current_period.end_date = today
        current_period.save()

    today_record = DailyRecord.objects.filter(
        user=request.user,
        date=today
    ).first()

    if today_record:
        Task.objects.filter(
            daily_record=today_record,
            source_habit=habit,
            is_done=False,
            is_cancelled=False
        ).update(
            is_cancelled=True,
            cancelled_at=timezone.now(),
            show_on_home=False
        )

    return redirect("habits")

@login_required
def toggle_task(request, task_id):
    """
    切换任务完成状态。

    当前规则：
    1. 如果任务未完成，点击后变成完成，并记录完成时间
    2. 如果任务已完成，点击后恢复未完成，并清空完成时间
    3. 根据 next 参数决定操作完成后回到哪个页面
    """

    task = get_object_or_404(Task, id=task_id)

    if not task.is_done:
        task.is_done = True
        task.completed_at = timezone.now()
    else:
        task.is_done = False
        task.completed_at = None

    task.save()

    next_page = request.GET.get("next")

    if next_page == "task_list":
        return redirect("task_list")

    return redirect("home")

def toggle_home_focus(request, task_id):
    """
    切换任务是否作为首页重点关注。

    作用：
    1. 根据 task_id 找到对应任务
    2. 如果它现在不是重点关注，就设为重点关注
    3. 如果它现在已经是重点关注，就取消重点关注
    4. 操作完成后回到今日任务页
    """

    # 根据任务 id 找到这条任务
    # 如果找不到，就返回 404 页面，避免程序直接报错
    task = get_object_or_404(Task, id=task_id)

    # True 变 False，False 变 True
    # 也就是：点击一次选中，再点击一次取消
    task.show_on_home = not task.show_on_home

    # 保存修改
    task.save()

    # 回到今日任务页
    return redirect("task_list")



def today_ticket(today_record):
    """
    今日小票数据统计 数据生成  制定规则
    """

    mood=today_record.mood or ""
    energy=today_record.energy 
    summary=today_record.summary or ""

    has_today_state=(
        mood 
        or energy is not None 
        or summary
    )

    has_today_state=(
        mood.strip()
        or energy is not None
        or summary.strip()
    )

    if not has_today_state:
        return None
    
    tasks = today_record.tasks.filter(
        is_cancelled=False
    )

    total_count = tasks.count()
    done_count = tasks.filter(
        is_done=True
    ).count()

    if energy is None:
        body_text = "信号未记录"
    elif energy <= 4 :
        body_text = "低电量模式"
    elif energy <= 7 :
        body_text = "普通运行中"
    else:
        body_text = "状态在线"

    if total_count == 0:
        completion_rate = None
        action_text = "今日未派单"
    else:
        completion_rate = done_count / total_count

        if completion_rate < 0.4:
            action_text = "间歇性上线"
        elif completion_rate < 0.8:
            action_text = "缓慢推进"
        else:
            action_text = "稳定在线"

    if "焦躁" in mood or "冒烟" in mood:
        emotion_text = "轻微冒烟"
    elif "空" in mood:
        emotion_text = "有点空"
    elif "平稳" in mood:
        emotion_text = "后台稳定"
    elif "疲惫" in mood:
        emotion_text = "低速运行"
    elif "摆烂" in mood:
        emotion_text = "暂停服务"
    elif "充实" in mood:
        emotion_text = "状态回暖"
    else:
        emotion_text = "后台运行中"
    
    summary_length = len(summary)

    if summary_length == 0:
        brain_text = "暂无记录信号"
    elif summary_length <= 10:
        brain_text = "简短汇报"
    elif summary_length <=20:
        brain_text = "正在处理信息"
    else:
        brain_text = "后台会议较多"

    if energy is not None and energy <= 4:
        result_text = "今天没有满分,但也没有清零"
        voucher_text = "只要没清零，就还有明天"
        stamp_text = "准许低功率运行"
    elif total_count is not None and completion_rate>= 0.8:
        result_text="建议奖励罐头一份"
        stamp_text="不允许骄傲"
    else:
        result_text = "今天的你,主打一个能活就行."
        voucher_text = "微弱发光，也算没黑屏"
        stamp_text = "准许普通发光"


    ticket_data = {
        "body":body_text,
        "action":action_text,
        "emotion":emotion_text,
        "brain":brain_text,
        "task_text": f"{done_count} / {total_count}",
        "energy_text": "未记录" if energy is None else f"{energy} / 10",#这个不是很重要 可以不显示
        "result": result_text,
        "stamp_text": stamp_text,
        "voucher_text":voucher_text,
    }

    return ticket_data

