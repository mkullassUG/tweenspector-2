import html
import re
import statistics
from enum import auto

import pandas as pd
import spacy
import twint
from wordcloud import WordCloud


class UserStatsOptions:
    REACTIONS = auto(),
    TWEETS_PER_HOUR = auto(),
    HASHTAGS = auto()


class InterconnectionsNetworkOptions:
    OPTIMAL_MODULARITY = auto(),
    SPRINGLASS = auto(),
    LABEL_PROPAGATION = auto(),
    INFOMAP = auto()


class Tweets:  # tworzymy obiekt klasy Tweets, który ma wszystkie metody potrzebne do wczytania tweetów i prezentacji danych
    def __init__(self, user_name, search_words, date_from, date_to, num_of_tweets=500):
        self.user_name = user_name  # nazwa użytkownika, liczba tweetów, daty od/do, a także poszukiwane słowa
        self.num_of_tweets = num_of_tweets
        self.num_of_tweets_read = 0
        self.Since = date_from
        self.Until = date_to
        self.search_words = search_words

    def get_wordcloud(self, width=1000, height=500, font_path=None, color_function=None):
        tweets = get_tweets(self.user_name, self.search_words, self.Since, self.Until, self.num_of_tweets)
        if tweets.empty:
            return None
        try:
            words = {}
            nlp = spacy.load("pl_core_news_lg")
            stopwords = nlp.Defaults.stop_words
            stopwords.update(["RT", ".", ",", " ", "!", "?", ":", "-", "\"", "$"])
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
                tweets_text_from_lemmatizer = nlp(str(text))  # kolejno lematyzujemy wszystkie słowa
                for t in tweets_text_from_lemmatizer:  # do tekstu do przetworzenia dodajemy tylko słowa znaczące
                    word = html.unescape(t.lemma_)
                    if t.lemma_ not in stopwords and word not in stopwords:
                        if word in words:
                            words[word] = words.get(word) + 1
                        else:
                            words[word] = 1

            wordcloud = WordCloud(
                background_color='black',
                colormap='Pastel1',
                width=width,
                height=height,
                stopwords=stopwords,
                regexp=r"\w[\w'\&\-]*\w",
                font_path=font_path,
                color_func=color_function)
            ret = wordcloud.fit_words(words).layout_
            return words, ret, (wordcloud.width * wordcloud.scale, wordcloud.height * wordcloud.scale)
        except ValueError as exc:  # obsługa wyjątków
            print("Generate word cloud - Blad wartosci")
            raise exc
        except Exception as exc:
            print("Generate word cloud - Cos poszlo nie tak: {excType} {excMsg}"
                  .format(excType=type(exc).__name__, excMsg=str(exc)))
            raise exc

    def get_interconnections_network(self):  # tu utworzenie grafu powiązań
        tweets = get_tweets(self.user_name, self.search_words, self.Since, self.Until, self.num_of_tweets)
        if tweets.empty:
            return None

        people = set()
        people.add(self.user_name.lower())
        for r in tweets.iterrows():
            text = r[1]['tweet']
            mts = set(re.findall(r"@(\w+)", text))
            for mt in mts:
                mt = mt.lower()
                people.add(mt)

        relations = dict()
        for someone in people:
            relations[someone] = dict()  # kolejno zliczamy interakcje użytkowników grafu ze sobą
            friend_tweets = get_tweets(someone, self.search_words, self.Since, self.Until, self.num_of_tweets)
            if friend_tweets.empty:  # w razie braku tweetów danego użytkownika informujemy o tym i idziemy dalej
                print("Generate interconnections network - Brak konta, user:", someone)
                continue
            for r in friend_tweets.iterrows():  # zliczanie odbywa się tutaj, interakcja to wspomnienie jednego użytkownika o drugim
                text = r[1]['tweet']
                mts = set(re.findall(r"@(\w+)", text))
                for mt in mts:
                    mt = mt.lower()
                    if mt in people:
                        if mt != someone:
                            if mt in relations[someone]:
                                relations[someone][mt] = relations[someone][mt] + 1
                            else:
                                relations[someone][mt] = 1

        #     x = 1000 * math.log(len(people))
        #     y = 600 * math.log(len(people))
        #     visual_style = {
        #         "vertex_size": 40,
        #         "vertex_label_size": 50,
        #         "vertex_label_dist": 2,
        #         "margin": 250,
        #         "bbox": (x, y),
        #         "vertex_label": people,
        #         "edge_width":
        #             [math.log(2 * relations[g.vs[edge.source]["name"]][g.vs[edge.target]["name"]], 1.5)
        #              for edge in g.es]
        #     }

        return people, relations  # vertices, edges

    def get_user_stats(self, option: UserStatsOptions):
        def generate_account_info(df):
            date1 = pd.to_datetime(df.iloc[0].date)
            date2 = pd.to_datetime(df.iloc[int(self.num_of_tweets_read) - 1].date)
            usersdict = dict()
            for tweet in df.tweet:
                mts = set(re.findall(r"@(\w+)", tweet))
                for mt in mts:
                    mt = mt.lower()
                    if mt in usersdict:
                        usersdict[mt] = usersdict[mt] + 1
                    else:
                        usersdict[mt] = 1
            hourdict = dict()
            for hour in df.hour:
                if hour in hourdict:
                    hourdict[hour] = hourdict[hour] + 1
                else:
                    hourdict[hour] = 1
            account_stats = {
                'avglikes': round(sum(df[df.retweet == False].nlikes) / len(df[df.retweet == False].nlikes)),
                'maxlikes': max(df[df.retweet == False].nlikes),
                'minlikes': min(df[df.retweet == False].nlikes),
                'medianlikes': statistics.median(df[df.retweet == False].nlikes),
                'avgretweets': round(sum(df[df.retweet == False].nretweets) /
                                     len(df[df.retweet == False].nretweets)),
                'maxretweets': max(df[df.retweet == False].nretweets),
                'minretweets': min(df[df.retweet == False].nretweets),
                'medianretweets': statistics.median(df[df.retweet == False].nretweets),
                'interval': (date1 - date2) / (int(self.num_of_tweets_read) - 1),  # średni odstęp między tweetami
                'places': set(),
                'hashtagdict': dict(),
                'usersdict': dict(sorted(usersdict.items(), key=lambda x: x[1])),  # uzytkownicy, o których wspomniano
                'hourdict': dict(sorted(hourdict.items(), key=lambda x: x[1]))}  # i godziny napisania

            for place in df.place:
                if place != '':
                    account_stats['places'].add(place)

            for hashtags in df.hashtags:
                for hashtag in hashtags:
                    if hashtag:
                        if hashtag in account_stats['hashtagdict']:
                            account_stats['hashtagdict'][hashtag] = account_stats['hashtagdict'][hashtag] + 1
                        else:
                            account_stats['hashtagdict'][hashtag] = 1
            return account_stats

        data_frame = get_tweets(self.user_name, self.search_words, self.Since, self.Until,
                                self.num_of_tweets)  # by mieć statystyki potrzebujemy tweetów
        if data_frame.empty:
            return None
        account_stats = generate_account_info(data_frame)

        def generate_reaction_stats():
            values_name = {'maxlikes': "Największa liczba likeów",
                           'avglikes': "Średnia ilość likeów",
                           'medianlikes': "Mediana liczby likeów",
                           'maxretweets': "Największa liczba retweetów",
                           'avgretweets': "Średnia liczba retweetów",
                           'medianretweets': "Mediana liczby retweetów",
                           }
            return list(values_name.values()), [account_stats[name] for name in list(values_name.keys())]

        def generate_tweets_per_hour_stats():
            hours_dict = account_stats["hourdict"]

            hours = []
            for i in range(10):
                hours.append("0" + str(i))
            for i in range(10, 24):
                hours.append(str(i))

            tweets_hour_count = []
            for hour in hours:
                if hour in list(hours_dict.keys()):
                    tweets_hour_count.append(hours_dict[hour])
                else:
                    tweets_hour_count.append(0)

            return hours, tweets_hour_count

        def generate_hashtag_stats():  # zwrócenie najczęściej użytych hasztagów
            hashtag_dict = account_stats["hashtagdict"]
            sorted_hashtag = list((sorted(hashtag_dict.items(), key=lambda item: item[1])))[::-1]
            filter_hashtag = sorted_hashtag[:10]  # 10 most popular hashtags

            hashtag_name = [i[0] for i in filter_hashtag]
            hashtag_count = [i[1] for i in filter_hashtag]

            return hashtag_name, hashtag_count

        if option == UserStatsOptions.REACTIONS:
            return generate_reaction_stats()
        elif option == UserStatsOptions.TWEETS_PER_HOUR:
            return generate_tweets_per_hour_stats()
        elif option == UserStatsOptions.HASHTAGS:
            return generate_hashtag_stats()
        else:
            return None


def get_tweets(user_name, search_words, date_from, date_to, num_of_tweets):
    # return pd.read_csv("donaldtusk.csv",
    #                    converters={
    #                        "place": lambda p: str(p),
    #                        "hour": lambda h: str(h),
    #                        "hashtags": lambda h: [x.strip(" '\"") for x in str(h).strip("[]").split(",")]
    #                    })
    try:
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
