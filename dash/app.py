# Import required libraries
from asyncio.log import logger
import logging
import pickle
import copy
import pathlib
import urllib.request
import dash
import math
import pandas as pd
import datetime as dt
import plotly.express as px
from datetime import datetime, timedelta
from dash.dependencies import Input, Output, State, ClientsideFunction
from dash import dcc, dash_table
from dash import html
from squid import fetch_kusama_transfers, fetch_transfers, fetch_vaults

# Multi-dropdown options
from controls import LABELS_FROM, LABELS_TO


# get relative data folder
PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("data").resolve()

app = dash.Dash(
    __name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}],
)
app.title = "Kintsugi Analytics"
server = app.server

# Create labels
from_label_options = LABELS_FROM
to_label_options = LABELS_TO


# Load squids data
try:
    kusama_transfers = pd.read_csv(
        DATA_PATH.joinpath("kusama_transfers.csv"),
        low_memory=False
    )
except Exception as e:
    print("Caching kusama transfers...")
    kusama_transfers = fetch_kusama_transfers() 
    kusama_transfers.to_csv(DATA_PATH.joinpath("kusama_transfers.csv"))

try:
    vaults = pd.read_csv(
        DATA_PATH.joinpath("vaults.csv"),
        low_memory=False
    )
except Exception as e:
    print("Caching vaults...")
    vaults = fetch_vaults() 
    vaults.to_csv(DATA_PATH.joinpath("vaults.csv"))

try:
    transfers_grouped = pd.read_csv(
        DATA_PATH.joinpath("transfers_grouped.csv"),
        low_memory=False
    )
    transfers_raw = pd.read_csv(
        DATA_PATH.joinpath("transfers_raw.csv"),
        low_memory=False
    )
    daddies = pd.read_csv(
        DATA_PATH.joinpath("daddies.csv"),
        low_memory=False
    )
except Exception as e:
    print("Caching transfers...")
    transfers_grouped, transfers_raw, daddies = fetch_transfers(vaults, kusama_transfers) 
    transfers_grouped.to_csv(DATA_PATH.joinpath("transfers_grouped.csv"))
    transfers_raw.to_csv(DATA_PATH.joinpath("transfers_raw.csv"))
    daddies.to_csv(DATA_PATH.joinpath("daddies.csv"))

df = transfers_raw[transfers_grouped.columns]

df["label_from_id"] = df["label_from_id"].apply(lambda x: x.split('/') if(pd.notnull(x)) else "none")
df["label_to_id"] = df["label_to_id"].apply(lambda x: x.split('/') if(pd.notnull(x)) else "none")
df.timestamp = pd.to_datetime(df.timestamp).dt.tz_localize(None)


def loading(loader_id: str, *children) -> dcc.Loading:
    """Wrap components with the loader."""
    return dcc.Loading(id=loader_id, children=children)

