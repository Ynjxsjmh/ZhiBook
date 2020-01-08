import re
import json
import time
import requests
from datetime import datetime
from ebooklib import epub


def get_author_info_content(author):
    author_url = "https://www.zhihu.com/people/hydfox" + author["url_token"]

    author_info_content = """
    <div class="AuthorInfo-content">
     <div class="AuthorInfo-head">
      <span class="UserLink AuthorInfo-name">
       <div class="Popover">
        <div id="Popover222-toggle" aria-haspopup="true" aria-expanded="false" aria-owns="Popover222-content">
         作者：<a class="UserLink-link" data-za-detail-view-element_name="User" target="_blank" href="{0}">{1}</a>
        </div>
       </div>
      </span>
     </div>
     <div class="AuthorInfo-detail">
      <div class="AuthorInfo-badge">
       <div class="AuthorInfo-badgeText">
        签名：{2}
       </div>
      </div>
     </div>
    </div>
    <br/>
    """.format(author_url, author["name"], author["headline"])

    return author_info_content


def download_image(image_url, image_path):
    # 下载图片并保存到同目录下的 images 目录下
    with open(image_path, "wb") as handler:
        img_data = requests.get(image_url).content
        handler.write(img_data)
        time.sleep(3)


def parse_answer_content(answer_content, answer_number):
    """
    格式化答案：
    1. 去除答案首部和尾部的换行
    2. 处理图片
    """

    """
    得到的图片是如下这样表示的
    '<figure><noscript><img src="https://pic2.zhimg.com/50/dabb778580858a9d05e837e29b54e445_hd.jpg" data-rawwidth="155" data-rawheight="155" class="content_image" width="155"/></noscript><img src="data:image/svg+xml;utf8,&lt;svg xmlns=&#39;http://www.w3.org/2000/svg&#39; width=&#39;155&#39; height=&#39;155&#39;&gt;&lt;/svg&gt;" data-rawwidth="155" data-rawheight="155" class="content_image lazy" width="155" data-actualsrc="https://pic2.zhimg.com/50/dabb778580858a9d05e837e29b54e445_hd.jpg"/></figure>
    <noscript> 标签里的可以直接用
    后面的那个不行，因此去掉后面的，留下 <noscript> 里的
    """

    answer_content = answer_content.replace("</noscript>", "")
    answer_content = answer_content.replace("<noscript>", "")

    image_regex = r"<img.*?/>"
    image_tag_list = re.findall(image_regex, answer_content, re.S | re.M)

    for i in range(len(image_tag_list)):
        if i % 2 == 0:
            pass
        else:
            answer_content = answer_content.replace(image_tag_list[i], "")

    # 现在 answer 里的图片都是 <img src="https://pic2.zhimg.com/50/dabb778580858a9d05e837e29b54e445_hd.jpg" data-rawwidth="155" data-rawheight="155" class="content_image" width="155"/> 这样了
    # 把这些图片下载到本地
    image_url_regex = r"<img src=\"(.*?)\""
    image_url_list = re.findall(image_url_regex, answer_content, re.S | re.M)

    image_name_list = []
    dir_path = "./images/"
    for i in range(len(image_url_list)):
        image_url = image_url_list[i]
        # image_url.split("/")[-1]
        image_name = "{}-{}.jpg".format(answer_number, i)

        download_image(image_url, dir_path+image_name)

        answer_content = answer_content.replace(image_url, image_name)
        image_name_list.append(image_name)

    return answer_content, dir_path, image_name_list


def get_time_content(answer):
    created_time = int(answer["created_time"])
    time_content = "发布于：%s" % datetime.utcfromtimestamp(created_time).strftime("%Y-%m-%d %H:%M:%S")
    updated_time = int(answer["updated_time"])

    if updated_time != created_time:
        time_content += "<br/>修改于：%s" % datetime.utcfromtimestamp(updated_time).strftime("%Y-%m-%d %H:%M:%S")

    return time_content


