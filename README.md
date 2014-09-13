Predicting Document Interest on Reddit
======================================

Identifying Interesting Documents for Reddit using Recommender Techniques

A Reddit agent that will automatically search the web for interesting text content to share to a
subreddit it has been trained on. The agent will make use of a number of machine learning and natural language 
processing techniques to achieve this goal.

Organistion
-----------

The source code is organised into folders as follows:
* src: source code for main code files related to the Recommender system.
* tools: source code for tools outside the scope of the Recommender system but used to download and extract post data from the Reddit API.
* figures: source code related to the generation of figures for this thesis.

Requirements
------------

The code is written for the standard CPython 2.7 interpeter. This is due to certain library requirements.

The following libraries are required (in pip format):

    nltk==2.0.4
    matplotlib==1.3.1
    numpy==1.8.1
    nose==1.3.3
    MySQL-python==1.2.5
    goose-extractor==1.0.20
    beautifulsoup4==4.3.2
    lxml==3.3.5
    argparse==1.2.1
    scikit-learn==0.14.1
    scipy==0.14.0
    requests==2.3.0

These should ideally be installed in a seperate [virtualenv](http://virtualenv.readthedocs.org/en/latest/) to prevent any previously installed libraries from influencing the runtime behavior.

Once a virtualenv has been setup and activated, the you can install the above libraries using the following command:

    pip install -r requirements.txt 