# Create app layout
app.layout = html.Div(
    [
        dcc.Store(id="aggregate_data"),
        # empty Div to trigger javascript file for graph resizing
        html.Div(id="output-clientside"),
        html.Div(
            [
                html.Div(
                    [
                        html.Img(
                            src=app.get_asset_url("kintsugi-logo.svg"),
                            id="kintsugi-image",
                            style={
                                "height": "60px",
                                "width": "auto",
                                "margin-bottom": "25px",
                            },
                        )
                    ],
                    className="one-third column",
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.H3(
                                    "Kintsugi Analysis",
                                    style={"margin-bottom": "0px"},
                                ),
                                html.H5(
                                    "AmsterDOT hackathon bounty", style={"margin-top": "0px"}
                                ),
                            ]
                        )
                    ],
                    className="one-half column",
                    id="title",
                ),
                html.Div(
                    [
                        html.A(
                            html.Button("Learn More", id="learn-more-button"),
                            href="https://docs.interlay.io/#/",
                            target="_blank",
                        )
                    ],
                    className="one-third column",
                    id="button",
                ),
            ],
            id="header",
            className="row flex-display",
            style={"margin-bottom": "25px"},
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.P(
                            "Historical days to fetch (select range in histogram):",
                            className="control_label",
                        ),
                        dcc.RangeSlider(
                            id="year_slider",
                            min=-(datetime.utcnow() - datetime(2022, 2, 15, 0)).days,
                            max=0,
                            value=[-30, 0],
                            className="dcc_control",
                        ),
                        html.P("Filter by from address label status:", className="control_label"),
                        dcc.RadioItems(
                            id="from_address_selector",
                            options=[
                                {"label": "All ", "value": "all"},
                                {"label": "Vaults only ", "value": "vault"},
                                {"label": "Customize ", "value": "custom"},
                            ],
                            value="vault",
                            labelStyle={"display": "inline-block"},
                            className="dcc_control",
                        ),
                        dcc.Dropdown(
                            id="well_statuses",
                            options=from_label_options,
                            multi=True,
                            value='@mafux777',
                            className="dcc_control",
                        ),
                        html.P("Filter by to address label status:", className="control_label"),
                        dcc.RadioItems(
                            id="to_address_selector",
                            options=[
                                {"label": "All ", "value": "all"},
                                {"label": "Vaults only ", "value": "vault"},
                                {"label": "Customize ", "value": "custom"},
                            ],
                            value="all",
                            labelStyle={"display": "inline-block"},
                            className="dcc_control",
                        ),
                        dcc.Dropdown(
                            id="well_types",
                            options=to_label_options,
                            multi=True,
                            value=to_label_options,
                            className="dcc_control",
                        ),
                    ],
                    className="pretty_container four columns",
                    id="cross-filter-options",
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(
                                    [html.H6(id="well_text"), html.P("Total transfers")],
                                    id="wells",
                                    className="mini_container",
                                ),
                                html.Div(
                                    [html.H6(id="gasText"), html.P("KSM transfers")],
                                    id="gas",
                                    className="mini_container",
                                ),
                                html.Div(
                                    [html.H6(id="oilText"), html.P("kBTC transfers")],
                                    id="oil",
                                    className="mini_container",
                                ),
                                html.Div(
                                    [html.H6(id="waterText"), html.P("KINT transfers")],
                                    id="water",
                                    className="mini_container",
                                ),
                            ],
                            id="info-container",
                            className="row container-display",
                        ),
                        html.Div(
                            dcc.Loading(id='loading-1',
                                children=[html.Div(dcc.Graph(id='count_graph'))],
                                type='default'),
                            # [dcc.Graph(id ='count_graph')],
                            id="countGraphContainer",
                            className="pretty_container",
                        ),
                    ],
                    id="right-column",
                    className="eight columns",
                ),
            ],
            className="row flex-display",
        ),
        html.Div(
            [
                html.Div(
                    [dash_table.DataTable(
                        id="main_table", 
                        row_selectable="multi",
                        style_table={'overflowX': 'scroll'},
                        style_as_list_view=True,
                        style_header={'backgroundColor': 'white','fontWeight': 'bold'},
                        page_action="native",
                        filter_action="native",
                        sort_action="native",
                        page_current=0,
                        page_size=40,
                        export_format="csv",
                    )],
                    id="mainTableContainer",
                    className="pretty_container twelve columns"
                ),
            ],
        ),
        # html.Div(
        #     [
        #         html.Div(
        #             [dcc.Graph(id="main_graph")],
        #             className="pretty_container seven columns",
        #         ),
        #         html.Div(
        #             [dcc.Graph(id="individual_graph")],
        #             className="pretty_container five columns",
        #         ),
        #     ],
        #     className="row flex-display",
        # ),
        # html.Div(
        #     [
        #         html.Div(
        #             [dcc.Graph(id="pie_graph")],
        #             className="pretty_container seven columns",
        #         ),
        #         html.Div(
        #             [dcc.Graph(id="aggregate_graph")],
        #             className="pretty_container five columns",
        #         ),
        #     ],
        #     className="row flex-display",
        # ),
    ],
    id="mainContainer",
    style={"display": "flex", "flex-direction": "column"},
)


