# 导入Django的render函数，用于渲染HTML模板
from django.shortcuts import render
# 导入datetime模块，用于处理日期和时间
from datetime import datetime

# 定义home视图函数，处理首页的HTTP请求
def home(request):
    """ 1. 获取今天日期
        2. 准备页面要显示的数据
        3. 把数据交给 home.html 页面
    """
    # 获取当前日期和时间
    today = datetime.now()

    # 创建context字典，用于存储传递给模板的数据
    context = {
        # 设置页面标题为"个人观察助手"
        "title":"个人观察助手",
        # 将日期格式化为"月日"的字符串形式，例如"05月29日"
        "date_text" : today.strftime("%m月%d日"),
        # 根据星期几的数值（0-6）从列表中取对应的中文星期名称
        "weekday_text":["星期一","星期二","星期三","星期四","星期五","星期六","星期日"][today.weekday()],
    }

    # 返回渲染后的home.html模板，并将context数据传递给模板使用
    return render(request,"observations/home.html",context)

