from slackclient import SlackClient
import summarize_plugin
import rss_plugin
import time
import threading
import sys
import json
import dataset
from SETTINGS import *

# TODO build in multiple attachment support. Break the photo into a separate section than the rest of it.
# TODO bring in the original description from the RSS feed instead of the summary. The color coded stuff is still nice
# TODO add more sources.
# TODO fix looping behavior

sc = SlackClient(slack_token)

def build_attachment(article_dict):
    print(article_dict['src'])

    # Highlight color based on News Source
    if article_dict['src'] == 'ETHNews':
        author_link = "https://www.ethnews.com/"
        article_dict['color'] = '#7c4dff'
    elif article_dict['src'] == 'CoinDesk':
        author_link = "https://www.coindesk.com/"
        article_dict['color'] = '#fcc118'
    elif article_dict['src'] == 'CoinTelegraph':
        author_link = "https://cointelegraph.com/"
        article_dict['color'] = '#253137'
    elif article_dict['src'] == 'redditCryptocurrency':
        author_link = "https://www.reddit.com/r/CryptoCurrency/"
        article_dict['color'] = '#e50000'
    else:
        author_link = ""

    slack_attachment = []

    # If contains images
    if "http" in article_dict['image_url']:
        slack_attachment.append({
            "title": "{}".format(article_dict['title']),
            "title_link": "{}".format(article_dict['link']),
            "fallback": "{}".format(article_dict['title']),
            "color": "{}".format(article_dict['color']),
            "image_url": "{}".format(article_dict['image_url'])

        })

        slack_attachment.append({
            "pretext": "*Summary Below*",
            "color": "{}".format(article_dict['color']),
            "text": "{}".format(article_dict['summary']),
            "author_name": "{}".format(article_dict['src']),
            "author_link": author_link,
            "footer": "Crypto News Bot",
            "footer_icon": "https://platform.slack-edge.com/img/default_application_icon.png",
            "mrkdwn_in": ["pretext"]
        })


    else:
        slack_attachment.append({
            "fallback": "{}".format(article_dict['title']),
            "color": "{}".format(article_dict['color']),
            "author_name": "{}".format(article_dict['src']),
            "author_link": author_link,
            "title": "{}".format(article_dict['title']),
            "title_link": "{}".format(article_dict['link']),
            "text": "{}".format(article_dict['summary']),
            "footer": "Crypto News Bot",
            "footer_icon": "https://platform.slack-edge.com/img/default_application_icon.png",
            "mrkdwn_in": ["pretext"]

        })


    return slack_attachment


def send_message(article_dict):

    response = sc.api_call(
        "chat.postMessage",
        channel="#{}".format(slack_channel),
        attachments=json.dumps(build_attachment(article_dict))
    )

    print(response)

    # If we successfully send the message, we mark it as sent in the Database.
    if response['ok']:
        print("Message sent!")

        article_id = article_dict['id']

        # Updating the record in the database now that we've summarized and sent the message
        db = dataset.connect('sqlite:///feed_items.db')
        table = db['articles']
        data = dict(id=article_id,sent=True)
        table.update(data, ['id'])

    else:
        print("There was an issue with sending the message, error is as follows: \n {}".format(response['error']))


def manager():
    if rss_plugin.grab_articles(): # Grabs articles and continues if successful
        new_articles = rss_plugin.check_db_for_new_articles() # Grab articles that haven't been sent so far

        #print(new_articles)

        # Grab Summary
        for article in new_articles:
            article_url = article['link']
            article['summary'] = summarize_plugin.request_summary(article_url)
            #article['summary'] = "FAKE SUMMARY FOR TESTING"
            print('Finished grabbing the summary for that one')

            # Send Slack message, passing along the article as a dictionary with the pruned information.
            send_message(article)

            # Wait 5 seconds so we don't send all the messages at once
            time.sleep(5)

        print("Done fetching articles for now. Sleeping for 5 minutes")
        return True

    else:
        print("Had an issue fetching the articles, so we're just going to quit out of this")
        sys.exit(1)

while True:
    manager()
    time.sleep(360)

