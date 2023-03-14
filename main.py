import requests
from bs4 import BeautifulSoup
import string
import os
import openai
from datetime import datetime

AI_SUMMARY = True
AI_SUMMARY_MAX_LENGTH = 60


def ai_generated_summary(input_text):
    """ Generates a summary of the input text thanks to the davinci-003 model from OpenAI.
    To use it, create an API account, retrieve your API key, and set it as an environment variable"""
    openai.api_key = os.getenv("OPENAI_API_KEY")
    summary_obj = openai.Completion.create(
        model="text-davinci-003",
        prompt=f"Write a very short summary (you can be really general about it) of the following article teaser: '{input_text}'",
        max_tokens=AI_SUMMARY_MAX_LENGTH,
        temperature=0.5
    )
    summary_text = summary_obj["choices"][0]["text"]
    return summary_text


def clean_title_name(name):
    forbidden_punct = string.punctuation + "—"
    name = name.strip()
    for char in name:
        if char in forbidden_punct:
            name = name.replace(char, "")
    name = name.replace(" ", "_", name.count(" "))
    if "__" in name:
        name = name.replace("__", "_", name.count("__"))
    return name


def create_write_file(path_to_dir, name, content):
    """ Writes the content (text) into a .txt file.
     Content contains the teaser of the article, and if AI_SUMMARY was set to true,
     then it also writes its AI generated summary"""
    name = clean_title_name(name)
    content = content.strip()
    file_name = os.path.join(path_to_dir, name + ".txt")
    file = open(file_name, "wb")
    file.write(content.encode())
    file.close()
    return None


def scrape(nb, type_art):
    """ Scrapes the Nature website (articles of 2020) for nb number of pages
    and for the type of article specified (e.g. 'News', 'News & Views'"""
    time_str = str(datetime.now())
    for page_nb in range(1, nb+1):
        url = f"https://www.nature.com/nature/articles?sort=PubDate&year=2020&page={page_nb}"
        r = requests.get(url)
        if r.status_code == 200:
            path_to_dir = os.path.join(os.getcwd(), "data", type_art + time_str, f"Page_{page_nb}")
            os.makedirs(path_to_dir, exist_ok=True)
            soup = BeautifulSoup(r.content, "html.parser")
            articles = soup.find_all("article")
            for article in articles:
                type_news = article.find('div', {'class': "c-card__section c-meta"})
                type_news = type_news.find('span', {'class': "c-meta__type"})
                type_news = type_news.text
                if type_news == type_art:
                    link = article.find('h3', {'class': "c-card__title", 'itemprop': "name headline"})
                    link = link.find('a')
                    link = link.get('href')
                    news_url = "http://www.nature.com" + link
                    news_r = requests.get(news_url)
                    if news_r.status_code == 200:
                        soup_news = BeautifulSoup(news_r.content, "html.parser")
                        name_article = soup_news.find("title").text
                        # body_news = soup_news.find('div', {'class': "c-article-body main-content"}).text
                        # previously the access was free, and we could access the article's content.
                        # Now we only have access to the teaser
                        # (to be verified because Nature changed its website regularly those last months)
                        teaser_news = soup_news.find('p', {'class': 'article__teaser'})
                        try:
                            teaser_news_text = teaser_news.text
                        except AttributeError:
                            print("attribute error")
                            pass
                        else:
                            if AI_SUMMARY:
                                ai_summary_text = ai_generated_summary(teaser_news_text)
                                final_text = f"Summary: {ai_summary_text} \n \nTeaser: {teaser_news_text}"
                                print("Summary: ", ai_summary_text)
                                print("Teaser: ", teaser_news_text)
                                create_write_file(path_to_dir, name_article, final_text)
                            else:
                                final_text = f"Teaser: {teaser_news_text}"
                                create_write_file(path_to_dir, name_article, final_text)

                    else:
                        print(f"The URL returned {news_r.status_code}!")
                        return None
        else:
            print(f"The URL returned {r.status_code}!")

    return None


def main():
    print("You're about to scrape https://www.nature.com/nature/articles?sort=PubDate&year=2020 ")
    nb_pages = int(input("How many pages do you want to scrape (give an integer)?"))
    type_article = input("What type of articles are you interested in (ex: 'News', 'News & Views'?")
    scrape(nb_pages, type_article)
    return None


if __name__ == '__main__':
    main()

