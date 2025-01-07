from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from openai import OpenAI

import time
from config import EXAMPLE_FILE_PATH, TABS

# 自動生成摘要
def auto_summary(plain_text, tab_button, h2_titles, all_titles):

    with open(EXAMPLE_FILE_PATH, 'r', encoding='utf-8') as file:
        output_sample = file.read()

    client = OpenAI()

    # 台電最新公告
    lastest_announcement_prompt = ""
    if any("台電最新公告" in title for title in h2_titles):
        lastest_announcement_prompt += "其中「台電最新公告」若有多項，請列點說明。"

    # 本週主題分析: 請 GPT 幫忙過濾掉無關的文字
    week_analysis_prompt = ""
    week_analysis = next(
        (title for title in h2_titles if "本週主題分析" in title),
        None
    )
    if week_analysis:
        week_analysis_prompt += f"其中「本週主題分析」需要提到即時、補充"
        week_analysis_prompt += (
            f"，除此之外，還要包含 {'、'.join(all_titles[week_analysis])}" 
            if len(all_titles[week_analysis]) != 0 else ""
        )

    # 市場最新動態
    lastest_market_prompt = ""
    if any("市場最新動態" in title for title in h2_titles):
        if len(tab_button)==0:
            index = next(i for i, title in enumerate(h2_titles) if "市場最新動態" in title)
            h2_titles.pop(index)
        else:
            lastest_announcement_prompt += f"""
            其中「市場最新動態」還須包含{len(tab_button)}個子標題{'、'.join(tab_button)}，每個子標題需換行，且需包含以下內容：
            「平均結清價格(required)」、「平均結清價格較上週上升or下滑多少(required)」、「本週參與容量(required)」、
            「參與容量較上週上升or下滑多少(required)」、「來自哪幾個廠商(optional)、對應的廠商名稱（required）、對應增加/減少的MW(optional)」，請用一句話描述，不需要分段。
            """

    # 台電電力供需資料
    electric_info = ""
    if any("台電電力供需資料" in title for title in h2_titles):
        electric_info += f"""
        其中「台電電力供需資料」一定會提到「再生能源占比(required)」、「滲透率(required)」。
        """

    # 下週預告
    next_week = ""
    if any("下週預告" in title for title in h2_titles):
        next_week += f"""
        其中「下週預告」只需要過濾掉不相關的文字，其餘直接複製貼上！
        """

    messages = []
    messages.append({
        "role": "system",
        "content": f"""
        您是一個直到獲取所有資訊後，才摘要重點的助手，會按照期望的輸出格式給予回覆。

        {lastest_announcement_prompt}

        {week_analysis_prompt}
        
        {lastest_market_prompt}
        
        {electric_info}
        
        {next_week}

        輸出的標題必須包含{'、'.join(h2_titles)}。
        
        期望的輸出格式如下（它是過去的歷史資料，這只是給你參考輸出的格式，並非實際的數據，請不要參考其中的數據內容）:
        {output_sample}。

        而實際的數據如下:
        {plain_text}。
        """
        })
    
    response = client.chat.completions.create(
        model="gpt-4o", 
        messages=messages,
        temperature=0
    )
    final_response = response.choices[0].message.content

    return final_response
    # with open(f"output/{datetime.today().strftime('%Y-%m-%d')}.mdx", 'w', encoding='utf-8') as file:
    #     file.write(final_response)

def auto_get_text(url):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # 啟用無頭模式
    options.add_argument("--no-sandbox")  # 避免沙盒問題（推薦在 Linux 系統上加上這個參數）
    options.add_argument("--disable-dev-shm-usage")  # 避免資源限制錯誤

    # 自動下載並使用對應版本的 ChromeDriver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.get(url)

    plain_text = "📈 市場最新動態"
    tab = []

    for tab_name, tab_value in TABS.items():
        # 點擊按鈕
        try:
            button = driver.find_element(By.CSS_SELECTOR, f'[data-service-tab-button="{tab_value}"]')
            if button:
                button.click()
                time.sleep(1)  # 等待內容加載

                # 獲取顯示的內容
                content_element = driver.find_element(By.CSS_SELECTOR, f'[data-service-tab-content="{tab_value}"]')
                content = content_element.text.strip()  # 提取文字內容
                plain_text += content

                if tab_name=="dReg/sReg":
                    tab.append("調頻備轉")
                elif tab_name=="光儲合一":
                    continue
                else:
                    tab.append(tab_name)
        except Exception as e:
            print(f"無法處理 {tab_name}，可能內容不存在或未顯示: {e}")
            continue

    # 移除本週摘要
    need_remove = driver.find_element(By.XPATH, '//*[@id="本週摘要"]')
    driver.execute_script("arguments[0].remove();", need_remove)
    need_remove = driver.find_element(By.XPATH, '//*[@id="__next"]/div/div[2]/article/div[3]')
    driver.execute_script("arguments[0].remove();", need_remove)

    element = driver.find_element(By.CSS_SELECTOR, "#__next > div > div.relative.grid.justify-center > article")
    elements = element.find_elements(By.CSS_SELECTOR, 'h2, p, ul')

    for e in elements:
        plain_text += f'\n{e.text}'

    driver.quit()

    # with open("plain_text.txt", 'w', encoding='utf-8') as file:
    #     file.write(plain_text)

    return plain_text, tab

def auto_get_title(url):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # 啟用無頭模式
    options.add_argument("--no-sandbox")  # 避免沙盒問題（推薦在 Linux 系統上加上這個參數）
    options.add_argument("--disable-dev-shm-usage")  # 避免資源限制錯誤

    # 自動下載並使用對應版本的 ChromeDriver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.get(url)

    h2_elements = driver.find_elements(By.TAG_NAME, 'h2')
    h2_elements = h2_elements[2:-1]
    h2_ids = [h2.get_attribute('id') for h2 in h2_elements]
    # print(h2_ids)

    head_elements = driver.find_elements(By.CSS_SELECTOR, 'h2, h3')
    head = [h.get_attribute('id') for h in head_elements]
    head_elements = head_elements[2:-2]
    head = [h.get_attribute('id') for h in head_elements]
    # print(head)

    titles = {}
    for h in head:
        if h in h2_ids:
            temp = h
            titles[temp] = []
        else:
            titles[temp].append(h)
    
    # print(f"蒐集到的標題: {h2_ids}")
    # print(f"全部包含細項: {titles}")

    return h2_ids, titles

# url = "https://info.poxa.io/report/20241125"
# auto_summary(*auto_get_text(url), *auto_get_title(url))