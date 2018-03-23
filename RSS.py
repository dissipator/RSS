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

def html2md(data,feed_name=None,rooturl=None):
    # data = Tomd(data).markdown
    # data = u'''<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8"></head><body>%s </body></html>''' % data

    soup = BeautifulSoup(data, 'lxml')#,'html.parser',from_encoding='utf-8'
    head = str(soup.head)
    content = soup.find(id='content')
    if content == None:
         content = soup.body


    clears = ['h4',]
    for c in clears:
        All = content.findAll(c)
        for a in All:
            try:
                a.find('a').decompose()
            except Exception as e:
                pass

            try:
                a['class'].clear()
            except Exception as e:
                pass

    dels = ['comments','nav-single']
    for tag in dels:
        ts = content.findAll(id=tag)
        for t in ts:
            if t !=None:
                t.decompose()

    imgs = content.findAll('img')
    for img in imgs:
        try:
            parsed = urllib.parse.urlparse(img['src'])
            if parsed.scheme=='' :
                img['src']=rooturl+img['src']
        except :
            pass

    filename = './%s.md' % feed_name
    data = u'''<!DOCTYPE html><html lang="zh-CN">%s<body>%s </body></html>''' % (head,str(content))
    data = Tomd(data).markdown
    with open(filename,'w') as file_writer:
            file_writer.write(data)
    file_writer.close()

    return data

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
    text = '\nHi there is a new %s article :%s . \nYou can read it here %s' % (feed_name, article_title, article_url)
    # http://blinky.nemui.org/shot?http://www.baidu.com
    print(text)
    mkdir("./"+feed_name)
    article_title=article_title.strip()# 去除首位空格
    article_title=article_title.rstrip("\\")# 去除尾部 \ 符号
    article_title=''.join(article_title.split('/'))
    parsed = urllib.parse.urlparse(article_url)
    rooturl = parsed.scheme+'://'+parsed.netloc

    with request.urlopen(article_url) as f:
        if(f.status==200):
            data = f.read()
            text = html2md(data.decode('utf-8'),feed_name+"/"+article_title,rooturl)
    try:
        smtp_server = smtplib.SMTP('smtp.qq.com', 587)
        smtp_server.ehlo()
        smtp_server.starttls()
        smtp_server.login('dissipator_520@qq.com', 'xxxxxxxxxxxxxx')
        msg = MIMEText(text)
        msg['Subject'] = 'New %s Article Available' % feed_name
        msg['From'] = 'dissipator_520@qq.com'
        msg['To'] = 'dissipator_520@qq.com'
        smtp_server.send_message(msg)
        smtp_server.quit()
    except Exception as e:
        print(e)

def read_article_feed():
    """ Get articles from RSS feed """
    feeds = {
                'appinn':'http://feeds.appinn.com/appinns/',
                'linux':'https://linux.cn/rss.xml',
                'niume':'https://segmentfault.com/feeds/blog/niume',
                'yangshengliang':'https://www.yangshengliang.com/feed',
                'ruanyifeng':'http://www.ruanyifeng.com/blog/atom.xml',
            }
    for fname in feeds:
        feed = feedparser.parse(feeds[fname])

        #print(feed)
        for article in feed['entries']:
            # send_notification(fname, article['title'], article['link'])
            if article_is_not_db(article['title'], article['published']):
                send_notification(fname, article['title'], article['link'])
                try:
                    add_article_to_db(article['title'], article['published'])
                except Exception as e:
                    add_article_to_db(article['title'], article["updated"])
                else:
                    print(article)

if __name__ == '__main__':
    read_article_feed()
    db_connection.close()
