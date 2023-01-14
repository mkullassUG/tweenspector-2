import datetime
from datetime import date

from bokeh.io import curdoc
from bokeh.layouts import column, layout, row, Spacer
from bokeh.models import Select, DatePicker, TextInput, Button, TableColumn, DataTable
from bokeh.models.callbacks import CustomJS
from bokeh.models.ui import Dialog

import numpy as np
import networkx as nx
import twint

from bokeh.io import show
from bokeh.models import Circle, MultiLine
from bokeh.plotting import figure, from_networkx
from bokeh.models import ColumnDataSource
from bokeh.transform import dodge
from numpy.random import randint
import pandas as pd
import nest_asyncio

from Tweets import Tweets

nest_asyncio.apply()


class Dashboard:
    """
    main dashboard class with class members for dashboard global variables which can be changed by callbacks
    """

    def __init__(self,
                 active_window_size=7,
                 ):
        # global variables which can be controlled by interactive bokeh elements
        self.plot_container = None
        self.error_dialog_container = None
        self.active_window_size = active_window_size
        self.layout = None
        self.empty_element = None

        tweet_num_options = [str(n) for n in range(100, 3100, 100)]
        functionalities = [
            ("wordcloud", "Najczęstsze słowa"),
            ("interconnections_network", "Powiązane konta"),
            ("user_stats", "Statystyki użytkownika")]

        self.username = TextInput(title="Nazwa użytkownika")
        self.search_word = TextInput(title="Poszukiwane słowo")
        self.date_from = DatePicker(title="Data początkowa", value=date.today() - datetime.timedelta(days=30))
        self.date_until = DatePicker(title="Data końcowa", value=date.today())
        self.num_of_tweets = Select(title="Liczba tweetow", value='100', options=tweet_num_options)
        self.functionality = Select(title="Funkcjonalność", value="wordcloud", options=functionalities)
        self.refresh_button = Button(label="Załaduj tweety", button_type="default", width=150)
        self.refresh_button.on_event('button_click', self.refresh)
        self.export_button = Button(label="Zapisz do CSV", button_type="default", width=150)
        self.export_button.on_event('button_click', self.save_to_csv)
        self.export_button.disabled = True  # TODO remove once save_to_csv() is implemented
        self.columns = None

    def hide_display(self):
        self.plot_container.children[0] = self.empty_element

    def show_display(self, content):
        self.plot_container.children[0] = content

    def show_error_message(self, message, title="Error"):
        error_dialog = Dialog(title=title, content=message)
        self.error_dialog_container.children[0] = error_dialog

    def refresh(self):
        self.hide_display()
        funct = self.functionality.value
        try:
            if funct == "wordcloud":
                user_name = self.username.value
                search_words = self.search_word.value
                date_from = self.date_from.value
                date_to = self.date_until.value
                tweets_count = self.num_of_tweets.value

                tweets = Tweets(user_name, search_words, date_from, date_to, tweets_count)
                words = tweets.get_wordcloud_words()
                if words is None:
                    self.show_error_message("Brak tweetów do wyświetlenia dla podanych parametrów")
                else:
                    # TODO display word cloud
                    print(f"{len(words)} words to display")
                    p, _, _, _ = self.generate_test_figures()
                    self.show_display(p)
                    print("Wordcloud displayed")
            elif funct == "interconnections_network":
                # TODO implement
                _, q, _, _ = self.generate_test_figures()
                self.show_display(q)
                print("Interconnections network displayed")
            elif funct == "user_stats":
                # TODO implement
                _, _, r, _ = self.generate_test_figures()
                self.show_display(r)
                print("User stats displayed")
            else:
                raise ValueError("Należy wybrać funkcjonalność")
        except Exception as e:
            self.show_error_message(str(e))
            raise e

    def save_to_csv(self):
        # TODO implement
        pass

    def generate_test_figures(self):
        x = np.linspace(0, 4 * np.pi, 100)
        y = np.sin(x)
        p = figure(title="Legend Example")
        p.circle(x, y, legend_label="sin(x)")
        p.circle(x, 2 * y, legend_label="2*sin(x)", color="orange")
        p.circle(x, 3 * y, legend_label="3*sin(x)", color="green")
        p.legend.title = 'Markers'

        G = nx.karate_club_graph()

        SAME_CLUB_COLOR, DIFFERENT_CLUB_COLOR = "darkgrey", "red"

        edge_attrs = {}
        for start_node, end_node, _ in G.edges(data=True):
            edge_color = SAME_CLUB_COLOR if G.nodes[start_node]["club"] == G.nodes[end_node][
                "club"] else DIFFERENT_CLUB_COLOR
            edge_attrs[(start_node, end_node)] = edge_color

        nx.set_edge_attributes(G, edge_attrs, "edge_color")

        q = figure(width=400, height=400, x_range=(-1.2, 1.2), y_range=(-1.2, 1.2),
                   x_axis_location=None, y_axis_location=None, toolbar_location=None,
                   title="Graph Interaction Demo", background_fill_color="#efefef",
                   tooltips="index: @index, club: @club")
        q.grid.grid_line_color = None

        graph_renderer = from_networkx(G, nx.spring_layout, scale=1, center=(0, 0))
        graph_renderer.node_renderer.glyph = Circle(size=15, fill_color="lightblue")
        graph_renderer.edge_renderer.glyph = MultiLine(line_color="edge_color",
                                                       line_alpha=0.8, line_width=1.5)
        q.renderers.append(graph_renderer)
        fruits = ['Apples', 'Pears', 'Nectarines', 'Plums', 'Grapes', 'Strawberries']
        years = ['2015', '2016', '2017']

        data = {'fruits': fruits,
                '2015': [2, 1, 4, 3, 2, 4],
                '2016': [5, 3, 3, 2, 4, 6],
                '2017': [3, 2, 4, 4, 5, 3]}

        source = ColumnDataSource(data=data)

        r = figure(x_range=fruits, y_range=(0, 10), title="Fruit Counts by Year",
                   height=350, toolbar_location=None, tools="")

        r.vbar(x=dodge('fruits', -0.25, range=r.x_range), top='2015', source=source,
               width=0.2, color="#c9d9d3", legend_label="2015")

        r.vbar(x=dodge('fruits', 0.0, range=r.x_range), top='2016', source=source,
               width=0.2, color="#718dbf", legend_label="2016")

        r.vbar(x=dodge('fruits', 0.25, range=r.x_range), top='2017', source=source,
               width=0.2, color="#e84d60", legend_label="2017")

        r.x_range.range_padding = 0.1
        r.xgrid.grid_line_color = None
        r.legend.location = "top_left"
        r.legend.orientation = "horizontal"
        data1 = pd.read_csv("donaldtusk.csv")
        source = ColumnDataSource(data1)

        self.columns = [
            TableColumn(field="id", title="ID"),
            TableColumn(field="tweet", title="Tekst"),
        ]
        s = DataTable(source=source, columns=self.columns, width=400, height=280, editable=False)
        return [p, q, r, s]

    def do_layout(self):
        """
        generates the overall layout by creating all the widgets, buttons etc and arranges
        them in rows and columns
        :return: None
        """

        self.empty_element = Spacer(width=0, height=0)
        self.plot_container = column(self.empty_element)

        dummy_dialog = Dialog(title="Error", content="An error occurred")
        dummy_dialog.visible = False
        self.error_dialog_container = column(dummy_dialog)

        self.layout = layout(children=[
            row(Spacer(sizing_mode="stretch_both"),
                column(
                    Spacer(width=1, sizing_mode="stretch_height"),
                    column(self.username, self.search_word, self.date_from, self.date_until, self.num_of_tweets,
                           self.functionality, row(self.refresh_button, self.export_button)),
                    Spacer(width=1, sizing_mode="stretch_height"),
                    sizing_mode="stretch_height"),
                column(
                    Spacer(width=1, sizing_mode="stretch_height"),
                    self.plot_container,
                    Spacer(width=1, sizing_mode="stretch_height"),
                    sizing_mode="stretch_height"),
                self.error_dialog_container,
                Spacer(sizing_mode="stretch_both"),
                sizing_mode="stretch_both")
        ], sizing_mode="stretch_both")

        curdoc().add_root(self.layout)
        curdoc().title = "Tweenspector"


dash = Dashboard()
dash.do_layout()
