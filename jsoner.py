import json
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
from shapely.geometry import Point, Polygon

dir = 'C:/Users/djava/PycharmProjects/5GSmartCity/LiDAR data sets/'
data_files = [f[:-5] for f in os.listdir(dir) if f.endswith(".pcap")]
data_files = ['DATA_20200323_180424']

def jsoner(file_name):

    P_car = pd.read_csv(dir + file_name + '_frozenNotTensorRtBigGood.csv', names=["time", "objectID", "x", "y", "class"], skiprows=1)  # Read CSV file with timestamp, Object ID, x and y cordination and mode, 1 for pedestrian, 2 for cars and 3 for cyclists
    P_ped = pd.read_csv(dir + file_name + '_bigPed_pedestrians.csv', names=["time", "objectID", "x", "y", "class"], skiprows=1)  # Read CSV file with timestamp, Object ID, x and y cordination and mode, 1 for pedestrian, 2 for cars and 3 for cyclists
    loops = pd.read_csv(dir + 'loops.csv', names=["ID", "x", "y", "class"], skiprows=1)  # Read the Virtual Loop locations

    loops['x'] = (loops['x'] - np.mean(loops['x'])) / np.std(loops['x'])
    loops['y'] = (loops['y'] - np.mean(loops['y'])) / np.std(loops['y'])
    P_car['x'] = (P_car['x'] - np.mean(P_car['x'])) / np.std(P_car['x'])
    P_car['y'] = (P_car['y'] - np.mean(P_car['y'])) / np.std(P_car['y'])
    P_ped['x'] = (P_ped['x'] - np.mean(P_ped['x'])) / np.std(P_ped['x'])
    P_ped['y'] = (P_ped['y'] - np.mean(P_ped['y'])) / np.std(P_ped['y'])

    sol = 2

    loops_car = loops[loops["class"] == 2]
    if sol == 1:
        streets = []
        streetNo = len(loops_car['ID'].unique())
    else:
        streetNo = len(loops['ID'].unique())
        streets = {}

    if sol == 3:
        loopGroups = {
            1: [1, 9, 10, 11],
            2: [2, 8, 12],
            3: [3],
            4: [4, 5, 6, 7]
        }
    else:
        loopGroups = {
            1: 1,
            2: 2,
            3: 3,
            4: 4,
            5: 4,
            6: 4,
            7: 4,
            8: 2,
            9: 1,
            10: 1,
            11: 1,
            12: 2
        }

    if sol == 1:
        for k in range(streetNo):
            loop = np.array(loops_car[loops_car["ID"] == k + 1])
            # print(loop)
            street = Polygon(
                [(loop[0, 1], loop[0, 2]), (loop[1, 1], loop[1, 2]), (loop[2, 1], loop[2, 2]), (loop[3, 1], loop[3, 2])])
            streets.append(street)
    elif sol == 2:
        for k in range(streetNo):
            loop = np.array(loops[loops["ID"] == k + 1])
            # print(loop)
            street = Polygon(
                [(loop[0, 1], loop[0, 2]), (loop[1, 1], loop[1, 2]), (loop[2, 1], loop[2, 2]), (loop[3, 1], loop[3, 2])])
            streets[k + 1] = street
    else:
        for k in range(streetNo):
            loop = []
            for obstacle in loopGroups[k + 1]:
                loop.append(np.array(loops[loops["ID"] == obstacle]))
            # print(loop)

            corners = list()

            for pol in loop:
                for corner in pol:
                    corners.append((corner[1], corner[2]))
            street = Polygon(corners)
            streets.append(street)

    data = {}
    data['cars'] = []
    data['pedestrians'] = []
    noSource = 0
    noDestination = 0

    P = P_car.append(P_ped)

    for k in range(int(P_car[["objectID"]].max())):

        target = P_car[P_car["objectID"] == k]
        target = target.sort_values(['time'])

        # print(target)

        enter_flag = True
        exit_flag = True
        i = 0
        j = target.shape[0] - 1
        ID = file_name + '_' + ((target["objectID"].iloc[[0]]).to_string(index=False)).strip()
        enter_time = ((target["time"].iloc[[0]]).to_string(index=False)).strip()
        exit_time = ((target["time"].iloc[[-1]]).to_string(index=False)).strip()
        duration = str(round((float(exit_time) - float(enter_time)), 4))

        tracks = list()
        for index, row in target.iterrows():
            x = row['x']
            y = row['y']
            point = Point(x, y)

            if sol == 1:
                idx = 1
                for street in streets:
                    if street.contains(point):
                        # print("found")
                        tracks.append(idx)
                    idx += 1
            else:
                for idx, pol in streets.items():
                    if pol.contains(point):
                        tracks.append(loopGroups[idx])

        # print(tracks)

        source = -1
        destination = -1

        for station in tracks:
            if source < 0:
                source = station
            elif destination < 0:
                if station != source:
                    destination = station
            else:
                break

        if source < 0:
            source = ''
            noSource += 1

        if destination < 0:
            destination = ''
            noDestination += 1
        # print(tracks)
        # print(source," ",destination)
        data['cars'].append({
            'ID': ID,
            'enter_st_id': source,
            'exit_st_id': destination,
            'enter_time': enter_time,
            'exit_time': exit_time,
            'duration': duration
        })

    # pedestrians

    noSourceP = 0
    noDestinationP = 0

    for k in range(int(P_ped[["objectID"]].max())):

        target = P_ped[P_ped["objectID"] == k]
        target = target.sort_values(['time'])

        enter_flag = True
        exit_flag = True
        i = 0
        j = target.shape[0] - 1
        ID = file_name + '_' + ((target["objectID"].iloc[[0]]).to_string(index=False)).strip()
        enter_time = ((target["time"].iloc[[0]]).to_string(index=False)).strip()
        exit_time = ((target["time"].iloc[[-1]]).to_string(index=False)).strip()
        duration = str(round((float(exit_time) - float(enter_time)), 4))

        # print(target)

        tracks = list()
        for index, row in target.iterrows():
            x = row['x']
            y = row['y']
            point = Point(x, y)

            if sol == 1:
                idx = 1
                for street in streets:
                    if street.contains(point):
                        # print("found")
                        tracks.append(idx)
                    idx += 1
            else:
                for idx, pol in streets.items():
                    if pol.contains(point):
                        tracks.append(loopGroups[idx])

        # print(tracks)

        source = -1
        destination = -1

        for station in tracks:
            if source < 0:
                source = station
            elif destination < 0:
                if station != source:
                    destination = station
            else:
                break

        if source < 0:
            source = ''
            noSourceP += 1

        if destination < 0:
            destination = ''
            noDestinationP += 1

        data['pedestrians'].append({
            'ID': ID,
            'enter_cw_id': source,
            'exit_cw_id': destination,
            'enter_time': enter_time,
            'exit_time': exit_time,
            'duration': duration
        })

    with open('{}_CarPedsDict.json'.format(file_name), 'w') as outfile:
        json.dump(data, outfile)

    print("About",(len(data['cars'])-noDestination)/len(data['cars'])*100, "%", " of cars have both source and destination according to the data.")
    print("About",(len(data['cars'])-noSource)/len(data['cars'])*100, "%", " of cars have at least source according to the data.")
    print("About",(len(data['pedestrians'])-noDestinationP)/len(data['pedestrians'])*100, "%", " of pedestrians crossed more than one street according to the data.")
    print("About",(len(data['pedestrians'])-noSourceP)/len(data['pedestrians'])*100, "%", " of pedestrians crossed at least one street according to the data.")
    print("We do not have enough information about %",noSourceP/len(data['pedestrians'])*100, "%", "of pedestrians according to the data.")

    plt.scatter(P_car['x'],P_car['y'],color='blue')
    plt.scatter(P_ped['x'],P_ped['y'],color='green')
    plt.scatter(loops['x'],loops['y'],color='red')
    plt.savefig('{}_Intersection.png'.format(file_name))
    plt.show()

    return

if __name__ == "__main__":
    for file in data_files:
        jsoner(file)