def write_answer_to_file(book_title, answer_list, get_answers_time):
    print("Write info to file:start...")
    start_time = time.time()

    book = epub.EpubBook()

    # 若初始值为 'nav'，那么开头会多出个目录页
    chapter_list = []

    # set metadata
    book.set_identifier("id123456")
    book.set_title(book_title)
    book.set_language("en")

    book.add_author("Ynjxsjmh")

    # create chapter
    meta_chapter = epub.EpubHtml(title="关于", file_name="chap_0.xhtml", lang="hr")

    today = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
    meta_chapter.content = "截至 {0} 共爬取本问题下 {1} 个回答，耗时 {2:.2f} 秒".format(today, str(len(answer_list)), get_answers_time)

    chapter_list.append(meta_chapter)

    cur_answer_count = 0
    cur_downloaded_image_count = 0
    for answer in answer_list:
        cur_answer_count += 1
        file_name = "chap_" + str(cur_answer_count) + ".xhtml"

        # create and set chapter meta info
        author_name = answer["author"]["name"]
        voteup_count = answer["voteup_count"]
        chapter_title = str(cur_answer_count) + "-" + author_name + "-" + str(voteup_count) + "赞"
        chapter = epub.EpubHtml(title=chapter_title, file_name=file_name, lang="hr")

        # add content to chapter
        author_info_content = get_author_info_content(answer["author"])
        acceptance_content = "%s 人赞同了该回答<br/><br/>" % voteup_count
        time_content = get_time_content(answer)
        original_link = """<br/><br/><a target="_blank" href="https://www.zhihu.com/question/{}/answer/{}">原文链接</a><br/>""".format(answer["question"]["id"], answer["id"])
        print("Downloading images...")
        answer_content, dir_path, image_name_list = parse_answer_content(answer["content"], cur_answer_count)
        cur_downloaded_image_count += len(image_name_list)
        if len(image_name_list) != 0:
            print("\tDownloaded %d images" % len(image_name_list))
        chapter.content = author_info_content + acceptance_content + answer_content + original_link + time_content

        # 通过将图片变成封面的方式曲线将图片pack进文件
        for image_name in image_name_list:
            book.set_cover(image_name, open(dir_path+image_name, "rb").read())

        chapter_list.append(chapter)

        answer_url = answer["url"]

    end_time = time.time()

    meta_chapter.content += "<br/><br/> 下载 {0} 张图片和制作文件大概花了 {1:.2f} 秒".format(cur_downloaded_image_count, (end_time-start_time))

    # add chapter
    book.add_item(meta_chapter)
    for chapter in chapter_list:
        book.add_item(chapter)

    # create table of contents
    # - add manual link
    # - add section
    # - add auto created links to chapters
    book.toc = (tuple(chapter_list))

    # add default NCX and Nav file
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # create spine
    # 没有这行会出现“打开书籍失败的错误”
    # 分析：spine 有书脊的意思，应该是说书包含哪些章节
    book.spine = chapter_list

    # write to the file
    epub.write_epub(book_title + ".epub", book, {})

    print("Write info to file:end...")


def get_answers(question_id):
    start_time = time.time()

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
    url = "https://www.zhihu.com/api/v4/questions/" \
          + question_id + "/answers" \
          "?sort_by=default&include=data[*].is_normal,voteup_count,content" \
          "&limit=" + str(limit) + "&offset=" + str(offset)

    '''
    "https://www.zhihu.com/api/v4/questions/" \
          + question_id + "/answers" \ "?include=data%5B%2A%5D.is_normal%2Cadmin_closed_comment%2Creward_info%2Cis_collapsed%2Cannotation_action%2Cannotation_detail%2Ccollapse_reason%2Cis_sticky%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccan_comment%2Ccontent%2Ceditable_content%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Ccreated_time%2Cupdated_time%2Creview_info%2Crelevant_info%2Cquestion%2Cexcerpt%2Crelationship.is_authorized%2Cis_author%2Cvoting%2Cis_thanked%2Cis_nothelp%2Cis_labeled%2Cis_recognized%2Cpaid_info%2Cpaid_info_content%3Bdata%5B%2A%5D.mark_infos%5B%2A%5D.url%3Bdata%5B%2A%5D.author.follower_count%2Cbadge%5B%2A%5D.topics&" \
       "&limit=" + str(limit) + "&offset=" + str(offset) + "&platform=desktop&sort_by=default"
    '''

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

    end_time = time.time()

    if len(answer_list) > 0:
        title = answer_list[0]["question"]["title"]
    else:
        # 若问题没有回答，其实可以通过访问该问题页面得到问题标题
        # 这里简化了
        title = question_id

    write_answer_to_file(title, answer_list, end_time-start_time)


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


if __name__ == "__main__":
    start_time = time.time()

    get_answers("20717002")

    end_time = time.time()
    print(end_time - start_time)
