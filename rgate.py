"""
A standalone HTTP server that operates as a gateway for redirecting
network traffic to the appropriate backend services (hosted on docker)
"""
#
# System Imports
#
import os
import yaml
import logging
import flask
import requests
import random
from flask import request
import docker
import click
import sqlite3


#
# Local Imports
#
from schemas import (
    Backend, BackendServices, DefaultResponse, ServiceResponse,
    ConnectionNotAvailable, BackendNotRunning, RequestsCount,
    LatencyMs, StatsResponse)
from sql import ExecSql


#
# Global Variables
#
app = flask.Flask(__name__)
DB_FILE_NAME = 'rgate.db'
db_conn = None
backend_services = BackendServices()


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    """
    Proxy function to capture all the traffic and redirect per requirements
    """
    if path.startswith('stats'):
        return fetch_rgate_stats_from_db()
    #
    # Proceeding with other routes
    #
    bknd_srv = get_bknd_service_for_path_prefix('/' + path)
    if bknd_srv:
        if not bknd_srv.service_urls:
            print("Backend available but not running")
            bkd_not_running = BackendNotRunning()
            update_db(bkd_not_running.status_code, 0)
            return bkd_not_running.dict()
        #
        # Proceeding with the happy path !!!
        #
        print("Serving request on any of the URLs: %s" % bknd_srv.service_urls)
        try:
            #
            # Round Robin selection of service URLs
            #
            if bknd_srv.service_url_to_pick < len(bknd_srv.service_urls) - 1:
                bknd_srv.service_url_to_pick += 1
            else:
                bknd_srv.service_url_to_pick = 0

            tp = bknd_srv.service_urls[bknd_srv.service_url_to_pick] + '/' + path
            print("The index am selecting is: %s" % bknd_srv.service_url_to_pick)
            print("Service URLs hitting is: %s" % tp)
            resp = requests.request(request.method, headers=request.headers,
                                    url=tp)
            # print("Response from backend is: %s" % resp.json())
            print("Time Elapsed in request: %s" % resp.elapsed.microseconds)
#            return_resp = ServiceResponse(
#                body=resp.json().get('message'),
#                status_code=resp.status_code)
            update_db(resp.status_code, resp.elapsed.microseconds)
            return (resp.text, resp.status_code, resp.headers.items())
        except requests.exceptions.ConnectionError as e:
            print("Connection not available to the backend: %s !!!"
                  % bknd_srv)
            cn_res = ConnectionNotAvailable()
            update_db(cn_res.status_code, 0)
            return cn_res.dict()
    else:
        def_res = DefaultResponse()
        update_db(def_res.status_code, 0)
        return def_res.dict()


#
# Utilities
#
def update_service_urls_per_labels():
    """
    Returns the service URLs for the input labels from docker
    """
    global backend_services
    client = docker.from_env()
    cntrs = client.containers.list()
    for each_cntr in cntrs:
        c_lbls = each_cntr.attrs['Config']['Labels']
        for e_bkd in backend_services.backends:
            if set(e_bkd.match_labels.items()).issubset(set(c_lbls.items())):
                #
                # Assumption - We pick the first port reflected in here
                #
                bkey = list(each_cntr.attrs['NetworkSettings']
                            ['Ports'].keys())[0]
                binfo = each_cntr.attrs['NetworkSettings']['Ports'][bkey][0]
                e_bkd.service_urls.append(
                    "http://%s:%s"
                    % (binfo.get('HostIp'), binfo.get('HostPort')))
    print("Backend services are: %s" % backend_services)
    return True


def get_bknd_service_for_path_prefix(path):
    """
    Returns the appropriate service in the available list of backends
    that matches the input path prefix
    """
    for bknd in backend_services.backends:
        if path.startswith(bknd.path_prefix):
            print("Returning Backend: %s for path_prefix: %s" % (bknd, path))
            return bknd
    print("Oops, No backend matched for the path: %s !!!" % path)
    return None


