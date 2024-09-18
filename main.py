from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from openai import OpenAI

from datetime import datetime
from config import SUMMARY_URL, BUTTONS_SELECTOR

# 自動生成摘要
def auto_summary(plain_text, h2_titles, all_titles):

    with open("summary_example.txt", 'r', encoding='utf-8') as file:
        output_sample = file.read()

    client = OpenAI()

    # 請 GPT 幫忙過濾掉無關的文字
    week_analysis = h2_titles[1]
    temp = f"其中「本週主題分析」需要提到即時、補充"
    temp += f"，除此之外，還要包含 {'、'.join(all_titles[week_analysis])}" if len(all_titles[week_analysis])!=0 else ""if len(all_titles[week_analysis])!=0 else ""

    messages = []
    messages.append({
        "role": "system",
        "content": f"""
        您是一個直到獲取所有資訊後，才摘要重點的助手，會按照期望的輸出格式給予回覆，請依照以下標題 {h2_titles} 進行摘要。
        {temp}
        其中「市場最新動態」還須包含四個子標題「調頻服務」、「E-dReg」、「即時備轉」、「補充備轉」，每個子標題需包含以下內容：
        「平均結清價格(required)」、「平均結清價格較上週上升or下滑多少(required)」、「本週參與容量(required)」、「參與容量較上週上升or下滑多少(required)」、「來自哪裡(optional)」，請用一句話描述，不需要分段。
        其中「台電電力供需資料」一定會提到「再生能源占比(required)」、「滲透率(required)」。
        
        期望的輸出格式如下（它是過去的歷史資料，這只是給你參考輸出的格式，並非實際的數據，請不要參考其中的數據內容）:
        {output_sample}。

        而實際的數據如下:
        {plain_text}
        """
        })
    
    response = client.chat.completions.create(
        model="gpt-4o-mini", 
        messages=messages,
        temperature=0
    )
    final_response = response.choices[0].message.content

    with open(f"output/{datetime.today().strftime('%Y-%m-%d')}.mdx", 'w', encoding='utf-8') as file:
        file.write(final_response)

def auto_get_text():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    driver.get(SUMMARY_URL)

    plain_text = "📈 市場最新動態"

    # button 要先拿，因為使用 XPATH，移除本週摘要的時候會影響到
    button_element = driver.find_element(By.XPATH, '//*[@id="__next"]/div/div[2]/article/div[5]/div[1]')
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'button')))
    buttons = button_element.find_elements(By.TAG_NAME, 'button')

    for i in range(0, 5):
        buttons[i].click()
        panel_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, BUTTONS_SELECTOR[i]))
        )
        # panel_element = driver.find_element(By.CSS_SELECTOR, BUTTONS_SELECTOR[i])
        p_elements = panel_element.find_elements(By.TAG_NAME, 'p')

        for p in p_elements:
            plain_text += f'\n{p.text}'

    # 移除本週摘要
    need_remove = driver.find_element(By.XPATH, '//*[@id="本週摘要"]')
    driver.execute_script("arguments[0].remove();", need_remove)
    need_remove = driver.find_element(By.XPATH, '//*[@id="__next"]/div/div[2]/article/div[3]')
    driver.execute_script("arguments[0].remove();", need_remove)

    element = driver.find_element(By.CSS_SELECTOR, "#__next > div > div.relative.grid.justify-center > article")
    elements = element.find_elements(By.CSS_SELECTOR, 'h2, p, ul')

    # print(len(p_elements))

    for e in elements:
        plain_text += f'\n{e.text}'

    driver.quit()

    with open("output/plain_text.txt", 'w', encoding='utf-8') as file:
        file.write(plain_text)

    return plain_text

def auto_get_title():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    driver.get(SUMMARY_URL)

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
    
    # print(f"蒐集到的標題: {titles}")

    return h2_ids, titles

auto_summary(auto_get_text(), *auto_get_title())