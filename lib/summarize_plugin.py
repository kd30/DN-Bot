import requests
import json
import logging
import re

# When we get a link form an RSS feed, we go to the website, grab the full version, and summarize it.

def request_summary(article_url):

    smmry_api_url = "http://api.smmry.com/"

    querystring = {"SM_API_KEY": "XXXXXX",
                "SM_LENGTH": "7",
                "SM_WITH_BREAK": "",
                "SM_URL": "{}".format(article_url),
                }
    summary_json = json.loads(requests.request("GET", smmry_api_url, params=querystring).text)

    print(summary_json)



    try:
        logging.debug(summary_json['sm_api_error'])
        print(summary_json['sm_api_error'])
    except:
        nasty_break = (str(summary_json['sm_api_content']).replace("[BREAK]", "\n \n"))
        summary_json['sm_api_content'] = nasty_break
        title = summary_json['sm_api_title']
        text_only = summary_json['sm_api_content']

        print(text_only)
        print(title)
        return text_only

