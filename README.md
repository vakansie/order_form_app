# About 

Easily generate a csv file required by Dutch Passions wholesale order website by  
entering the order in a easy to use fancy smancy web app.  

## Build

Follow these steps to get this app running on your machine.

### Active the `venv` virtual environment

```
# From this directoy activate the virtual environment.
source .venv/bin/activate

# Install the required dependencies in the virtual env.
pip install -r requirements.txt
```

### Database

This app needs a database containing all the products from "Dutch Passions".  
It is not included and must be provided by the user as `products.db` in this  
directory.

For testing purposes one can copy the `products.db.sample` to `products.db`

## Running

```console
# Active the virtual env if you haven't done already
source .venv/bin/activate

# Fire up the app!
python Dutch_Passion_csv_Generator.py
```

