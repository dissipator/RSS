#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sqlite3
import smtplib
from email.mime.text import MIMEText
import urllib
from urllib import request 
from bs4 import BeautifulSoup
from tomd import Tomd

import feedparser

db_connection = sqlite3.connect('./magazine_rss.sqlite')
db = db_connection.cursor()
db.execute(' CREATE TABLE IF NOT EXISTS magazine (title TEXT, date TEXT)')

def article_is_not_db(article_title, article_date):
    """ Check if a given pair of article title and date
    is in the database.
    Args:
        article_title (str): The title of an article
        article_date  (str): The publication date of an article
    Return:
        True if the article is not in the database
        False if the article is already present in the database
    """
    db.execute("SELECT * from magazine WHERE title=? AND date=?", (article_title, article_date))
    if not db.fetchall():
        return True
    else:
        return False

def add_article_to_db(article_title, article_date):
    """ Add a new article title and date to the database
    Args:
        article_title (str): The title of an article
        article_date (str): The publication date of an article
    """
    db.execute("INSERT INTO magazine VALUES (?,?)", (article_title, article_date))
    db_connection.commit()

def convert(feed_name, papers):
    str = ''
    filename = './%s.md' % feed_name
    with open(filename,'w') as file_writer:
        for p in papers:
            if p['tag']=='text':
                str += p['content'].replace('c_start','**').replace('c_end','**')  #这个是替换颜色,使用加粗
                pass
            elif p['tag']=='code':
                str += '```'+'\r\n'+p['content']+'\r\n'+'```'  #这个是代码框的添加

            else:
                #![](//upload-images.jianshu.io/upload_images/1823443-7c4c920514b8f0cf.jpg?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)#这个是图片链接的转化
                str += '![](%s)'%(p['content'])
                str += '\r\n'+str+'\r\n'
            file_writer.write(str)
            file_writer.write('\r\n')
 
    file_writer.close()
    return str



def html2md(data,article_url=None):
    papers = []
    soup = BeautifulSoup(data, 'html.parser')#,'html.parser',from_encoding='utf-8'
    pres = soup.findAll('pre')
    for pre in pres:
        pre.name ='p' 
        pre['code']='yes'

    ps = soup.findAll('p')
    for p in ps:
        img = p.img
        if img !=None:
            parsed = urllib.parse.urlparse(img['src'])
            if parsed.scheme=='' :
                img['src']=article_url+img['src']
            content={'tag':'img','content':img['src']}
            papers.append(content)
        if p.get('code')=='yes':
            # content={'tag':'code','content':p.text.replace('&nbsp:','').strip()}
            content={'tag':'code','content':p.text.replace(' :','').strip()}
            papers.append(content)

        elif p.span != None:
                spans = p.findAll('span')
                for span in spans:
                    print('span',span.get('style'))
                    if span.string!=None:
                        span.name = 'color'
                        if span.string!=None:
                            span.string = 'c_start'+span.string+'c_end'
                    # if span.get('style').findAll('color')!=-1:
                    #     # del span['style']
                    #     span.name='color'
                    #     if span.string!=None:
                    #         span.string = 'c_start'+span.string+'c_end' 
        links = p.findAll('a')
        for link in links:
            if link.string!=None:
                link.string = '['+link.string+']'+'('+link.string+')'
        
            content={'tag':'text','content':p.text.replace('&nbsp:','').strip()}
            papers.append(content)
    return papers
def mkdir(path):

    import os
    path=path.strip()# 去除首位空格
    path=path.rstrip("\\")# 去除尾部 \ 符号
    isExists=os.path.exists(path)

    if not isExists:
        os.makedirs(path) 
        return True
    else:
        return False

def send_notification(feed_name, article_title, article_url):
    """ Add a new article title and date to the database

    Args:
        article_title (str): The title of an article
        article_url (str): The url to access the article
    """

    smtp_server = smtplib.SMTP('smtp.qq.com', 587)
    smtp_server.ehlo()
    smtp_server.starttls()
    smtp_server.login('xxxxxxxxx@qq.com', 'xxxxxxxxxx')
    text = '\nHi there is a new %s article :%s . \nYou can read it here %s' % (feed_name, article_title, article_url)
    print(text)
    # http://blinky.nemui.org/shot?http://www.baidu.com
    mkdir("./"+feed_name)
    article_title=article_title.strip()# 去除首位空格
    article_title=article_title.rstrip("\\")# 去除尾部 \ 符号
    parsed = urllib.parse.urlparse(article_url)
    rooturl = parsed.scheme+'://'+parsed.netloc

    with request.urlopen(article_url) as f:
        if(f.status==200):
            data = f.read()
            try:
                text = convert(feed_name+"/"+article_title,html2md(data.decode('utf-8'),rooturl))
                # text = Tomd(text).markdown
                print('Use : html2md')
            except Exception as e:
                text = Tomd(data.decode('utf-8')).markdown
                print('Use : Tomd')
            else:
                pass

    msg = MIMEText(text)
    msg['Subject'] = 'New %s Article Available' % feed_name
    msg['From'] = 'xxxxxxxxx@qq.com'
    msg['To'] = 'xxxxxxxxx@qq.com'
    smtp_server.send_message(msg)
    smtp_server.quit()

def read_article_feed():
    """ Get articles from RSS feed """
    feeds = {
                'appinn':'http://feeds.appinn.com/appinns/',
                'linux':'https://linux.cn/rss.xml',
                'niume':'https://segmentfault.com/feeds/blog/niume',
                'yangshengliang':'https://www.yangshengliang.com/feed',
                'ruanyifeng':'http://www.ruanyifeng.com/feed.html',
            }
    for fname in feeds:
        feed = feedparser.parse(feeds[fname])

        #print(feed)
        for article in feed['entries']:
            send_notification(fname, article['title'], article['link'])
            if article_is_not_db(article['title'], article['published']):
                send_notification(fname, article['title'], article['link'])
                add_article_to_db(article['title'], article['published'])

if __name__ == '__main__':
    read_article_feed()
    db_connection.close()