from jieba import cut, load_userdict
from csv import writer
from bs4 import BeautifulSoup
from json import loads
from requests import get

def Search():
    # requests url 參數(keyword='搜尋關鍵字', page='頁數', area=6001001000(台北市)%2C6001002000(新北市), jobexp=1(一年以下), 1,3(一到三年), ro=1(全職)) & headers:User-Agent
    searchword = input('請輸入查詢關鍵字:')
    userAgent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36'
    headers = {'User-Agent':userAgent}

    pre_file = []
    skill_total_list = []
    specialty_set = set()
    for i in range(1,6): # 頁數選擇 每頁20個職缺
        url = f'https://www.104.com.tw/jobs/search/?ro=1&keyword={searchword}&page={i}&jobsource=tab_cs_to_job&asc=1&mode=s&kwop=7'
        res = get(url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
    # 定位一頁每個職缺的連結
        content = soup.select('a.js-job-link')
    # 抓取職缺連結的 ID
        for j in range(len(content)):
            content_ID = content[j]['href'].split('?')[0].split('/')[-1]
    # 抓取職缺連結 json 網址
            content_url = f'https://www.104.com.tw/job/ajax/content/{content_ID}'
    # headers 需帶指定 ID 的 Referer
            content_headers = {'Referer':f'https://www.104.com.tw/job/{content_ID}'}
            content_res = get(url = content_url, headers = content_headers)
    # 轉換網頁 json 為 Dict
            content_json = loads(content_res.text)
    # 找出 職稱=jobName, 公司=custName, 薪水=salary, 地區=addressRegion
            jobName = content_json['data']['header']['jobName']
            custName = content_json['data']['header']['custName']
            addressRegion = content_json['data']['jobDetail']['addressRegion']
            salary = content_json['data']['jobDetail']['salary']
    # 觀察網頁後，找到有可能有寫到技能的地方 / 工作內容=jobDescription / 擅長工具=specialty / 其他=other
    # 利用 擅長工具 = specialty 自動建立 jieba 辭典
            specialty = content_json['data']['condition']['specialty']
            if specialty:
                specialty_str = ''
                for a in specialty:
                    specialty_str += (a['description']+' ')
                    specialty_set.add(a['description'].replace(' ',''))
            else:
                specialty_str = ''
            other = content_json['data']['condition']['other']
            jobDescription = content_json['data']['jobDetail']['jobDescription']
    # 將全部合併為一個字串，並利用jieba斷詞找出是否提到關鍵技能字詞
            skill_total = specialty_str + jobDescription + other
            skill_total_list.append(skill_total.replace('\n','').replace(' ',''))
            pre_file.append([jobName,custName,addressRegion,salary])
        print(f'已查詢:{len(pre_file)}個職缺')

    with open(f'./{searchword}_skill.txt', 'w', encoding='utf-8') as f:
        for j in tuple(specialty_set):
            f.write(f'{j}\n')
        print(f'\n{searchword}_skill.txt 已創建完成')

    # 自定義辭典 利用集合交集找出是否含關鍵字
    load_userdict(f'./{searchword}_skill.txt')

    # 開啟輸出的 CSV 檔案
    with open(f'./104_{searchword}_search.csv', 'w', newline='', encoding='utf-8') as csvfile:
      # 建立 CSV 檔寫入器
        c_writer = writer(csvfile)
        c_writer.writerow(['職稱','公司名稱','地區','薪水','相關工具或技能'])
      # 寫入另外幾列資料
        print(f'開始寫入 104_{searchword}_search.csv')
        for x in range(len(pre_file)):
            skill_total_list[x] = ' '.join(cut(skill_total_list[x])).split()
            final_skill = str(specialty_set & set(skill_total_list[x])).lstrip('{').rstrip('}')
            final_skill = '無' if final_skill == 'set()' else final_skill
            pre_file[x].append(final_skill)
            c_writer.writerow(pre_file[x])
    print(f'104_{searchword}_search.csv 已成功儲存')
    
if __name__ == '__main__':
    Search()

