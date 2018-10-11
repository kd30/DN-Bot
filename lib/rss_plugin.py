import requests
import feedparser
import dataset

from bs4 import BeautifulSoup

ethNews = 'https://www.ethnews.com/rss.xml'
coinDesk = 'https://feeds.feedburner.com/CoinDesk'
coinTelegraph = 'https://cointelegraph.com/rss'
#redditCryptocurrency = "https://www.reddit.com/r/CryptoCurrency.rss"

feeds_list = [ethNews,coinDesk,coinTelegraph]


def fetch_feed_data():
    feed_dict = {}
    for feed in feeds_list:
        parsed_feed = feedparser.parse(feed)
        feed_dict[parsed_feed['feed']['title']] = parsed_feed

    feed_dict['CoinTelegraph'] = feed_dict.pop('Cointelegraph.com News')

    return feed_dict


def write_article_to_db(feed_item):
    db = dataset.connect('sqlite:///feed_items.db')

    table = db['articles']

    if table.find_one(title="{}".format(feed_item['title'])):
        print('That article was already in there')
        pass
    else:
        # Insert a new record.
        table.insert(feed_item)
        print("Inserted Article")


def grab_articles(feed_dict=fetch_feed_data()):
    feed_names = list(feed_dict)
    try:
        for fd in feed_names:
            # Simplify what we put in the database
            article_cleaned = {}

            if fd == 'ETHNews':
                soup = BeautifulSoup(feed_dict[fd].entries[0].title,"html.parser")
                article_cleaned['src'] = str(fd)
                article_cleaned['title'] = soup.text
                article_cleaned['link'] = feed_dict[fd].entries[0].link
                article_cleaned['description'] = feed_dict[fd].entries[0].description
                article_cleaned['sent'] = False

            else:
                # Simplify what we put in the database
                article_cleaned['src'] = str(fd)
                article_cleaned['title'] = feed_dict[fd].entries[0].title
                article_cleaned['link'] = feed_dict[fd].entries[0].link
                article_cleaned['description'] = feed_dict[fd].entries[0].description
                article_cleaned['sent'] = False

            # Try and pull out image and if we find one, commit it to the DB as 'image_url'
            soup = BeautifulSoup(article_cleaned['description'], 'html.parser')
            if soup.findAll(name='img'):
                image_link = (soup.findAll(name='img')[0]['src'])
                #print("Found an image link \n {}".format(image_link))
                article_cleaned['image_url'] = image_link
            else:
                article_cleaned['image_url'] = ''


            write_article_to_db(article_cleaned)

        print('Finished writing new articles to DB for now')
        return True

    except:
        return False


def check_db_for_new_articles():
    db = dataset.connect('sqlite:///feed_items.db')
    table = db['articles']

    unsent_articles = table.find(sent=0)

    return unsent_articles
