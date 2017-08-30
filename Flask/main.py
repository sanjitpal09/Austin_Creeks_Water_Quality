import os, requests, json
from flask import Flask, render_template
from flask_bootstrap import Bootstrap

app = Flask(__name__)
bootstrap = Bootstrap(app)

@app.route('/')
def index():
    from bokeh.plotting import figure, save
    from bokeh.models import (ColumnDataSource, HoverTool, LogColorMapper,GMapPlot,
                              GMapOptions, ColumnDataSource, Circle, DataRange1d, PanTool,
                              WheelZoomTool, BoxSelectTool)
    import numpy as np
    import json, requests
    from pandas.io.json import json_normalize
    import pandas as pd
    from bokeh.plotting import figure
    from bokeh.tile_providers import WMTSTileSource
    def query_site(url, params):
        # Queries the Water Quality Sample Data of data.austintexas.gov.
        # A json document is returned by the query.
        r = requests.get(url, params)
        print("Requesting", r.url)

        if r.status_code == requests.codes.ok:
            return r.json()
        else:
            r.raise_for_status()
    base_url = 'https://data.austintexas.gov/resource/v7et-4fvp.json?$limit=50000'
    params = {'parameter': 'E COLI BACTERIA', 'unit': 'MPN/100ML'}
    data = query_site(base_url, params)
    df = json_normalize(data)
    ecoli_df = ecoli_df = df[['sample_date','site_name','parameter','result','unit','lat_dd_wgs84','lon_dd_wgs84']]
    ecoli_df.rename(columns={'lat_dd_wgs84': 'latitude', 'lon_dd_wgs84': 'longitude'}, inplace=True)
    ecoli_df['sample_date'] = pd.to_datetime(ecoli_df['sample_date'])
    mask = (ecoli_df['sample_date'] > '2016-01-01')
    ecoli_df = ecoli_df.loc[mask]
    ecoli_df['result'] = ecoli_df['result'].astype('float64')
    ecoli_df['latitude'] = ecoli_df['latitude'].astype('float64')
    ecoli_df['longitude'] = ecoli_df['longitude'].astype('float64')
    ecoli_score = ecoli_df.groupby(['site_name']).mean()
    ecoli_score.reset_index(inplace=True)
    ecoli_score['x'] = ecoli_score['longitude']
    ecoli_score['y'] = ecoli_score['latitude']
    k = 6378137.0
    ecoli_score['x'] = ecoli_score['x'].apply(lambda x: (x*k * np.pi/180.0))
    ecoli_score['y'] = ecoli_score['y'].apply(lambda y: np.log(np.tan((90.0 + y) * (np.pi)/360.0))*k)
    ecoli_score['Unit']='MPN/100ML'
    ecoli_score_unsafe = ecoli_score.loc[ecoli_score['result'] > 400.0]
    ecoli_score_unsafe['Warning'] = 'Unsafe to Swim'
    ecoli_score_safe = ecoli_score.loc[ecoli_score['result'] <= 400.0]
    ecoli_score_safe['Warning'] = 'Safe to Swim'
    # Austin = ((-10898752, -10855820), (3525750, 3550837))
    USA = x_range,y_range = ((-10898752, -10855820), (3525750, 3550837))
    TOOLS="pan,wheel_zoom,zoom_in,zoom_out,box_zoom,undo,redo,reset,save,"

    fig = figure(title = "Water Quality Map (Here Red-Unsafe and Green-Safe)",tools=TOOLS, x_range=x_range, y_range=y_range,plot_width=1000, plot_height=800)
    fig.axis.visible = False
    url = 'https://maps.wikimedia.org/osm-intl/{Z}/{X}/{Y}@2x.png'
    attribution = "Map tiles by WikiMedia"
    fig.add_tile(WMTSTileSource(url=url, attribution=attribution))
    dfsource1 = ColumnDataSource(data=ecoli_score_safe)
    fig.circle('x', 'y',source=dfsource1,color="green" )
    dfsource2 = ColumnDataSource(data=ecoli_score_unsafe)
    fig.circle('x','y',source=dfsource2,color="red")
    hover = HoverTool(tooltips=[
    ("Site Name", "@site_name"),
    ("Ecoli_Level", "@result"),
    ("Unit", "@Unit"),
    ("Warning","@Warning")
    ])
    fig.add_tools(hover)
    output_file = 'templates/Ecoli.html'
    save(fig, output_file)
    return render_template('Ecoli.html')


if __name__ == '__main__':
    app.run(debug=True)