# Helper functions
def filter_dataframe(df, from_labels, to_labels, year_slider):
    filterer_from = df['from_id']==0
    filterer_to = df['from_id']==0
    for type in from_labels:
        if len(from_labels) == len(LABELS_FROM):
            filterer_from = [not elem for elem in filterer_from]
            break
        for i, row in df.iterrows():
            if filterer_from[i] == True:
                    continue
            try:
                filterer_from[i] = type in df.loc[i, "label_from_id"]
            except TypeError:
                filterer_from[i] = False
    for type in to_labels:
        if len(to_labels) == len(LABELS_TO):
            filterer_to = pd.Series([True for elem in filterer_to])
            break
        for i, row in df.iterrows():
            print("WOW!")
            if filterer_to[i] == True:
                    continue
            try:
                filterer_to[i] = type in df.loc[i, "label_from_id"]
            except TypeError:
                filterer_to[i] = False
    dff = df[
        filterer_from
        & filterer_to
        & (df["timestamp"] > datetime.now()+timedelta(days=year_slider[0]))
        & (df["timestamp"] < datetime.now()+timedelta(days=year_slider[1]))
    ]
    return dff


# Create callbacks
app.clientside_callback(
    ClientsideFunction(namespace="clientside", function_name="resize"),
    Output("output-clientside", "children"),
    [Input("count_graph", "figure")],
)


@app.callback(
    Output("aggregate_data", "data"),
    [
        Input("well_statuses", "value"),
        Input("well_types", "value"),
        Input("year_slider", "value"),
    ],
)
def update_production_text(well_statuses, well_types, year_slider):
    dff = filter_dataframe(df, well_statuses, well_types, year_slider)
    ksm = dff.ksm.sum()
    kbtc = dff.kbtc.sum()
    kint = dff.kint.sum()
    return [ksm, kbtc, kint]


# Radio -> multi
@app.callback(
    Output("well_statuses", "value"), [Input("from_address_selector", "value")]
)
def display_status(selector):
    if selector == "all":
        return from_label_options
    elif selector == "vault":
        return ["@mafux777", "pumpernickel"]
    return []


# Radio -> multi
@app.callback(Output("well_types", "value"), [Input("to_address_selector", "value")])
def display_type(selector):
    if selector == "all":
        return to_label_options
    elif selector == "vault":
        return ["@mafux777", "pumpernickel"]
    return []


# # Slider -> count graph
# @app.callback(Output("year_slider", "value"), [Input("count_graph", "selectedData")])
# def update_year_slider(count_graph_selected):

#     if count_graph_selected is None:
#         return [-50, 0]

#     nums = [int(point["pointNumber"]) for point in count_graph_selected["points"]]
#     return [min(nums) + 1960, max(nums) + 1961]


# Selectors -> well text
@app.callback(
    Output("well_text", "children"),
    [
        Input("well_statuses", "value"),
        Input("well_types", "value"),
        Input("year_slider", "value"),
    ],
)
def update_well_text(well_statuses, well_types, year_slider):

    dff = filter_dataframe(df, well_statuses, well_types, year_slider)
    return dff.shape[0]


@app.callback(
    [
        Output("gasText", "children"),
        Output("oilText", "children"),
        Output("waterText", "children"),
    ],
    [Input("aggregate_data", "data")],
)
def update_text(data):
    return round(data[0],2), round(data[1], 5), round(data[2], 2)

# Selectors -> main table filter
@app.callback(
    [
        Output("main_table", "columns"),
        Output("main_table", "data"),
    ],
    [
        Input("well_statuses", "value"),
        Input("well_types", "value"),
        Input("year_slider", "value"),
    ],
)
def filter_table(well_statuses, well_types, year_slider):
    dff = filter_dataframe(df, well_statuses, well_types, year_slider)
    dff['label_from_id'] = dff['label_from_id'].astype(str)
    dff['label_to_id'] = dff['label_from_id'].astype(str)
    # dff = dff[['from_id', 'fromChain', 'to_id', 'toChain', 'kint', 'ksm', 'kbtc', 'timestamp']] 
    cols = [{"name": i, "id": i} for i in dff.columns]
    data = dff.to_dict('records')
    return [cols, data]

    # # table = dff.to_dict('records'), [{"name": i, "id": i} for i in df.columns]
    # dff.reset_index(level=0, inplace=True)
    # dff.rename(columns={'index':'col_name'}, inplace=True)
    # return dff.to_json(date_format='iso', orient='split')
    # return table


