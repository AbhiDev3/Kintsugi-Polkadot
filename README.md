# kintusgi-extras - Kintsugi Vault and Transfer Dashboard

This is a dashboard visualization of the squid created for tracking Kintsugi vaults and transfers utilizing Plotly's Dash package. *The Subsquid implementation used in the squid.py file can be found in the kintsugi-x branch of this repo along with an exploratory Jupyter Notebook for analyzing the data retrieved from the squid.*

## Getting Started

### Video Demo:
https://clipchamp.com/watch/BQg0UVDT6dC

### Running the app locally

Clone the repo to a local directory.

Create a virtual environment and activate it.

```
python -m venv venv

source venv/bin/activate
```

Install requirements with pip

```
pip install -r requirements.txt
```

Clone the git repo, then install the requirements with pip

Run the app and open it at http://127.0.0.1:8050/

```
python ./dash/app.py
```

## About the app

This dashboard shows the labelled vaults and total transfers by these vaults. It fetches data from a custom subsquid and creates a poor man's cache in the form of several CSV files. These must be deleted to fetch new data. The date range sets a distance from today's date in the graph and the statistics above the graph. The transfer data along with all labels is also shown in a table below the graph and can be exported to a CSV file.

## Built With

- [Subsquid](https://subsquid.io/) - Data sourcing via GraphQL
- [Dash](https://dash.plot.ly/) - Main server and interactive components
- [Plotly Python](https://plot.ly/python/) - Used to create the interactive plots

## Screenshots

![image](https://github.com/techsavage18/Kintsugi-Polkadot/assets/122214438/93925e1f-6c47-4406-bd78-50f53f703f8b)
![Screenshot 2023-05-12 002855](https://github.com/techsavage18/Kintsugi-Polkadot/assets/122214438/94b76ec2-ad66-49b1-8486-c406b623f0ae)
