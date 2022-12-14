import json
import plotly
import pandas as pd
import pickle
import os

from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from sklearn.base import BaseEstimator, TransformerMixin

from flask import Flask
from flask import render_template, request, jsonify
from plotly.graph_objs import Bar
from sqlalchemy import create_engine

import pathlib

project_directory = os.getcwd()
project_directory = pathlib.PurePath(project_directory)

app = Flask(__name__)

def tokenize(text):
    tokens = word_tokenize(text)
    lemmatizer = WordNetLemmatizer()

    clean_tokens = []
    for tok in tokens:
        clean_tok = lemmatizer.lemmatize(tok).lower().strip()
        clean_tokens.append(clean_tok)

    return clean_tokens

class TextLengthExtractor(BaseEstimator, TransformerMixin):
    """
    Customized class to add the length of text as a feature.
    This class is used in building model
    """

    def fit(self, x, y=None):
        return self

    def transform(self, X):
        X_length = pd.Series(X).apply(lambda x: len(x))
        return pd.DataFrame(X_length)

# load data
engine = create_engine('sqlite:///data/disaster_response.db')
df = pd.read_sql('SELECT * FROM messages_with_categories', engine)
categories = df.drop(columns = ['message', 'original', 'id', 'genre','child_alone'])

    
# load model
with open(project_directory / "models/preferred_pipeline.pickle", "rb") as f:
    model = pickle.load(f)

# index webpage displays cool visuals and receives user input text for model
@app.route('/')
@app.route('/index')
def index():
    
    # extract data needed for visuals
    genre_counts = df.groupby('genre').count()['message']
    genre_names = list(genre_counts.index)
    
    categories_counts = categories.sum(axis = 0).values
    categories_names = categories.columns

    request_counts = df.groupby('request').count()['message']
    request_names = ['no', 'yes']

    # create visuals
    graphs = [
        # first graph: the genre graph, with a bar layout
        {
            'data': [
                Bar(
                    x = genre_names,
                    y = genre_counts
                )
            ],

            'layout': {
                'title': 'Distribution of Message Genres',
                'yaxis': {
                    'title': "Count"
                },
                'xaxis': {
                    'title': "Genre"
                }
            }
        },
        # second graph: the distribution of request messages
        {
            'data': [
                Bar(
                    x = request_names,
                    y = request_counts
                )
            ],

            'layout': {
                'title': 'Distribution of Request messages',
                'yaxis': {
                    'title': "Count"
                },
                'xaxis': {
                    'title': "Request"
                }
            }
        },
        # third and last graph: the distribution of message categories
        {
            'data': [
                Bar(
                    x = categories_names,
                    y = categories_counts
                )
            ],

            'layout': {
                'title': 'Distribution of Message Categories',
                'yaxis': {
                    'title': "Count"
                },
                'xaxis': {
                    'title': "Category name"
                }
            }
        }
    ]
    
    # encode plotly graphs in JSON
    ids = ["graph-{}".format(i) for i, _ in enumerate(graphs)]
    graphJSON = json.dumps(graphs, cls=plotly.utils.PlotlyJSONEncoder)
    
    # render web page with plotly graphs
    return render_template('master.html', ids=ids, graphJSON=graphJSON)


# web page that handles user query and displays model results
@app.route('/go')
def go():
    # save user input in query
    query = request.args.get('query', '') 

    # use model to predict classification for query
    classification_labels = model.predict([query])[0]
    classification_results = dict(zip(df.columns[4:], classification_labels))

    # This will render the go.html Please see that file. 
    return render_template(
        'go.html',
        query = query,
        classification_result = classification_results
    )


def main():
    app.run(
        host = '0.0.0.0', 
        port = 3001, 
        debug = False)


if __name__ == '__main__':
    main()