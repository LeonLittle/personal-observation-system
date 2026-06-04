from django.shortcuts import render,redirect,get_object_or_404
from django.utils import timezone
from datetime import datetime
from .models import Task,DailyRecord
#1. render作用:把数据交给HTML页面,然后生成网页返回给浏览器 意思:生成网页
#2. redirect作用:跳转到另一个页面  意思:保存完任务后,重新回到首页 
#3. get_object_or_404作用:代码安全维护  意思:去数据库找某条数据;找不到就显示404错误页
#4. from datetime import datetime是在python里的datetime时间管理模块 导入datetime日期+时间工具
#5. shortcuts是django快捷工具箱
from django.contrib.auth.decorators import login_required

@login_required
def home(request):
    """ 首页视图函数。

    这一版做 6 件事：
    1. 获取今天日期
    2. 获取或创建今天的状态记录
    3. 处理新增任务
    4. 处理今日状态保存
    5. 从数据库读取所有任务
    6. 把数据交给 home.html 页面显示
    7. request获取浏览器所有信息
    8. get_or_create查询or创建 是否刚创建True/Flash,所以必须要有两个变量来接收
    """
    
    today = datetime.now()
    #命名了一个today变量来获取今日日期+时间

    today_record,created = DailyRecord.objects.get_or_create(
        user=request.user,
        date=today.date()
    )
    #today_record接收DailyRecord里的符合today.date日期的数据 
    #get_or_create如果有数据直接给today同时返回一个flash给created
    #get_or_create如果没有数据就新建一个符合today.date日期的数据同时返回一个True给created


    if request.method == "POST":
        #method 浏览器的请求方式GET/POST
        #判断用户是否提交数据

        form_type = request.POST.get("form_type")
        #获取浏览器里提交的("form_type")数据给到变量form_type

        if form_type == "task":
            #判断变量form_type里的数据是不是task

            title = request.POST.get("title")
            #获取浏览器提交的("title")数据给到变量title

            if title:
                Task.objects.create(
                    title=title,
                    daily_record=today_record,
                )
            #如果变量title里有数据 create就在Task类里添加一条数据
            #并把变量里的title数据 保存到Task类里的title字段
            #daily_record=today_record
            
            #刷新home页面
            return redirect("home")



    # tasks = Task.objects.filter(
    #     daily_record=today_record
    # ).order_by("-created_at")
    # #created_at是Task里创建时间字段
    # #("-created_at")-倒序
    # #.order_by() 按某个字段排序
    # #daily_record=today_record 把这条任务绑定到今天这条日期上

    # total_count = tasks.count()
    # #.count()统计数量
    # #.count()统计tasks里有多少数量 保存到total_count里

    # done_count = tasks.filter(is_done=True).count()
    # #.filter() 筛选
    # #tasks.filter(is_done=True)筛选(is_done=True)的数据
    # #筛选完后.count()统计数量
    # #统计有多少已完成的任务 保存到done_count里
    # 今天全部任务

    tasks = Task.objects.filter(
        daily_record=today_record
    ).order_by("-created_at")

    # 今天未完成任务
    undone_tasks = tasks.filter(is_done=False)

    # 今天已完成任务
    done_tasks = tasks.filter(is_done=True)

    # 首页只显示前 2 条未完成任务
    next_tasks = undone_tasks.filter(
        show_on_home=True
    )

    # 数量统计
    undone_count = undone_tasks.count()
    done_count = done_tasks.count()
    total_count = tasks.count()

    context = {
        #左边是html里使用的名字
        #Python里的真实变量
        #.strftime()把日期时间05/31格式化成指定名字05月/31日
        #today.weekday()
        #.weekday()计算星期几,并返回对应编号
        "title":"个人观察助手",
        "date_text" : today.strftime("%m月%d日"),
        "weekday_text":["星期一","星期二","星期三","星期四","星期五","星期六","星期日"][today.weekday()],
        "tasks": tasks,
        "next_tasks": next_tasks,
        "undone_count": undone_count,
        "done_count": done_count,
        "total_count": total_count,
        "today_record":today_record,
    }

    return render(request,"observations/home.html",context)
    #把context的数据交给"observations/home.html" render生成到最终页面

@login_required
def task_list_view(request):
    """
    今日任务页视图函数

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

    if request.method == "POST":
        title = request.POST.get("title")

    # 获取用户填写的计划开始时间和计划结束时间。
    # 如果用户没有填写，就用 None，表示这个任务没有设置时间。
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
    
    undone_tasks = Task.objects.filter(
        daily_record=today_record,
        is_done=False
    ).order_by("-created_at")

    done_tasks = Task.objects.filter(
        daily_record=today_record,
        is_done=True
    ).order_by("-created_at")

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

        energy = request.POST.get("energy")

        today_record.summary = request.POST.get("summary","")

        if energy:
            today_record.energy = int(energy)
        else:
            today_record.energy = None

        today_record.save()
        #保存

        return redirect("home")
        #保存后回到首页

    context = {
        "title":"今日状态记录",
        "date_text" : today.strftime("%m月%d日"),
        "weekday_text":["星期一","星期二","星期三","星期四","星期五","星期六","星期日"][today.weekday()],
        "today_record":today_record,
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

    records = DailyRecord.objects.filter(
        user=request.user
    ).order_by("-date")[:7]

    history_items = []

    for record in records:
        tasks=record.tasks.all().order_by("-created_at")

        total_count= tasks.count()

        done_count = tasks.filter(is_done=True).count()

        history_items.append({
            "record": record,
            "tasks": tasks,
            "total_count": total_count,
            "done_count": done_count,
        })

    context={
        "title":"最近观察",
        "history_items":history_items,
    }

    return render(request,"observations/history.html",context)

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
    task = get_object_or_404(Task, id=task_id)

    # 删除这条任务
    task.delete()

    # 删除后回到今日任务页，而不是首页
    return redirect("task_list")

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