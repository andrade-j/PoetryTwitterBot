from bs4 import BeautifulSoup
import re, requests, tweepy, time, os, random, io


class PoemScraper:

    formatted_data = {}
    poem_num = 1

    def scrape_website(self):
        # Get the poem names from the website
        website = 'https://rpo.library.utoronto.ca/poems'
        res = requests.get(website)
        res.raise_for_status()
        bs = BeautifulSoup(res.text, "html.parser")

        raw_links = bs.findAll('a', href=re.compile('^/poems/'))

        for poem in raw_links:
            link = str(poem)
            cleanURL = re.compile('(^<a href="/poems/.*">)')
            link = (cleanURL.search(link)).group()
            # print(link)
            link = link[15:-2]

            url = website + str(link)
            # print(url)

            # Get the individual poem page
            res = requests.get(url)
            res.raise_for_status()
            bs = BeautifulSoup(res.text, "html.parser")
            tag_set = bs.findAll('span', {'class': 'line-text'}, text=re.compile('.*'))

            # Get the poem title
            poem_title = bs.find('h1', {'id': 'page-title'})

            # Get the string part of the tag object and format it
            poem_title = poem_title.string
            poem_title = poem_title.strip()
            poem_title = poem_title.replace(' ', '')
            punctuation = ('!', ',' ,':', ';', '?', '.', '(', ')', '[', ']', '*','"', "'",'-', '‘', '’', '“', '”', '#')
            poem_title = ''.join(char for char in poem_title if char not in punctuation)
            poem_title = '#' + poem_title
            # print(poem_title)

            # Find the stanza linebreaks
            stanza_breaks = []
            for node in bs.findAll('div', {'class': 'poemline stanza'}):
                # print(node.findNext('span').contents[0])
                try:
                    stanza_breaks.append(int(node.findNext('span').contents[0]))
                except IndexError:
                    continue
                except ValueError:
                    continue
            # print(poem_title)
            PoemScraper.format_data(self, poem_title, tag_set, stanza_breaks)

    def save_data(self):
        with io.open('PoemData.py', 'w', encoding="utf-8") as storage_file:
            storage_file.write('data = ' + str(PoemScraper.formatted_data))
        storage_file.close()

    def format_data(self, title, tag_set, stanza_breaks):
        # Extract the text of the poems
        poem_text = ''
        line_count = 1
        for nodes in tag_set:
            poem_text += ''.join(nodes.findAll(text=True)) + '\n'

            # Check if new stanza
            if line_count + 1 in stanza_breaks:
                poem_text += '\n'
            line_count += 1

        PoemScraper.formatted_data.setdefault(PoemScraper.poem_num, {'title': '', 'text': ''})
        PoemScraper.formatted_data[PoemScraper.poem_num]['title'] = title
        PoemScraper.formatted_data[PoemScraper.poem_num]['text'] = poem_text
        PoemScraper.poem_num += 1


class TweetComposer:

    # Twitter generated keys
    consumer_key = ''
    consumer_secret = ''
    access_token = ''
    access_token_secret = ''

    # Set up access to Twitter account
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)

    def format_text(self, poem):
        # Break up the poem into 140 char segments
        poem_text = poem['text']
        poem_tweet = [poem['title']]
        start = 0
        end = 140
        while (end < len(poem_text)):
            # Prevent the splitting of words between tweets
            while (poem_text[end] not in ['.', ',', '!', '?', '\n', ':', ';']):
                end -= 1
            poem_tweet.append(poem_text[start:end])
            start = end
            end += 140

        # Tack on whatever is left
        poem_tweet.append(poem_text[start:])

        return poem_tweet

    def post_tweet(self, poem_tweet):
        for segment in poem_tweet:
            self.api.update_status(segment)
            time.sleep(3)
            # print(segment)

    def get_random_poem(self):
        # Collect the poem data, if it does not exist
        if not (os.path.exists('PoemData.py')):
            scraper = PoemScraper()
            scraper.scrape_website(self)
            scraper.save_data(self)

        try:
            import PoemData
        except ImportError:
            print('Error importing PoemData.py')
            os._exit(0)

        data = PoemData.data

        # Pick a random poem
        key = random.choice(list(data.keys()))
        poem = data.pop(key)

        # Overwrite the file
        with io.open('PoemData.py', 'w', encoding="utf-8") as storage_file:
            storage_file.write('data = ' + str(data))
        storage_file.close()

        return poem


def main():
    composer = TweetComposer()

    poem = composer.get_random_poem()
    poem_tweet = composer.format_text(poem)
    composer.post_tweet(poem_tweet)

if __name__ == "__main__":
    main()
