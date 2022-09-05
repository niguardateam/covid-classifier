# <img src="./web_interface/static/logo_sub.png" width=600> 

# Summary

Welcome to the CLEARLUNG framework!
This package provides both clinical and radiomic analysis of lung CT scans. It was developed as a Master Thesis project.

Clinical features and metrics are extracted using techinques described [here](https://pubmed.ncbi.nlm.nih.gov/33567361/), while radiomic features are extracted and passed to a pre-trained classifier (reference [here](https://arxiv.org/abs/2109.13931)) to estimate the probability of COVID-19 versus other viral infections. 
All of the information is then printed on a PDF report for medical use.
The package also provides the possibility to connect to a local PACS node to retrieve exams, and to upload the generated output.

# Installation

`python 3.8+` is required.
First of all, clone the repository using you favourite connection option (SSH or HTTPS), for example

```bash
git clone git@github.com:niguardateam/covid-classifier.git
```
Then install the commands and requirements (possibly in a virtual environment):

```bash
cd covid-classifier
sudo pip3 install -e .
```
Note that the external package `dcm2niix` must be installed independently. If you are using MacOS, I suggest to download it from [Homebrew](brew.sh)
```bash
brew install dcm2niix
```
If you are using Linux, you can download it with
```bash
sudo apt-get install -y dcm2niix
```


# Usage


The CLEARLUNG package provides three main commands:
- `clearlung` is the core package and it is to be ran from the command line. The use of this command is not recommended as it is not easy to fully understand the command line options. However, to get more information just run `clearlung --help`
- `cleargui` is a wrapper of the above command, and it provides a web interface on your local browser. If you want to host the application on a specific port, run `cleargui -p PORTNUMBER` (deafult is 8000). After running the command, navigate to `localhost:8000` and use the graphical interface.
IMPORTANT: When you are done, remember to shut down the process with CTRL-C (not with CTRL-Z), otherwise you wil have to manually shutdown the port or the port will results as not available.
- `clearwatch path/to/folder` is only available on Linux. This command constantly monitors the folder passed as input argument. When a new folder is created inside of it, the CLEARLUNG pipeline automatically starts with default parameters.  

A help message explaining the commands can be accessed with the command
```bash
clearhelp
```


# Other

Contributions are always welcome. Please raise [issues](https://github.com/niguardateam/covid-classifier/issues) if you find any bugs or unexpected behaviour.

Special thanks to Prof. Stefano Carrazza ([@scarrazza](https://github.com/scarrazza)) for his tireless assistance and counseling in the making of this project.
