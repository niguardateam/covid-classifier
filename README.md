# <img src="./web_interface/static/logo_sub.png" width=600> 

This package provides both clinical and radiomic analysis of pulmonary CT scans.
Clinical features and metrics are extracted using techinques described [here](https://pubmed.ncbi.nlm.nih.gov/33567361/), while radiomic features are extracted and passed to a pre-trained classifier (reference [here](https://arxiv.org/abs/2109.13931)) to estimate the probability of COVID-19 versus other viral infections. 
All of the information is then printed on a PDF report for medical use.

Furthermore, this pakage is able to donwload lung CTs from a local PACS node, and to store the produced report onto the same node (with a different series number)

To install and use the package, after cloning the repo just run

```bash
cd covid-classifier
sudo pip install -e .
clearlung --help

To make a more friendly UI than the command line, I have developed a simple web interface to start and customize the pipeline. Note that `uvicorn` and `fastapi` must be installed in order to make it work properly, even though they are not strictly necessary to use this package. To start a web page with the UI run:

```bash
cd covid-classifier/web_interface
uvicorn servers:app --reload
```
And then navigaete with your default browser to `localhost:8000`.


Special thanks to Prof. Stefano Carrazza (@scarrazza) for his tireless assistance and counseling in the making of this project.