# # Selectors -> main graph
# @app.callback(
#     Output("main_graph", "figure"),
#     [
#         Input("well_statuses", "value"),
#         Input("well_types", "value"),
#         Input("year_slider", "value"),
#     ],
#     [State("main_graph", "relayoutData")],
# )
# def make_main_figure(
#     well_statuses, well_types, year_slider, main_graph_layout
# ):

#     dff = filter_dataframe(df, well_statuses, well_types, year_slider)

#     traces = []
#     for well_type, dfff in dff.groupby("Well_Type"):
#         trace = dict(
#             type="scattermapbox",
#             lon=dfff["Surface_Longitude"],
#             lat=dfff["Surface_latitude"],
#             text=dfff["Well_Name"],
#             customdata=dfff["API_WellNo"],
#             name=WELL_TYPES[well_type],
#             marker=dict(size=4, opacity=0.6),
#         )
#         traces.append(trace)

#     # relayoutData is None by default, and {'autosize': True} without relayout action
#     if main_graph_layout is not None and selector is not None and "locked" in selector:
#         if "mapbox.center" in main_graph_layout.keys():
#             lon = float(main_graph_layout["mapbox.center"]["lon"])
#             lat = float(main_graph_layout["mapbox.center"]["lat"])
#             zoom = float(main_graph_layout["mapbox.zoom"])
#             layout["mapbox"]["center"]["lon"] = lon
#             layout["mapbox"]["center"]["lat"] = lat
#             layout["mapbox"]["zoom"] = zoom

#     figure = dict(data=traces, layout=layout)
#     return figure


# # Main graph -> individual graph
# @app.callback(Output("individual_graph", "figure"), [Input("main_graph", "hoverData")])
# def make_individual_figure(main_graph_hover):

#     layout_individual = copy.deepcopy(layout)

#     if main_graph_hover is None:
#         main_graph_hover = {
#             "points": [
#                 {"curveNumber": 4, "pointNumber": 569, "customdata": 31101173130000}
#             ]
#         }

#     chosen = [point["customdata"] for point in main_graph_hover["points"]]
#     index, gas, oil, water = produce_individual(chosen[0])

#     if index is None:
#         annotation = dict(
#             text="No data available",
#             x=0.5,
#             y=0.5,
#             align="center",
#             showarrow=False,
#             xref="paper",
#             yref="paper",
#         )
#         layout_individual["annotations"] = [annotation]
#         data = []
#     else:
#         data = [
#             dict(
#                 type="scatter",
#                 mode="lines+markers",
#                 name="Gas Produced (mcf)",
#                 x=index,
#                 y=gas,
#                 line=dict(shape="spline", smoothing=2, width=1, color="#fac1b7"),
#                 marker=dict(symbol="diamond-open"),
#             ),
#             dict(
#                 type="scatter",
#                 mode="lines+markers",
#                 name="Oil Produced (bbl)",
#                 x=index,
#                 y=oil,
#                 line=dict(shape="spline", smoothing=2, width=1, color="#a9bb95"),
#                 marker=dict(symbol="diamond-open"),
#             ),
#             dict(
#                 type="scatter",
#                 mode="lines+markers",
#                 name="Water Produced (bbl)",
#                 x=index,
#                 y=water,
#                 line=dict(shape="spline", smoothing=2, width=1, color="#92d8d8"),
#                 marker=dict(symbol="diamond-open"),
#             ),
#         ]
#         layout_individual["title"] = dataset[chosen[0]]["Well_Name"]

#     figure = dict(data=data, layout=layout_individual)
#     return figure


