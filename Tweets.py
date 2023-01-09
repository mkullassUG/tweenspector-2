import html
import re
import pandas as pd
import spacy
import twint


class Tweets:  # tworzymy obiekt klasy Tweets, który ma wszystkie metody potrzebne do wczytania tweetów i prezentacji danych
    def __init__(self, user_name, search_words, date_from, date_to, num_of_tweets=500):
        self.user_name = user_name  # nazwa użytkownika, liczba tweetów, daty od/do, a także poszukiwane słowa
        self.num_of_tweets = num_of_tweets
        self.num_of_tweets_read = 0
        self.Since = date_from
        self.Until = date_to
        self.search_words = search_words

    def get_wordcloud_words(self):
        tweets = get_tweets(self.user_name, self.search_words, self.Since, self.Until, self.num_of_tweets)
        if tweets.empty:  # wczytujemy tweety, jeśli brak tweetów to wychodzimy
            return None
        try:
            words = []
            lemmatizer_enabled = True  # włączamy lematyzer
            preprocessed_tweets_text = ''  # tu tekst tweetów po przetworzeniu
            nlp = spacy.load("pl_core_news_lg")
            # tutaj kolejno szukamy wspominków o innych kontach by dodać je do słów nieznaczących
            for tweet in tweets.iterrows():
                text = tweet[1]['tweet']
                # w pierwszym kroku odflitrowujemy wszystkie linki http/https
                lst = re.findall('http://\S+|https://\S+', text)
                for i in lst:
                    text = text.replace(i, '')
                # w kolejnym usuwamy wszystkie odwoloania do @nazwa
                lst = re.findall(r"(@\w+)", text)
                for i in lst:
                    text = text.replace(i, '')
                if lemmatizer_enabled:  # tutaj lematyzacja słów
                    stopwords = nlp.Defaults.stop_words
                    stopwords.add("RT")
                    tweets_text_from_lemmatizer = nlp(str(text))  # kolejno lematyzujemy wszystkie słowa
                    for t in tweets_text_from_lemmatizer:  # do tekstu do przetworzenia dodajemy tylko słowa znaczące
                        if t.lemma_ not in stopwords:
                            words.append(html.unescape(t.lemma_))
                else:
                    # gdyby lematyzer był wyłączony to w tekście wszystkie słowa
                    words = tweets.tweet.values
            return words
        except ValueError:  # obsługa wyjątków
            print("Generate word cloud - Blad wartosci")
            return None
        except Exception as exc:
            print("Generate word cloud - Cos poszlo nie tak: {excType} {excMsg}"
                  .format(excType=type(exc).__name__, excMsg=str(exc)))
            return None


def get_tweets(user_name, search_words, date_from, date_to, num_of_tweets):  # wczytanie tweetów
    try:  # w przeciwnym razie konfigurujemy Twinta
        c = twint.Config()
        c.Username = user_name
        c.Limit = num_of_tweets
        c.Pandas = True
        c.Retweets = True
        c.Pandas_clean = True
        c.Stats = True
        c.Count = True
        c.Since = date_from
        c.Until = date_to
        c.Search = search_words
        c.Hide_output = True
        twint.run.Profile(c)
        if twint.output.panda.Tweets_df.empty:  # jeśli nie znaleziono tweetów to informujemy o tym
            print("No tweets from user: ", user_name)
            return twint.output.panda.Tweets_df
        else:  # zwracamy pustą lub pełną ramke danych
            return twint.output.panda.Tweets_df
    except ValueError:  # obsługujemy potencjalne wyjątki
        print("Get tweets - Blad wartosci, user:", user_name)
        return pd.DataFrame()
    except Exception as exc:
        print("Get tweets - Cos poszlo nie tak, user: {user}, wyjatek: {excType} {excMsg}"
              .format(user=user_name, excType=type(exc).__name__, excMsg=str(exc)))
        return pd.DataFrame()
