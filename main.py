import datetime
import math
from datetime import date

from bokeh.io import curdoc
from bokeh.layouts import column, layout, row, Spacer
from bokeh.models import Select, DatePicker, TextInput, Button, TableColumn, DataTable, CrosshairTool, HoverTool, \
    SaveTool, RadioGroup
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

from Tweets import Tweets, UserStatsOptions, InterconnectionsNetworkOptions

nest_asyncio.apply()


class Dashboard:
    """
    main dashboard class with class members for dashboard global variables which can be changed by callbacks
    """

    def __init__(self,
                 active_window_size=7,
                 ):
        # global variables which can be controlled by interactive bokeh elements
        self.display_container = None
        self.error_dialog_container = None
        self.active_window_size = active_window_size
        self.layout = None

        tweet_num_options = [str(n) for n in range(100, 3100, 100)]
        functionalities = [
            ("wordcloud", "Najczęstsze słowa"),
            ("interconnections_network", "Powiązane konta"),
            ("user_stats", "Statystyki użytkownika")]

        self.inter_net_options = [
            ("Optimal modularity", InterconnectionsNetworkOptions.OPTIMAL_MODULARITY),
            ("Springlass", InterconnectionsNetworkOptions.SPRINGLASS),
            ("Label propagation", InterconnectionsNetworkOptions.LABEL_PROPAGATION),
            ("Infomap", InterconnectionsNetworkOptions.INFOMAP)
        ]
        self.user_stats_options = [
            ("Reakcje na tweety", UserStatsOptions.REACTIONS),
            ("Godzina publikacji", UserStatsOptions.TWEETS_PER_HOUR),
            ("Hasztagi", UserStatsOptions.HASHTAGS)
        ]

        self.inter_net_option_widgets = RadioGroup(labels=[t[0] for t in self.inter_net_options], active=0,
                                                   visible=False)
        self.user_stats_option_widgets = RadioGroup(labels=[t[0] for t in self.user_stats_options], active=0,
                                                    visible=False)

        def update_functionality_options(attr, old, new):
            for w in self.functionality_option_widgets:
                if w.visible:
                    w.visible = False
            funct_opt = self.functionality_options.get(self.functionality.value)
            if funct_opt is not None:
                funct_opt.visible = True

        self.username = TextInput(title="Nazwa użytkownika")
        self.search_word = TextInput(title="Poszukiwane słowo", height=300)
        self.date_from = DatePicker(title="Data początkowa", value=date.today() - datetime.timedelta(days=30), height=300)
        self.date_until = DatePicker(title="Data końcowa", value=date.today(), height=300)
        self.num_of_tweets = Select(title="Liczba tweetow", value='100', options=tweet_num_options, height=300)
        self.functionality = Select(title="Funkcjonalność", value="wordcloud", options=functionalities)
        self.functionality_options = {
            "wordcloud": None,
            "interconnections_network": self.inter_net_option_widgets,
            "user_stats": self.user_stats_option_widgets
        }
        self.functionality_option_widgets = [self.functionality_options.get(k) for k in self.functionality_options
                                             if self.functionality_options.get(k) is not None]
        self.functionality.on_change("value", update_functionality_options)
        self.refresh_button = Button(label="Załaduj tweety", button_type="default", width=150)
        self.refresh_button.on_event('button_click', self.update_display)
        self.export_button = Button(label="Zapisz do CSV", button_type="default", width=150)
        self.export_button.on_event('button_click', self.save_to_csv)
        self.export_button.disabled = True  # TODO remove once save_to_csv() is implemented
        self.columns = None

    def hide_display(self):
        self.display_container.children[0] = get_empty_element()

    def show_display(self, content):
        self.display_container.children[0] = content

    def show_error_message(self, message, title="Error"):
        error_dialog = Dialog(title=title, content=message)
        self.error_dialog_container.children[0] = error_dialog

    def update_display(self):
        try:
            display = self.create_display()
            if display is not None:
                self.show_display(display)
            else:
                self.hide_display()
        except Exception as e:
            self.hide_display()
            raise e

    def create_display(self):
        funct = self.functionality.value
        try:
            user_name = self.username.value
            search_words = self.search_word.value
            date_from = self.date_from.value
            date_to = self.date_until.value
            tweets_count = self.num_of_tweets.value
            tweets = Tweets(user_name, search_words, date_from, date_to, tweets_count)
            if funct == "wordcloud":
                words = tweets.get_wordcloud_words()
                if words is None:
                    self.show_error_message("Nie znaleziono żadnych tweetów dla podanych parametrów")
                    return None
                # TODO display word cloud
                print(f"{len(words)} words to display")
                p, _, _, _ = self.generate_test_figures()
                return p
            elif funct == "interconnections_network":
                option = self.inter_net_options[self.inter_net_option_widgets.active][1]
                data = tweets.get_interconnections_network()
                if data is None:
                    self.show_error_message("Nie znaleziono żadnych tweetów dla podanych parametrów")
                    return None
                vertices, edges = data
                # TODO display interconnections network graph
                print(f"Interconnections graph: {len(vertices)} vertices, {len(edges)} edges")
                _, q, _, _ = self.generate_test_figures()
                return q
            elif funct == "user_stats":
                option = self.user_stats_options[self.user_stats_option_widgets.active][1]
                stats = tweets.get_user_stats(option)
                if stats is None:
                    self.show_error_message("Nie znaleziono żadnych tweetów dla podanych parametrów")
                    return None
                labels, values = stats
                if option == UserStatsOptions.REACTIONS:
                    if len(values) == 0:
                        self.show_error_message("Nie znaleziono żadnych tweetów dla podanych parametrów")
                        return None
                    figure_title = "Reakcje na tweety"
                    r_tooltips = [
                        ("Statystyka", "@labels"),
                        ("Wartość", "@$name{0.00}"),
                    ]
                    legend_label = "Wartość"
                    x_label_orientation = math.pi / 12
                elif option == UserStatsOptions.TWEETS_PER_HOUR:
                    if len(values) == 0:
                        self.show_error_message("Nie znaleziono żadnych tweetów dla podanych parametrów")
                        return None
                    figure_title = "Godziny publikacji"
                    r_tooltips = [
                        ("Godzina", "@labels"),
                        ("Ilość tweetów", "@$name{0.00}"),
                    ]
                    legend_label = "Ilość tweetów"
                    x_label_orientation = None
                elif option == UserStatsOptions.HASHTAGS:
                    if len(values) == 0:
                        self.show_error_message("Znalezione tweety nie zawierają żadnych hasztagów")
                        return None
                    figure_title = "Hasztagi"
                    r_tooltips = [
                        ("Hasztag", "@labels"),
                        ("Ilość", "@$name{0.00}"),
                    ]
                    legend_label = "Ilość tweetów"
                    x_label_orientation = math.pi / 12
                else:
                    self.show_error_message("Nierozpoznana opcja")
                    return None

                data = {"labels": labels, "values": values}
                source = ColumnDataSource(data=data)
                y_max = max(values + [0]) * 1.2
                x_step = 0.4
                fig = figure(x_range=labels, y_range=(0, y_max), title=figure_title)

                fig.vbar(x=dodge('labels', 0, range=fig.x_range), top='values', source=source,
                         width=x_step, color="#e84d60", legend_label=legend_label, name='values')

                fig.x_range.range_padding = x_step / 2
                fig.xgrid.grid_line_color = None
                fig.legend.location = "top_left"
                if x_label_orientation is not None:
                    fig.xaxis.major_label_orientation = x_label_orientation
                fig.add_tools(HoverTool(tooltips=r_tooltips, formatters={'@Date': 'datetime'}))
                return fig
            else:
                self.show_error_message("Należy wybrać funkcjonalność")
                return None
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
                   x_axis_location=None, y_axis_location=None,
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
                   height=350)

        r.vbar(x=dodge('fruits', -0.25, range=r.x_range), top='2015', source=source,
               width=0.2, color="#c9d9d3", legend_label="2015", name='2015')

        r.vbar(x=dodge('fruits', 0.0, range=r.x_range), top='2016', source=source,
               width=0.2, color="#718dbf", legend_label="2016", name='2016')

        r.vbar(x=dodge('fruits', 0.25, range=r.x_range), top='2017', source=source,
               width=0.2, color="#e84d60", legend_label="2017", name='2017')

        r_tooltips = [
            ("Fruit", "@fruits"),
            ("Year", "$name"),
            ("Amount", "@$name"),
        ]

        r.x_range.range_padding = 0.1
        r.xgrid.grid_line_color = None
        r.legend.location = "top_left"
        r.legend.orientation = "horizontal"
        r.add_tools(HoverTool(tooltips=r_tooltips, formatters={'@Date': 'datetime'}))

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

        self.display_container = column(get_empty_element())

        dummy_dialog = Dialog(title="Error", content="An error occurred", visible=False)
        self.error_dialog_container = column(dummy_dialog)

        self.layout = layout(children=[
            row(Spacer(sizing_mode="stretch_both"),
                column(
                    # Spacer(width=1, sizing_mode="stretch_height"),
                    column(self.username, self.search_word, self.date_from, self.date_until,
                           self.num_of_tweets, self.functionality,
                           row(self.functionality_option_widgets),
                           row(self.refresh_button, self.export_button)),
                    # Spacer(width=1, sizing_mode="stretch_height"),
                    sizing_mode="stretch_height"),
                column(
                    Spacer(width=1, sizing_mode="stretch_height"),
                    self.display_container,
                    Spacer(width=1, sizing_mode="stretch_height"),
                    sizing_mode="stretch_height"),
                self.error_dialog_container,
                Spacer(sizing_mode="stretch_both"),
                sizing_mode="stretch_both")
        ], sizing_mode="stretch_both")

        curdoc().add_root(self.layout)
        curdoc().title = "Tweenspector"


def get_empty_element():
    return Spacer(width=0, height=0)


dash = Dashboard()
dash.do_layout()