#
# DB Related
#
def create_connection(db_file):
    """
    create a database connection to the SQLite database
    specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    global db_conn
    try:
        db_conn = sqlite3.connect(db_file, check_same_thread=False)
        return True
    except Exception as e:
        print(e)
        return False


def exec_sql(input_sql, input_args=()):
    """
    create a table from the create_table_sql statement
    :param conn: Connection object
    :param input_sql statement
    :return:
    """
    try:
        c = db_conn.cursor()
        if input_args:
            c.execute(input_sql, input_args)
        else:
            c.execute(input_sql)
        return c
    except Exception as e:
        print(e)


def update_db(status_code, time_elapsed):
    """
    Updates the DB with the input object in the appropriate format
    :param input_obj
    :return boolean
    """
    sql = ExecSql.InsertRequestStats
    try:
        cur = db_conn.cursor()
        cur.execute(sql, (status_code, time_elapsed))
        db_conn.commit()
        return True
    except Exception as e:
        print(e)


def fetch_rgate_stats_from_db():
    """
    Returns the rgate stats from DB
    :param
    :return StatsResponse
    """
    sql_query = ExecSql.NthPercentileQuery
    #
    # 95th percentile
    #
    curr_95 = exec_sql(sql_query, (95,))
    percentile_95 = curr_95.fetchone()[0]
    #
    # 99th percentile
    #
    curr_99 = exec_sql(sql_query, (99,))
    percentile_99 = curr_99.fetchone()[0]
    print("Percentiles calculated: %s and %s"
          % (percentile_95, percentile_99))
    #
    # Statistics from DB
    #
    curr_stats = exec_sql(ExecSql.StatsQuery)
    total, s_count, avg = curr_stats.fetchone()
    print("Stats retrieved: 95th percentile: %s, 99th percentile: %s,"
          "Total: %s, success: %s and average: %s"
          % (percentile_95, percentile_99, total, s_count, avg))
    req_cnt = RequestsCount(
        success=s_count,
        error=total-s_count)
    lats = LatencyMs(
        average=avg,
        p95=percentile_95,
        p99=percentile_99)
    stats = StatsResponse(
        requests_count=req_cnt,
        latency_ms=lats)
    return stats.dict()


#
# CLI
#
@click.group(name="rgate")
def rgate():
    pass


def validate_file_path(ctx, param, value):
    """
    Validates if the input file path is available else raises and exception
    """
    if os.path.exists(value):
        return value
    else:
        print("Sorry, The config file path specified: %s doesn't exist !!!")


@rgate.command(
    name="rgate gateway for backend services",
    help="Listens on a specific port as an API gateway to the backend "
         "services")
@click.option("--port",
              help="The port on which rgate should listen",
              required=True,
              type=int)
@click.option("--config",
              callback=validate_file_path,
              help="Input configuration for rgate",
              required=True)
def rgate(port, config):
    print("Input attributes are: %s and %s" % (port, config))
    configs = {}
    with open(config, 'r') as fd:
        configs = yaml.load(fd)
    print("Input configs are: %s" % configs)
    #
    # Initialize Schemas
    #
    global backend_services
    global db_conn
    print("Backend services are: %s" % backend_services)
    for every_route in configs.get('routes'):
        #
        # Match Labels per Backend
        #
        match_labels = [
            each_bknd.get('match_labels')
            for each_bknd in configs.get('backends')
            if each_bknd.get('name') == every_route.get('backend')][0]
        print("Match labels are: %s" % match_labels)
        #
        # Initialize Backend now
        #
        backend = Backend(
            backend_name=every_route.get('backend'),
            path_prefix=every_route.get('path_prefix'),
            match_labels={k:v for k,v in (x.split('=') for x in match_labels)}
        )
        #
        # Append the backend service to master
        #
        backend_services.backends.append(backend)
    #
    # Lets fetch the service URLs from docker now
    #
    update_service_urls_per_labels()
    #
    # Let's initialize DB for request/response information now
    #
    if not create_connection(DB_FILE_NAME):
        raise Exception("Internal Error, check with admin for more details")

    exec_sql(ExecSql.CreateRgateTable)
    #
    # We have all the info we need now, moving on with serving on Http now
    #
    app.run(debug=True, host='0.0.0.0', port=port)


if __name__ == "__main__":
    logging.basicConfig()
    rgate()
