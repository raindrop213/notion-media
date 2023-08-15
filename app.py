import requests
from lxml import etree
import re
import sys


with open("reader-notionapi.txt", "r") as prf:
    page_id = ("".join(prf.readlines(1))).strip("\n")
    token = ("".join(prf.readlines(2))).strip("\n")

print("请输入豆瓣电影id：")

#page_id = ""
#token = ""

movid = str(input())
doubanurl = "https://movie.douban.com/subject/" + movid

# 请求头------------------------------------------------------------------------------------------------------------
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 '
                  'Safari/537.36'}

data = requests.get(doubanurl, headers=headers)
html = etree.HTML(data.text)

# 开始爬取网页上的数据-------------------------------------------------------------------------------------------------

# 中文片名
name = "".join(html.xpath("//head/title/text()"))
if name == ("" or "页面不存在"):  # 如果没有查到，则结束程序
    print("未查到电影信息")
    sys.exit()
name = (name.replace("(豆瓣)", "")).strip()  # 去掉电影名称中多余的字
print("搜索中……")

# 原文片名
native = "".join(html.xpath("//*[@id='mainpic']/a/img/@alt"))

# 海报
post = "".join(html.xpath("//*[@id='mainpic']/a/img/@src"))

# 导演
director = ",".join(html.xpath("//*[@id='info']/span[1]/span[2]/a/text()"))

# 编剧
writer = ",".join(html.xpath("//*[@id='info']/span[2]/span[2]/a/text()"))

# 演员
actor = ",".join(html.xpath("//meta[@property='video:actor']/@content"))

# 类型
genre = html.xpath("//span[./text()='类型:']/following::span[@property='v:genre']/text()")
genre += [" ", " ", " ", " "]  # 加上几个空格元素增加列表长度，避免提交的时候溢出

# 地区
region = ",".join(html.xpath("//span[./text()='制片国家/地区:']/following::text()[1]"))
region = region.split("/")  # 分割为列表
region = [i.strip() for i in region]  # 去除空格
region += [" ", " ", " ", " ", " ", " ", " ", " ", " ", " "]  # 增加列表长度

# 语言
language = ",".join(html.xpath("//span[./text()='语言:']/following::text()[1]"))
language = language.split("/")  # 分割为列表
language = [i.strip() for i in language]  # 去除空格
language += [" ", " ", " ", " "]  # 增加列表长度

# 时长
duration = ",".join(html.xpath("//span[@property='v:runtime']/text()"))

# imdb号
imdb = "".join(html.xpath("//span[./text()='IMDb:']/following::text()[1]"))
imdb = imdb.strip()

# 年份
year = "".join(html.xpath("//span[@class='year']/text()"))
year = re.findall(r'-?\d+\.?\d*', year)[0]  # 提取纯数字
year = int(year)  # 数据类型转换成整数

# 评分
rate = "".join(html.xpath("//*[@id='interest_sectl']/div[1]/div[2]/strong/text()"))
rate = rate.strip()
if rate == "":  # 判断有没有评分，如果以下几项数据全部为空
    raters = None
    rate = None
    r5, r4, r3, r2, r1 = [None, None, None, None, None]

else:
    # 评分人数
    raters = "".join(html.xpath("//*[@class='rating_people']/span/text()"))

    # 5-1星评分者比例
    rlist = \
        html.xpath("//*[@class='ratings-on-weight']/div[1]/span[2]/text()") + \
        html.xpath("//*[@class='ratings-on-weight']/div[2]/span[2]/text()") + \
        html.xpath("//*[@class='ratings-on-weight']/div[3]/span[2]/text()") + \
        html.xpath("//*[@class='ratings-on-weight']/div[4]/span[2]/text()") + \
        html.xpath("//*[@class='ratings-on-weight']/div[5]/span[2]/text()")

    rlist = [i.replace("%", "") for i in rlist]  # 去除百分号

    # 将评分比例数据分配到5个变量，便于整理
    r5, r4, r3, r2, r1 = rlist[0], rlist[1], rlist[2], rlist[3], rlist[4]

    # 修改数据类型
    rate = float(rate)
    raters = int(raters)
    r5 = float(r5) / 100
    r4 = float(r4) / 100
    r3 = float(r3) / 100
    r2 = float(r2) / 100
    r1 = float(r1) / 100

# 所在的榜单和排名
rank_li = "".join(html.xpath("//*[@class='top250-link']/a/text()"))
if rank_li != "":  # 如果有榜单，则获取它在榜单的名次
    rank_no = int(("".join(html.xpath("//*[@class='top250-no']/text()"))).replace("No.", ""))
else:  # 如果没有榜单，则空置
    rank_li = " "
    rank_no = None

print("已完成数据爬取：" + name + str(year))

# 开始向notion请求-----------------------------------------------------------------------------------------------------

url = "https://api.notion.com/v1/pages"

p = {"parent": {
    "type": "database_id",
    "database_id": page_id
},
    "properties": {
        "片名": {"title": [{"type": "text", "text": {"content": name}}]},
        "原名": {"rich_text": [{"type": "text", "text": {"content": native}}]},
        "评分": {"number": rate},
        "评分人数": {"number": raters},
        "上映年份": {"number": year},
        "IMDb": {"rich_text": [{"type": "text", "text": {"content": imdb}}]},
        "导演": {"rich_text": [{"type": "text", "text": {"content": director}}]},
        "主演": {"rich_text": [{"type": "text", "text": {"content": actor}}]},
        "类型": {"multi_select": [{"name": genre[0]}, {"name": genre[1]}, {"name": genre[2]}, {"name": genre[3]}]},
        "片长": {"rich_text": [{"type": "text", "text": {"content": duration}}]},
        "国家/地区": {
            "multi_select": [{"name": region[0]}, {"name": region[1]}, {"name": region[2]}, {"name": region[3]},
                             {"name": region[4]}, {"name": region[5]}, {"name": region[6]}, {"name": region[7]}]},
        "语言": {"multi_select": [{"name": language[0]}, {"name": language[1]}, {"name": language[2]}, {"name": language[3]}]},
        "榜单": {"select": {"name": rank_li}},
        "排名": {"number": rank_no},
        "编剧": {"rich_text": [{"type": "text", "text": {"content": writer}}]},
        "5星": {"number": r5},
        "4星": {"number": r4},
        "3星": {"number": r3},
        "2星": {"number": r2},
        "1星": {"number": r1},
        "封面": {"files": [{"name": "封面", "type": "external", "external": {"url": post}}]},
        "豆瓣": {"url": doubanurl}
    }
}
headers = {
    "Accept": "application/json",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
    "Authorization": "Bearer " + token
}

r = requests.post(url, json=p, headers=headers)

# 接受返回数据---------------------------------------------------------------------------------------------------------

if r.status_code == 200:
    print("导入Notion成功！")
else:
    print("导入Notion失败！")
    print(r.text)  # 返回讯息中可以看到错误提示

    # 用get请求来检测是不是连接上的错误
    print("输入000检查数据库通讯）")
    check = str(input())
    if check == "000":
        url = "https://api.notion.com/v1/databases/" + page_id
        headers = {
            "Accept": "application/json",
            "Notion-Version": "2022-06-28",
            "Authorization": "Bearer " + token
        }

        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            print("数据库通讯正常，请检查表格项目是否匹配")
        else:
            print("通讯错误，请检查integration机器人是否正确设置")

        print(r.text)
