import logging
import logging.handlers
import os

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import date,timedelta,datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication


#########log and connect with github
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger_file_handler = logging.handlers.RotatingFileHandler(
    "status.log",
    maxBytes=1024 * 1024,
    backupCount=1,
    encoding="utf8",
)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger_file_handler.setFormatter(formatter)
logger.addHandler(logger_file_handler)

try:
    #logger.info(os.environ)
    SECRET = os.environ["ACTION_SECRET"]
except KeyError:
    SECRET = "Token not available!"
    logger.info("Token not available!")
    raise


#######define vars
url = "http://www.hsyce.com/"
suffix = "jszp/list.php?id=4"

curr_date = date.today()
yesterday = (curr_date-timedelta(1)).strftime('%Y-%m-%d')

smtp_config = {
    'server': 'smtp.qq.com',
    'port': 465,
    'username': '2196437340@qq.com',
    'password': 'lagmifgjsddkeaac',
    'to_wj': 'lwjanhui@163.com',
    'to_eva': ''
}


def get_html(url):
    html = requests.get(url)

    ######parse data
    html.encoding = 'utf-8'
    soup = BeautifulSoup(html.text, "html.parser")
    return soup

def parse_html(soup):
    hire = soup.find_all("ul","bd")[0]
    hire_ls = hire.find_all("li")

    results = [(li.find("a").get("href"),
                li.find("a").get_text().strip('\n').strip(),
                li.find("span").get_text()) for li in hire_ls]
    
    df = pd.DataFrame(results,columns=["href","title","date"])
    df["link"] = url + df["href"]
    df.drop("href",axis=1,inplace=True)
    
    return df


########convert into html
def get_send_html(df):
    heads = f"""
    <p>Hi, </p>
    <p>please see the latest teacher from {url} hirement infos.\n</p>
    """

    if df.shape[0]>0:
        html_pre = f"""
            <p>New hire infos:\n</p>
            """
        html_t = df.to_html(index=False)
        html_all = html_pre+html_t
    else:
        html_all = f"""
            <p>There is no new hire info from  {url+suffix} on {curr_date}.\n</p>
            """

    html_tot = heads+html_all
    
    return html_tot


def send_email_with_attachment(smtp_config, subject, df,to_email=smtp_config['to_wj']):

    ######generate html table
    html_content = get_send_html(df)

    msg = MIMEMultipart()
    msg['From'] = smtp_config['username']
    msg['To'] = to_email
    msg['Subject'] = subject
    
    msg.attach(MIMEText(html_content, 'html'))
    
    try:
        with smtplib.SMTP_SSL(smtp_config['server'], smtp_config['port']) as server:
            server.login(smtp_config['username'], smtp_config['password'])
            server.send_message(msg)
            server.quit()
        print("email send done")
    except Exception as e:
        print(f"email send failed: {e}")



if __name__ == "__main__":
    logger.info(f"Token value: {SECRET}")

    html = get_html(url+suffix)
    df = parse_html(html)
    df_update = df.loc[df["date"]==yesterday]

    send_email_with_attachment(smtp_config, f'Tech Hire Info --{curr_date}', df_update)
    logger.info(f'email update info done on {curr_date}')