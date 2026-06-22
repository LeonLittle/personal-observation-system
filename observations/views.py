from django.shortcuts import render,redirect,get_object_or_404
from django.utils import timezone
from datetime import datetime,timedelta
from .models import Task,DailyRecord,Habit,HabitPeriod
from .ai_service import call_agnes_for_today_ticket
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

    today = datetime.now().date()

    week_start,week_end = get_current_week_range(today)

    week_summary = build_period_summary(
        user=request.user,
        start_date = week_start,
        end_date = week_end,
        expected_days=7
    )

    records = DailyRecord.objects.filter(
        user=request.user,
        date__range=[week_start,week_end]
    ).order_by("-date")

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
        done_count = tasks.filter(
            is_done=True
        ).count()

        #total_count列表
        history_items.append({
            "record": record,#一组DailyRecord对象
            "tasks": tasks,#相关daily_record_id列表
            "total_count": total_count,#daily_record_id数量
            "done_count": done_count,#daily_record_id里is_done为True的数量
        })

    context={
        "title":"每周观察",
        "week_summary":week_summary,
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

def extract_ai_ticket_field(ai_text, field_name):
    """
    从 AI 返回的小票文本里，提取某一个字段的内容。

    例如：
    field_name = "脑子"
    就从 AI 文本里找：
    脑子：
    后面的内容

    如果找不到，就返回空字符串。
    """

    # 如果 AI 没有返回内容，直接返回空字符串
    if not ai_text:
        return ""

    # 小票里可能出现的标题
    field_names = ["脑子", "身体", "情绪", "行动力", "结算", "盖章"]

    # 按行拆开，并去掉空行
    lines = []

    for line in ai_text.splitlines():
        clean_line = line.strip()

        if clean_line:
            lines.append(clean_line)

    collecting = False
    result_lines = []

    for line in lines:
        # 去掉 Markdown 加粗符号，避免 **脑子：** 识别失败
        clean_line = line.replace("**", "")

        # 统一中文冒号和英文冒号
        clean_line = clean_line.replace("：", ":")

        # 判断这一行是不是某个字段标题
        is_field_title = False

        for name in field_names:
            if clean_line.startswith(name + ":"):
                is_field_title = True

                # 如果当前已经在收集目标字段，
                # 遇到下一个字段标题，就停止收集
                if collecting and name != field_name:
                    return " ".join(result_lines).strip()

                # 如果这一行是目标字段，就开始收集
                if name == field_name:
                    collecting = True

                    # 处理“脑子：内容”这种写在同一行的情况
                    field_value = clean_line.split(":", 1)[1].strip()

                    if field_value:
                        result_lines.append(field_value)

                break

        # 如果这一行不是标题，并且已经开始收集目标字段
        # 就把这一行加入结果
        if collecting and not is_field_title:
            result_lines.append(line.replace("**", "").strip())

    return " ".join(result_lines).strip()

def get_safe_ai_text(ai_data, key, max_length):
    """
    从 AI 返回的数据里取字段。

    作用：
    1. 如果字段不存在，返回空字符串
    2. 如果字段太长，返回空字符串
    3. 避免 AI 输出过长内容撑坏页面
    """

    if not ai_data:
        return ""

    value = ai_data.get(key, "")

    if not value:
        return ""

    value = value.replace("：", ":")
    if ":" in value:
        value = value.split(":", 1)[1].strip()

    if len(value) > max_length:
        return ""

    return value




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
    elif total_count >0 and completion_rate>= 0.8:
        result_text="没有惊艳，但很可靠"
        voucher_text = "可靠的人生，往往没有太多特效"
        stamp_text="准许继续保持"
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

    if total_count == 0:
        completion_rate_text = "暂无行动"
    else:
        completion_rate_text = f"{round(completion_rate*100)}%"

    today_summary = {
        "mood": mood,
        "energy": energy,
        "summary": summary,
        "total_count": total_count,
        "done_count": done_count,
        "completion_rate_text": completion_rate_text,

        # 顺便把规则版分析结果也给 AI 参考
        # 这样 AI 更容易生成贴近当前状态的小票文案
        "rule_brain": brain_text,
        "rule_body": body_text,
        "rule_emotion": emotion_text,
        "rule_action": action_text,
    }

    # 调用 Agnes AI
    ai_data = call_agnes_for_today_ticket(today_summary)

    if ai_data:
        ai_brain = get_safe_ai_text(ai_data, "brain", 18)
        ai_body = get_safe_ai_text(ai_data, "body", 18)
        ai_emotion = get_safe_ai_text(ai_data, "emotion", 18)
        ai_action = get_safe_ai_text(ai_data, "action", 22)
        ai_result = get_safe_ai_text(ai_data, "result", 36)
        ai_voucher = get_safe_ai_text(ai_data, "voucher_text", 26)
        ai_stamp = get_safe_ai_text(ai_data, "stamp_text", 7)

        if ai_brain:
            ticket_data["brain"] = ai_brain

        if ai_body:
            ticket_data["body"] = ai_body

        if ai_emotion:
            ticket_data["emotion"] = ai_emotion

        if ai_action:
            ticket_data["action"] = ai_action

        if ai_result:
            ticket_data["result"] = ai_result

        if ai_voucher:
            ticket_data["voucher_text"]=ai_voucher

        if ai_stamp:
                ticket_data["stamp_text"] = ai_stamp
    

    return ticket_data

def get_current_week_range(today_date):
    """
    计算当前日期所在这一周的开始日期和结束日期

    当前项目规则:
    1.一周从星期一开始
    2.一周到星期日结束
    3.本周观察只统计本周一到周日的数据
    """

    weekday_number = today_date.weekday()
    #把日期转换为星期几然后返回数字给到weekday_number

    week_start = today_date - timedelta(days=weekday_number)
    

    week_end = week_start + timedelta(days=6)
    #

    return week_start,week_end

def build_period_summary(user,start_date,end_date,expected_days):
    """
    统计某一个时间段内的观察数据

    这个函数不是只给"本周"用
    以后本月/本年也可以复用
    """

    records = DailyRecord.objects.filter(
        user=user,
        date__range=[start_date,end_date]
    )
    #date字段是今天的日期
    #这里的records定义是找到当前周一到周日之间数据 __range包含开始和结束

    tasks = Task.objects.filter(
        daily_record__user=user,
        daily_record__date__range=[start_date,end_date],
        is_cancelled=False
    )
    #然后这里再获取这个周期的任务
    #这里daily_record__user=user 为什么要这么写 一个是为什么要加两个下划线然后user=user,后面的user是上面左边的user对吗
    #daily_record__date__range=[start_date,end_date]这里也不理解
    #is_cancelled=False没有取消的任务 这里为什么要这么写  取消的数据其实也可以加到数据统计里面,但是暂时先不考虑这个,但是需要给后期统计留上底座


    record_days = 0
    #记录天数起始为0

    for record in records:
        has_state=(
            record.mood.strip()
            or record.energy is not None
            or record.summary.strip()
        )
        #这里是循环records数据 找出energny不为空
        #.strip() 去掉字符串空格

        if has_state:
            record_days = record_days +1
        #如果has_state有数据 这个记录天数就加1

    total_actions = tasks.count()
        #统计任务数量

    done_actions = tasks.filter(
        is_done=True
    ).count()
        #统计已完成任务数量

        #这里开始分析任务数量  但是我还没打算怎么展示 所以这里不是重点
    if total_actions == 0:
        completion_rate = None
        completion_rate_text = "本周无任务"
    else:
        completion_rate = done_actions / total_actions
        completion_rate_text = f"{round(completion_rate * 100)}%"
        #已完成数量转换成百分比
        #round四舍五入

    energy_records = records.filter(
        energy__isnull=False
    )
        #这里是找精力值不是空的数据
        #__isnull是否为空

    energy_count = energy_records.count()
    #多少条精力记录

        #这里也是精力分析
    if energy_count == 0:
        energy_index = None
        energy_index_text = "未记录"
    else:
        total_energy = 0

        for record in energy_records:
            total_energy = total_energy + record.energy
        #循环每条精力记录 把值给到total_energy
            
        energy_index = total_energy / energy_count
        #平均精力分
        energy_index_text = f"{energy_index:.1f}"
        #这里是精力文本显示1位数  

        #这里是总的分析吗
    if total_actions == 0 and record_days == 0:
        summary_text = "这周没有留下记录"
    #如果这周任务为0

    elif energy_index is not None and energy_index <= 4:
        summary_text = "这周精力偏低"
    #如果这周精力小于等于4

    elif completion_rate is not None and completion_rate >= 0.8:
        summary_text = "这周任务推进得不错"
    #如果这周任务完成度在80%以上

    else:
        summary_text = "这周有推进,也有留白"
        #其他,就是有记录 精力在4以上 完成度在80%以下

    period_summary={
        "start_date":start_date, #开始日期
        "end_date":end_date,    #结束日期
        "start_text":start_date.strftime("%m月%d日"), #开始日期的文本格式我想是,但是不明白为什么要单独写着一条.strftime这个是什么意思 转换日期的吗
        "end_text":end_date.strftime("%m月%d日"), #结束日期 和开始同形态
        "record_days":record_days,#本周已记录天数的意思吗
        "expected_days":expected_days,#这条也是上面没有的 但这条是函数的参数,不知道是什么意思
        "total_actions":total_actions,#本周未取消任务
        "done_actions": done_actions,#本周完成的任务
        "completion_rate": completion_rate,#本周的任务完成度
        "completion_rate_text": completion_rate_text,#本周的任务完成度文本
        "energy_index": energy_index,#本周精力总数吗?
        "energy_index_text": energy_index_text,#本周精力总数文本
        "summary_text": summary_text,#这个就是分析的文案文本
    }

    return period_summary