import requests
from bs4 import BeautifulSoup
import re
import os
import csv
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.font_manager import FontProperties

# 设置字体
font = FontProperties(fname='sarasa-ui-sc-regular.ttf')

def url_get(url,filename):
    headers={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0'}
    response=requests.get(url,headers=headers)
    with open(filename,'w',encoding='utf-8') as f:
        f.write(response.text)

def movies_get():
    #下载猫眼电影排行页面
    if not os.path.exists('data/maoyan_top.html'):
        url_get("https://piaofang.maoyan.com/rankings/year?year=2023&limit=100&tab=1","data/maoyan_top.html")

    #根据豆瓣排行，找到十部热门电影
    #因豆瓣限制，请手动下载豆瓣电影排行页面
    movies=open('data/movies.html','r',encoding='utf-8').read()
    movies_soup=BeautifulSoup(movies,'html.parser')
    a_tags = movies_soup.find_all('a')
    filtered_a_tags = [a for a in a_tags if a.get('href', '').startswith('https://www.douban.com/doubanapp/dispatch?uri=/movie/')]

    #获取电影简介页面
    i=0
    for a in filtered_a_tags:
        url=a.get('href')
        match=re.search(r'/movie/(\d+)',url)
        if match:
            movie_id=match.group(1)
            movie_douban(movie_id)
            i+=1
        if i==10:
            break

def movie_douban(movie_id):
    new_url='https://movie.douban.com/subject/'+movie_id
    if not os.path.exists('data/movie'+str(i)+'.html') :
        url_get(new_url,'data/movie'+str(i)+'.html')

def boxoffice_get(title):
    # 获取对应的猫眼票房页
    with open("data/maoyan_top.html","r",encoding='utf-8') as f:
        maoyan_top=f.read()
    maoyan_top_soup=BeautifulSoup(maoyan_top,'html.parser')
    def contains_title(text):
        if text is None:
            return False
        return title[0:1] in text
    p_tag=maoyan_top_soup.find('p',string=contains_title)
    if p_tag is None:
        raise Exception("找不到对应的猫眼页面")
    data_com=p_tag.find_parent('ul')['data-com']
    data_com=re.search(r"'(.*?)'",data_com)
    url='https://piaofang.maoyan.com'+data_com.group(1)
    if not os.path.exists('data/'+title+'_maoyan.html'):
        url_get(url,'data/'+title+'_maoyan.html')
    with open('data/'+title+'_maoyan.html','r',encoding='utf-8') as f:
        maoyan=f.read()

    # 获取票房数据
    maoyan_soup=BeautifulSoup(maoyan,'html.parser')
    p_tag = maoyan_soup.find('p', string='累计票房 ')
    if p_tag is None:
        raise Exception(title+'数据获取失败。请检查'+'data/'+title+'_maoyan.html文件是否有异常')
    parent_div=p_tag.find_parent('div')
    span_tag=parent_div.find('span',class_="detail-num")
    total_boxoffice=float(span_tag.text)
    span_tag=parent_div.find('span',class_="detail-unit")
    if '亿' in span_tag.text:
        total_boxoffice=total_boxoffice*100000000
    elif '万' in span_tag.text:
        total_boxoffice=total_boxoffice*10000

    # 获取粉丝分布
    # 性别
    div_tag=maoyan_soup.find('div',class_="persona-line-item male")
    male_percentage_tag=div_tag.find('div',class_="persona-item-value")
    male_percentage=male_percentage_tag.text
    div_tag=maoyan_soup.find('div',class_="persona-line-item female")
    female_percentage=div_tag.find('div',class_="persona-item-value").text
    # 所在地
    div_tag=maoyan_soup.find('div',class_="persona-block hotarea")
    hotarea=div_tag.find('div',class_="persona-item-key",string='一线城市')
    hotarea=hotarea.parent
    hotarea=hotarea.find('div',class_="persona-item-value")
    hotarea_percentage=[hotarea.text]
    hotarea=div_tag.find('div',class_="persona-item-key",string='二线城市')
    hotarea=hotarea.parent
    hotarea=hotarea.find('div',class_="persona-item-value")
    hotarea_percentage.append(hotarea.text)
    hotarea=div_tag.find('div',class_="persona-item-key",string='三线城市')
    hotarea=hotarea.parent
    hotarea=hotarea.find('div',class_="persona-item-value")
    hotarea_percentage.append(hotarea.text)
    hotarea=div_tag.find('div',class_="persona-item-key",string='四线城市')
    hotarea=hotarea.parent
    hotarea=hotarea.find('div',class_="persona-item-value")
    hotarea_percentage.append(hotarea.text)

    # 写入数据文件
    if not os.path.exists('result/boxoffice.csv'):
        with open('result/boxoffice.csv','w',newline='',encoding='utf-8') as f:
            writer=csv.writer(f)
            writer.writerow(['电影','票房','男性比例','女性比例','一线城市比例','二线城市比例','三线城市比例','四线城市比例'])
    with open('result/boxoffice.csv','a',newline='',encoding='utf-8') as f:
        writer=csv.writer(f)
        writer.writerow([title,total_boxoffice,male_percentage,female_percentage,hotarea_percentage[0],hotarea_percentage[1],hotarea_percentage[2],hotarea_percentage[3]])

def analysis():
    # 删除旧的数据文件
    if os.path.exists('result/movie_data.csv'):
        os.remove('result/movie_data.csv')
    if os.path.exists('result/boxoffice.csv'):
        os.remove('result/boxoffice.csv')

    for i in range(10):
        with open('data/movie'+str(i)+'.html','r',encoding='utf-8') as f:
            movie=f.read()
            movie_soup=BeautifulSoup(movie,'html.parser')
            # 获取标题
            title=movie_soup.find('span',property='v:itemreviewed').text
            # 获取类型
            genres = movie_soup.find_all('span',property="v:genre")
            # 获取评分
            scores= movie_soup.find_all('span',class_="rating_per")
            # 获取简介
            summary=movie_soup.find_all('span',property="v:summary")
            # 获取猫眼票房数据
            boxoffice_get(title)
            # 写入数据文件
            if not os.path.exists('result/movie_data.csv'):
                with open('result/movie_data.csv','w',newline='',encoding='utf-8') as f:
                    writer=csv.writer(f)
                    writer.writerow(['电影','类型','评分','简介'])
            with open('result/movie_data.csv','a',newline='',encoding='utf-8') as f:
                writer=csv.writer(f)
                data_row=[]
                data_row.append(title)
                data_str=';'.join([genre.text for genre in genres])
                data_row.append(data_str)
                data_str=';'.join([score.text for score in scores])
                data_row.append(data_str)
                data_row.append(summary[0].text)
                writer.writerow(data_row)

def draw():
    # 绘制评分比例图
    df = pd.read_csv('result/movie_data.csv')
    for index, row in df.iterrows():
        ratings = row['评分'].split(';')
        ratings = [float(r.strip('%')) for r in ratings]
        ratings_new=[ratings[0]+ratings[1],ratings[2],ratings[3]+ratings[4]]
        # 绘制饼图
        plt.figure(index)
        plt.pie(ratings_new, labels=['正面','中性','负面'],autopct='%1.1f%%',textprops={'fontproperties':font})
        plt.title(row['电影'] + ' 评分分布',fontproperties=font)
        plt.savefig('result/'+row['电影']+'评分分布'+'.png')
        plt.close()

    # 绘制粉丝性别比例图
    df = pd.read_csv('result/boxoffice.csv')
    for index, row in df.iterrows():
        male_ratio = float(row['男性比例'].strip('%'))
        female_ratio = float(row['女性比例'].strip('%'))
        # 绘制饼图
        plt.figure(index)
        plt.pie([male_ratio, female_ratio], labels=['男性', '女性'], autopct='%1.1f%%', textprops={'fontproperties': font})
        plt.title(row['电影'] + ' 性别比例', fontproperties=font)
        plt.savefig('result/'+row['电影'] + '_性别比例.png')
        plt.close()

    # 绘制粉丝地域分布图
    df = pd.read_csv('result/boxoffice.csv')
    for index, row in df.iterrows():
        city1_ratio = float(row['一线城市比例'].strip('%'))
        city2_ratio = float(row['二线城市比例'].strip('%'))
        city3_ratio = float(row['三线城市比例'].strip('%'))
        city4_ratio = float(row['四线城市比例'].strip('%'))
        # 绘制饼图
        plt.figure(index)
        plt.pie([city1_ratio, city2_ratio, city3_ratio, city4_ratio], labels=['一线城市', '二线城市', '三线城市', '四线城市'], autopct='%1.1f%%', textprops={'fontproperties': font})
        plt.title(row['电影'] + ' 城市级别比例', fontproperties=font)
        plt.savefig('result/'+row['电影'] + '_城市级别比例.png')
        plt.close()

    # 绘制票房柱状图
    df = pd.read_csv('result/boxoffice.csv')
    # 对'票房'列进行排序
    df_sorted = df.sort_values('票房', ascending=False)
    # 绘制柱状图
    vertical_names = ['\n'.join(name.split(' ')[0]) for name in df_sorted['电影']]
    plt.figure(figsize=(13, 6))
    bars=plt.bar(df_sorted['电影'], df_sorted['票房'])
    plt.xlabel('电影', fontproperties=font)
    plt.ylabel('票房', fontproperties=font)
    plt.title('电影票房', fontproperties=font)
    plt.xticks(range(len(df_sorted)), vertical_names, fontproperties=font)
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x(), yval, int(yval), va='bottom')
    plt.tight_layout()
    plt.savefig('result/电影票房.png')
    plt.close()

def main():
    #创建文件夹
    if not os.path.exists('data'):
        os.mkdir('data')
    if not os.path.exists('result'):
        os.mkdir('result')
    #爬虫获取影片相关数据
    movies_get()
    #分析数据
    analysis()
    #绘制结论图
    draw()

if __name__=='__main__':
    main()