# # Selectors, main graph -> aggregate graph
# @app.callback(
#     Output("aggregate_graph", "figure"),
#     [
#         Input("well_statuses", "value"),
#         Input("well_types", "value"),
#         Input("year_slider", "value"),
#         Input("main_graph", "hoverData"),
#     ],
# )
# def make_aggregate_figure(well_statuses, well_types, year_slider, main_graph_hover):

#     layout_aggregate = copy.deepcopy(layout)

#     if main_graph_hover is None:
#         main_graph_hover = {
#             "points": [
#                 {"curveNumber": 4, "pointNumber": 569, "customdata": 31101173130000}
#             ]
#         }

#     chosen = [point["customdata"] for point in main_graph_hover["points"]]
#     well_type = dataset[chosen[0]]["Well_Type"]
#     dff = filter_dataframe(df, well_statuses, well_types, year_slider)

#     selected = dff[dff["Well_Type"] == well_type]["API_WellNo"].values
#     index, gas, oil, water = produce_aggregate(selected, year_slider)

#     data = [
#         dict(
#             type="scatter",
#             mode="lines",
#             name="Gas Produced (mcf)",
#             x=index,
#             y=gas,
#             line=dict(shape="spline", smoothing="2", color="#F9ADA0"),
#         ),
#         dict(
#             type="scatter",
#             mode="lines",
#             name="Oil Produced (bbl)",
#             x=index,
#             y=oil,
#             line=dict(shape="spline", smoothing="2", color="#849E68"),
#         ),
#         dict(
#             type="scatter",
#             mode="lines",
#             name="Water Produced (bbl)",
#             x=index,
#             y=water,
#             line=dict(shape="spline", smoothing="2", color="#59C3C3"),
#         ),
#     ]
#     layout_aggregate["title"] = "Aggregate: " + WELL_TYPES[well_type]

#     figure = dict(data=data, layout=layout_aggregate)
#     return figure


# # Selectors, main graph -> pie graph
# @app.callback(
#     Output("pie_graph", "figure"),
#     [
#         Input("well_statuses", "value"),
#         Input("well_types", "value"),
#         Input("year_slider", "value"),
#     ],
# )
# def make_pie_figure(well_statuses, well_types, year_slider):

#     layout_pie = copy.deepcopy(layout)

#     dff = filter_dataframe(df, well_statuses, well_types, year_slider)

#     selected = dff["API_WellNo"].values
#     index, gas, oil, water = produce_aggregate(selected, year_slider)

#     aggregate = dff.groupby(["Well_Type"]).count()

#     data = [
#         dict(
#             type="pie",
#             labels=["Gas", "Oil", "Water"],
#             values=[sum(gas), sum(oil), sum(water)],
#             name="Production Breakdown",
#             text=[
#                 "Total Gas Produced (mcf)",
#                 "Total Oil Produced (bbl)",
#                 "Total Water Produced (bbl)",
#             ],
#             hoverinfo="text+value+percent",
#             textinfo="label+percent+name",
#             hole=0.5,
#             marker=dict(colors=["#fac1b7", "#a9bb95", "#92d8d8"]),
#             domain={"x": [0, 0.45], "y": [0.2, 0.8]},
#         ),
#         dict(
#             type="pie",
#             labels=[WELL_TYPES[i] for i in aggregate.index],
#             values=aggregate["API_WellNo"],
#             name="Well Type Breakdown",
#             hoverinfo="label+text+value+percent",
#             textinfo="label+percent+name",
#             hole=0.5,
#             marker=dict(colors=[WELL_COLORS[i] for i in aggregate.index]),
#             domain={"x": [0.55, 1], "y": [0.2, 0.8]},
#         ),
#     ]
#     layout_pie["title"] = "Production Summary: {} to {}".format(
#         year_slider[0], year_slider[1]
#     )
#     layout_pie["font"] = dict(color="#777777")
#     layout_pie["legend"] = dict(
#         font=dict(color="#CCCCCC", size="10"), orientation="h", bgcolor="rgba(0,0,0,0)"
#     )

