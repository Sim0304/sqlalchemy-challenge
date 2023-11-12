from flask import Flask, jsonify
import numpy as np
import pandas as pd
import datetime as dt
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text, inspect, func

# Create an SQLAlchemy engine to connect to your database
engine = create_engine("sqlite:///hawaii.sqlite")
Base = automap_base()
Base.prepare(autoload_with=engine)

# Create a Flask app
app = Flask(__name__)
Measurement = Base.classes.measurement
Station = Base.classes.station

# Define the homepage route
@app.route("/")
def homepage():
    return (
        "Welcome to the Climate App API!<br/>"
        "Available routes:<br/>"
        "/api/v1.0/precipitation<br/>"
        "/api/v1.0/stations<br/>"
        "/api/v1.0/tobs<br/>"
        "/api/v1.0/&lt;start&gt;<br/>"
        "/api/v1.0/&lt;start&gt/&lt;end&gt"
    )

# Define the /api/v1.0/precipitation route
@app.route("/api/v1.0/precipitation")
def precipitation():
    # Open session
    session = Session(engine)

    # Calculate the date one year from the latest date in the dataset
    latest_date = session.query(func.max(Measurement.date)).scalar()
    latest_date = dt.datetime.strptime(latest_date, '%Y-%m-%d')
    one_year_ago = latest_date - dt.timedelta(days=365)

    # Query precipitation data for the last 12 months
    Precipitation = session.query(Measurement.date, Measurement.prcp).filter(Measurement.date >= one_year_ago).all()

    # Close session
    session.close()

    # Convert the query results to a dictionary
    prcp_dict = {date: prcp for date, prcp in Precipitation}

    return jsonify(prcp_dict)

# Define the /api/v1.0/stations route
@app.route("/api/v1.0/stations")
def stations():

    # Open session
    session = Session(engine)

    # Query and return the list of stations
    station_list = session.query(Station.station).all()
    stations = [station for station, in station_list]

    # Close session
    session.close()

    return jsonify(stations)

# Define the /api/v1.0/tobs route
@app.route("/api/v1.0/tobs")
def tobs():

    # Open session
    session = Session(engine)

    # Determine the most active station
    most_active_station = session.query(Measurement.station, func.count(Measurement.station)).\
        group_by(Measurement.station).\
        order_by(func.count(Measurement.station).desc()).first()[0]
    

    # Calculate the date one year from the latest date in the dataset
    latest_date = session.query(func.max(Measurement.date)).scalar()
    latest_date = dt.datetime.strptime(latest_date, '%Y-%m-%d')
    one_year_ago = latest_date - dt.timedelta(days=365)

    # Query temperature observations for the most active station in the last 12 months
    tobs_data = session.query(Measurement.date, Measurement.tobs).filter(
        Measurement.station == most_active_station,
        Measurement.date >= one_year_ago
    ).all()

    # Close session
    session.close()

    return jsonify(tobs_data)

# Define the /api/v1.0/start and /api/v1.0/start/end routes
@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")
def temperature_stats(start, end=None):

    # Open session
    session = Session(engine)

    # Define a function to calculate temperature statistics
    def calculate_temperatures(start_date, end_date=None):
        if end_date is None:
            temp_stats = session.query(
                func.min(Measurement.tobs),
                func.max(Measurement.tobs),
                func.avg(Measurement.tobs)
            ).filter(Measurement.date >= start_date).all()
        else:
            temp_stats = session.query(
                func.min(Measurement.tobs),
                func.max(Measurement.tobs),
                func.avg(Measurement.tobs)
            ).filter(Measurement.date >= start_date, Measurement.date <= end_date).all()

        return temp_stats

    # Convert the provided start and end dates to datetime objects
    start_date = dt.datetime.strptime(start, '%Y-%m-%d')
    if end is not None:
        end_date = dt.datetime.strptime(end, '%Y-%m-%d')
    else:
        end_date = None

    # Calculate temperature statistics
    temperature_stats = calculate_temperatures(start_date, end_date)

    # Close session
    session.close()

    # Create a dictionary for the results
    temp_dict = {
        "start_date": start_date,
        "end_date": end_date,
        "TMIN": temperature_stats[0][0],
        "TMAX": temperature_stats[0][1],
        "TAVG": temperature_stats[0][2]
    }

    return jsonify(temp_dict)

if __name__ == "__main__":
    # Start the Flask app
    app.run(debug=True)
