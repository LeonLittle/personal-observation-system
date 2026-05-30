
from django.shortcuts import render,redirect,get_object_or_404
from datetime import datetime

from .models import Task,DailyRecord


# 定义home视图函数，处理首页的HTTP请求
def home(request):
    """ 首页视图函数。

    这一版做 6 件事：
    1. 获取今天日期
    2. 获取或创建今天的状态记录
    3. 处理新增任务
    4. 处理今日状态保存
    5. 从数据库读取所有任务
    6. 把数据交给 home.html 页面显示
    """
    
    today = datetime.now()

    #获取或创建今天的DailyRecord
    #如果今天已经有记录,就拿出来
    #如果今天还没有记录,就自动创建一条
    today_record,created = DailyRecord.objects.get_or_create(
        date=today.date()
    )

    #如果用户是通过表单提交任务,也就是点击了"添加任务"按钮
    if request.method == "POST":
        #从网页表里取出name=from_type 输入的内容
        form_type = request.POST.get("form_type")

        if form_type == "task":
            #从网页表里取出name="title"输入的内容
            title = request.POST.get("title")

        #如果用户真的输入了内容,才创建任务 
            if title:
                Task.objects.create(title=title)

            return redirect("home")

        if form_type =="daily_record":
            today_record.mood = request.POST.get("mood","")
            energy = request.POST.get("energy")
            today_record.summary = request.POST.get("summary","")

        if energy:
            today_record.energy = int(energy)
        
            today_record.save()

            return redirect("home")

    tasks = Task.objects.all().order_by("-created_at")

    total_count = tasks.count()
    done_count = tasks.filter(is_done=True).count()


    # 创建context字典，用于存储传递给模板的数据
    context = {

        "title":"个人观察助手",
        "date_text" : today.strftime("%m月%d日"),
        "weekday_text":["星期一","星期二","星期三","星期四","星期五","星期六","星期日"][today.weekday()],
        "tasks":tasks,
        "total_count":total_count,
        "done_count":done_count,
        "today_record":today_record,
    }

    # 返回渲染后的home.html模板，并将context数据传递给模板使用
    return render(request,"observations/home.html",context)


def toggle_task(request,task_id):
    """
    切换任务完成状态

    作用：
    1. 根据 task_id 找到对应任务
    2. 如果任务未完成,就改成已完成
    3. 如果任务已完成,就恢复成未完成
    4.保存到数据库
    5. 回到首页
    """

    #根据任务id从数据库里找到这条任务
    task = get_object_or_404(Task,id=task_id)

    #把当前状态反过来
    #原来是False,就变成True
    #原来是True,就变成False
    task.is_done = not task.is_done

    #保存修改
    task.save()

    #回到首页
    return redirect("home")

def delete_task(request,task_id):
    """
    删除任务视图函数

    作用:
    1,根据task_id找到对应任务
    2,删除这条任务
    3,回到首页
    """

    #根据任务id从出数据库里找到这条任务
    task = get_object_or_404(Task,id=task_id)

    #删除这条任务
    task.delete()
    
    #删除后回到首页
    return redirect("home")