#     figure = dict(data=data, layout=layout_pie)
#     return figure



# Selectors -> histogram
@app.callback(
    Output("count_graph", "figure"),
    [
        Input("well_statuses", "value"),
        Input("well_types", "value"),
        Input("year_slider", "value"),
    ],
)
def make_histogram(well_statuses, well_types, year_slider):
    all_filter = [-(datetime.utcnow() - datetime(2022, 2, 15, 0)).days, 0]
    dff = filter_dataframe(df, well_statuses, well_types, all_filter)

    g = dff[["from_id", "timestamp", "toChain"]]
    g.index = g["timestamp"]
    g_2023 = g[g["toChain"] == 2023].resample("D").count()
    g_2092 = g[g["toChain"] == 2092].resample("D").count()
    g_2000 = g[g["toChain"] == 2000].resample("D").count()
    g = g.resample("D").count()
    display_g = pd.DataFrame(index = pd.date_range(start = (datetime.utcnow().date() + timedelta(days = all_filter[0])), end = datetime.utcnow().date()))
    display_2023 = pd.DataFrame(index = pd.date_range(start = (datetime.utcnow().date() + timedelta(days = all_filter[0])), end = datetime.utcnow().date()))
    display_2092 = pd.DataFrame(index = pd.date_range(start = (datetime.utcnow().date() + timedelta(days = all_filter[0])), end = datetime.utcnow().date()))
    display_2000 = pd.DataFrame(index = pd.date_range(start = (datetime.utcnow().date() + timedelta(days = all_filter[0])), end = datetime.utcnow().date()))
    display_g = display_g.join(g)
    display_2023 = display_2023.join(g_2023)
    display_2092 = display_2092.join(g_2092)
    display_2000 = display_2000.join(g_2000)

    colors = []
    # for i in range(all_filter[0], all_filter[1]):
    #     if i >= int(year_slider[0]) and i < int(year_slider[1]):
    #         colors.append("rgb(123, 199, 255)")
    #     else:
    #         colors.append("rgba(123, 199, 255, 0.2)")

    for i in range(-(datetime.utcnow() - display_g.index[0]).days, -(datetime.utcnow() - display_g.index[-1]).days +1):
        if i >= int(year_slider[0]) and i < int(year_slider[1]):
            colors.append({
                "2023": "rgb(240, 174, 6)",
                "2092": "rgb(6, 20, 45)",
                "2000": "rgb(245, 48, 60)",
            })
        else:
            colors.append({
                "2023": "rgba(240, 174, 6, 0.2)",
                "2092": "rgba(6, 20, 45, 0.2)",
                "2000": "rgba(245, 48, 60, 0.2)"
            })

    data = [
        dict(
            type="scatter",
            mode="markers",
            x=display_g.index,
            y=display_g["from_id"] / 2,
            name="Transactions",
            opacity=0,
            hoverinfo="skip",
        ),
        dict(
            type="bar",
            x=display_2023.index,
            y=display_2023["from_id"],
            name="Moonriver Txs",
            marker=dict(color= [color['2023'] for color in colors]),
            offsetgroup=1,
        ),
        dict(
            type="bar",
            x=display_2092.index,
            y=display_2092["from_id"],
            name="Kintsugi TXs",
            marker=dict(color= [color['2092'] for color in colors]),
            offsetgroup=1,
            base = display_2023["from_id"]
        ),
        dict(
            type="bar",
            x=display_2000.index,
            y=display_2000["from_id"],
            name="Karura TXs",
            marker=dict(color= [color['2000'] for color in colors]),
            offsetgroup=1,
            base=display_2023["from_id"] + display_2092["from_id"],
        ),
    ]

    layout = {}
    layout['barmode'] = 'group'
    layout["title"] = "Transactions by recipient chain"
    layout["dragmode"] = "select"
    # layout["showlegend"] = False
    layout["autosize"] = True

    figure = dict(data=data, layout=layout)
    return figure


# Main
if __name__ == "__main__":
    app.run_server(debug=True)
