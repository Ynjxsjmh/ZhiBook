import re
import json
import requests

from util import *


def get_answers(question_id, sort_type):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36",
               "Host": "www.zhihu.com",
               "Referer": "https://www.zhihu.com/",
               }

    # 每次我们取10条回答
    limit = 10
    # 获取答案时的偏移量
    offset = 0
    # 答案排序方式，还有 updated 按时间排序
    sort_by = "default"

    # 我们获取数据的URL格式是什么样呢？
    # https://www.zhihu.com/api/v4/questions/39162814/answers?
    # sort_by=default&include=data[*].is_normal,content&limit=5&offset=0
    url = "https://www.zhihu.com/api/v4/questions/{0}/answers?sort_by={1}&include=data[*].is_normal,voteup_count,content&limit={2}&offset={3}"
    url = url.format(question_id, sort_by, limit, offset)


    '''
    折叠的回答
    https://www.zhihu.com/api/v4/questions/20717002/collapsed-answers?include=data%5B*%5D.is_normal%2Cadmin_closed_comment%2Creward_info%2Cis_collapsed%2Cannotation_action%2Cannotation_detail%2Ccollapse_reason%2Cis_sticky%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccan_comment%2Ccontent%2Ceditable_content%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Ccreated_time%2Cupdated_time%2Creview_info%2Crelevant_info%2Cquestion%2Cexcerpt%2Crelationship.is_authorized%2Cis_author%2Cvoting%2Cis_thanked%2Cis_nothelp%2Cis_labeled%2Cis_recognized%2Cpaid_info%2Cpaid_info_content%3Bdata%5B*%5D.mark_infos%5B*%5D.url%3Bdata%5B*%5D.author.follower_count%2Cbadge%5B*%5D.topics&offset=&limit=5&sort_by=default
    '''

    answer_list = []
    is_end = False

    while not is_end:
        response = requests.get(url, headers=headers)

        # 返回的信息为json类型
        response = json.loads(response.content)

        data_list = response["data"]

        answer_list += data_list

        is_end = response["paging"]["is_end"]
        url = response["paging"]["next"]

    print("Fetch info end...")
    print("Got answer num:" + str(len(answer_list)))

    '''
    答案排序方式：
    1. 点赞数
    2. 评论数
    3. 更新时间
    '''

    return answer_list


def get_comments(answer_url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36",
               "Host": "www.zhihu.com",
               "Referer": "https://www.zhihu.com/",
               }

    url = answer_url + "/comments?order=normal&limit=20&offset=0"

    '''
    默认排序
    https://www.zhihu.com/api/v4/questions/20717002/root_comments?order=normal&limit=10&offset=0

    时间排序
    https://www.zhihu.com/api/v4/questions/20717002/comments?order=reverse&limit=10&offset=0&status=open
    '''

    comment_list = []
    is_end = False

    while not is_end:
        response = requests.get(url, headers=headers)

        # 返回的信息为json类型
        response = json.loads(response.content)

        data_list = response["data"]

        comment_list += data_list

        is_end = response["paging"]["is_end"]
        url = response["paging"]["next"]


def get_question(question_id):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36",
        "Host": "www.zhihu.com",
        "Referer": "https://www.zhihu.com/",
    }

    url = "https://www.zhihu.com/api/v4/questions/{0}?include=data[*].answer_count%2Cauthor%2Cfollower_count"
    url = url.format(question_id)

    response = requests.get(url, headers=headers)

    # 返回的信息为json类型
    question = json.loads(response.content)

    return question
