import json
import csv
import requests
from requests.auth import AuthBase
import hmac
import hashlib
import codecs
import os.path
from datetime import datetime
from datetime import timezone

filename = 'pessl_json.csv'

# Endpoint of the API, version for example: v1
apiURI = 'https://api.fieldclimate.com/v1'

# HMAC Authentication credentials
publicKey = 'ac696b8139646f6d330b5be3b845844c4b232e2f'
privateKey = '5188bcaabe41b925dff9783b77f6af223ca71304'

# Class to perform HMAC encoding
class AuthHmacMetosGet(AuthBase):
    # Creates HMAC authorization header for Metos REST service GET request.
    def __init__(self, apiRoute, publicKey, privateKey):
        self._publicKey = publicKey
        self._privateKey = privateKey
        self._method = 'GET'
        self._apiRoute = apiRoute

    def __call__(self, request):
        dateStamp = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
        print("timestamp: ", dateStamp)
        request.headers['Date'] = dateStamp
        msg = (self._method + self._apiRoute + dateStamp + self._publicKey).encode(encoding='utf-8')
        h = hmac.new(self._privateKey.encode(encoding='utf-8'), msg, hashlib.sha256)
        signature = h.hexdigest()
        request.headers['Authorization'] = 'hmac ' + self._publicKey + ':' + signature
        return request

'''Reads the existing csv file and finds the last timestamp that data was stored from'''
def find_last_date():

    file = codecs.open(filename, 'rU', 'utf-16')

    csv_reader = csv.reader(file, delimiter="\t", lineterminator="\n")

    i = 0
    for row in csv_reader:
        if i == 2:
            last_date = row[0]
            break
        i += 1

    file.close()

    print(last_date)

    return last_date

''' Reads the csv file (if one exists and is full - the existence is not checked here) and copies it into a matrix 
   so that new rows can be added at the top'''
def import_matrix():
    file = open(filename, 'r')

    csv_reader = csv.reader(file, delimiter=",", lineterminator="\n")

    n = 0
    m = 0
    for row in csv_reader:
        if n == 0:
            n = len(row)
        m += 1

    matrix = [[0 for x in range(n)] for y in range(m)]

    i = 0
    j = 0
    for row in csv_reader:
        matrix[i] = row
        i += 1

    print(matrix)

    file.close()

    return matrix

'''If no matrix exists, create one from the data that has just been read from fieldclimate'''
def create_matrix(sensor_data, dates):
    n = 1  # col count, stats at 1 to account for dates col
    for sensor in sensor_data:
        for key in sensor_data[sensor]['aggr']:
            if n == 1:
                m = len(sensor_data[sensor]['aggr'][key]) # number of rows needed for data
            n += 1

    m += 2  # account for the two header rows

    matrix = [[0 for x in range(n)] for y in range(m)] # Creates blank matrix

    # Can now populate the matrix with data
    i = 1
    j = 0
    matrix[i][j] = 'Date/Time'
    for date in dates:
        i += 1
        matrix[i][j] = date

    j += 1

    for sensor in sensor_data:
        i = 0
        matrix[i][j] = sensor_data[sensor]['name']

        for key in sensor_data[sensor]['aggr']:
            i = 1
            matrix[i][j] = key

            for value in sensor_data[sensor]['aggr'][key]:
                i += 1
                matrix[i][j] = value
            j += 1

    return matrix

'''Gets the data from fieldclimate using the API
   returns a response in json form'''
def get_data(last_date = 0):
    readData = '/data/optimized/00204E80/hourly/from/' + last_date

    print(readData)

    # Service/Route that you wish to call
    apiRoute = readData

    auth = AuthHmacMetosGet(apiRoute, publicKey, privateKey)

    response = requests.get(apiURI+apiRoute, headers={'Accept': 'application/json'}, auth=auth)

    return response

def write_to_csv(matrix):
    file = open(filename, 'a')

    csv_writer = csv.writer(file, delimiter=",", lineterminator="\n")

    for row in matrix:
        csv_writer.writerow(row)

    file.close()

########################################################################################################################


def main():
    file_exists = os.path.isfile(filename)

    if file_exists:
        last_date = find_last_date()
    response = get_data(last_date)
    data_parsed = response.json()     # Turns JSON object into a python dictionary of dictionaries

    print(data_parsed)

    sensor_data = data_parsed['data'] # Isolates the dictionary containing sensor data
    dates = data_parsed['dates']      # Isolates the dictionary containing the timestaps for each data point in data


    if file_exists():
        print('yoza')
    else:
        print('noza')
    #     matrix = import_matrix()
    #     append_new_data(matrix, sensor_data, dates)
    # else:
    #     matrix = create_matrix(sensor_data, dates)
    #
    # write_to_csv(matrix)

main()