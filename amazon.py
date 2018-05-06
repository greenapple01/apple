import numpy
import matplotlib.pyplot
import time
from lxml import etree
import requests
from myPymysql import DBHelper
import random
start = "https://www.amazon.com/s/ref=nb_sb_noss?url=search-alias%3Daps&field-keywords=skirt&rh=i%3Aaps%2Ck%3Askirt"

start = 'https://www.amazon.com/s/ref=sr_pg_{}?fst=p90x%3A1%2Cas%3Aon&rh=k%3Askirt%2Cn%3A7141123011%2Cn%3A7147440011%2Cn%3A1040660%2Cn%3A1045022&page={}&keywords=skirt&ie=UTF8&qid=1525325330'

start = 'https://www.amazon.com/s/ref=sr_pg_{}?page={}&keywords=skirt'# accept:text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
# accept-encoding:gzip, deflate, sdch, br
# accept-language:zh-CN,zh;q=0.8

# start = "https://www.amazon.com/s/ref=sr_pg_3/140-4081174-0214411?page={}&keywords=skirt"
user_agent = "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:58.0) Gecko/20100101 Firefox/58.0"
headers = {'User-Agent':user_agent,
            'accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'accept-language':'zh-CN,zh;q=0.8',
            'accept-encoding':'gzip, deflate, sdch, br'}
# 获取页面信息
def get_html(url):
    headers = {'Referer':url,'User-Agent':user_agent}
    try:
        r = requests.get(url,headers=headers)
        r.status_code
    except Exception as e:
        print(e)
    else:
        r.encoding = r.apparent_encoding
        return  r.text
def parse(html):
   node = []
   html = etree.HTML(html)
   # class ="pagnDisabled"
   results = html.xpath(
      '//a[@class="a-link-normal s-access-detail-page  s-color-twister-title-link a-text-normal"]/@href')
   print('results-------------', len(results))
   for i in results:
      i = i.strip()
      if 'https' != i[:5]:
         i = 'https://www.amazon.com' + i
      node.append(i)
   return node

def parse_goods(html):
    dbhelper = DBHelper()
    item = {}
    html = etree.HTML(html)
    item['ProductTitle'],item['SellersRank'], item['EvaluationNum'], item['AnswerNum'], item['ShelfTime'] ,item['ReviewList']= \
        None,None, None, None, None,[]
    max_num = None
    item['star']=None
    star = html.xpath('//span[@id="acrPopover"]//span[@class="a-icon-alt"]/text()')
    if star:
        item['star']=star[0].strip()
    productTitle = html.xpath("//span[@id='productTitle']/text()")
    if productTitle:
        item['ProductTitle'] = productTitle[0].strip()
    price = html.xpath("//span[@id='priceblock_ourprice']/text()")
    if price:
        item['Price'] = price[0].strip()
    else:
        return
    sellersrank = html.xpath("//li[@id='SalesRank']/text()")
    if len(sellersrank) >= 2:
         seller = sellersrank[1].strip()[:-1]
         seller = seller.split(' in')
         item['SellersRank'] =''.join(seller[0][1:].split(','))
    # print(html.xpath("//span[@id='acrCustomerReviewText']/text()"))
    else:
        return

    evaluationnum = html.xpath("//span[@id='acrCustomerReviewText']/text()")
    if evaluationnum:
        item['EvaluationNum'] = evaluationnum[0].strip()
    shelftime = html.xpath('//div[@id="detailBullets_feature_div"]//li[last()]/span/span[last()]/text()')

    if shelftime:
        item['ShelfTime'] = shelftime[0].strip()

    answer = html.xpath("//a[@id='askATFLink']/span/text()")

    if answer:
        item['AnswerNum'] = html.xpath("//a[@id='askATFLink']/span/text()")[0].strip()
    print(item)
    if item['SellersRank'] and item['EvaluationNum']  and \
            item['ShelfTime'] and item['star']:
        sql = 'insert into amazon01(Rank, ProductTitle,reviewNumber,Price,AnswerNum,ShelfTime,star)\
            values(%s,%s,%s,%s,%s,%s,%s)'
        params = (item['SellersRank'],item['ProductTitle'],item['EvaluationNum'],
            item['Price'],item['AnswerNum'],item['ShelfTime'],item['star'])
        dbhelper.execute(sql,params)
        print(item['SellersRank']+':插入成功')
    else:
      return
    

    if evaluationnum:
        item['EvaluationNum'] = evaluationnum[0].strip()
        # review_url = html.xpath('//a[@id="dp-summary-see-all-reviews"]/@href')
        # if review_url:
        #     review_start = 'https://www.amazon.com' + review_url[0]
        #     # print(review_start)
        #     answer = get_html(review_start)
        #     answer = etree.HTML(answer)
        #     page = answer.xpath('//li[@class="page-button"]')
        #     if page:
        #         max_number = 1
        #         max_num = page[-1].xpath("a/text()")
        #         if max_num: 
        #             max_number = int(max_num[0])
        #             # M_Rank primary key, review_start ,max_number
        #             print(type(max_number),max_number)
        #             sql = 'insert into middle(M_Rank,start,number) values(%s,%s,%r)'
        #             params = (item['SellersRank'],review_start,max_number)
        #             dbhelper.execute(sql,params) 

                #     print(str(item['SellersRank'])+'middle url 插入成功。')
                # else:
                #     print(str(item['SellersRank'])+'middle url没有插入。')
    # 插入数据库    
# {'SellersRank': '#27,860 in Clothing, Shoes & Jewelry ',
#  'EvaluationNum': '78 customer reviews',
#  'AnswerNum': '15 answered questions',
#  'ShelfTime': 'June 23, 2017',
#  'ProductTitle': "Janmid Women's High Waisted A Line Street Skirt Skater Pleated Full Midi Skirt",
# 'Price': '$16.99',
def parse_review(url):
    star, title, body,stblist=None,None,None,[]
    html = get_html(url)
    html = etree.HTML(html)
    answers = html.xpath('//div[@id="cm_cr-review_list"]/div[@id]/div[@class="a-section celwidget"]')
    for answer in answers:
        star = answer.xpath('./div[@class="a-row"]/a[@class="a-link-normal"]/@title')
        # if star:
            # print(star[0])
        title = answer.xpath('./div[@class="a-row"]/a[@data-hook="review-title"]/text()')
        # if title: 
            # print(title[0])
        body = answer.xpath('./div[@class="a-row review-data"]/span/text()')
        # if body:
        #     print(body[0])
        if body and title and star:
            stblist.append({'star':star[0],'title':title[0],'body':body[0]})
    return stblist
if __name__ =="__main__":
    for i in range(1,99):
        print('正在查询'+str(i) + '页')
        url = start.format(i,i)
        print(url)
        html =get_html(url)
        goodslist = parse(html)
        for goods_url in goodslist:
           goods_html = get_html(goods_url)
           parse_goods(goods_html)
           time.sleep(random.randint(3,6))

        print()
        time.sleep(28)

