import datetime

def read(filename):
    now = datetime.datetime(day=29, month=7, year=2016, hour=5).time()

    with open(filename, 'r') as cfg:
        data = [(datetime.time(int(h), int(m)), float(price)) for h, m, price in (line.split() for line in cfg)]

    data.sort(key=lambda x: x[0])

    for i in range(1, len(data)):
        time_a, time_b = data[i-1][0], data[i][0]

        if time_a <= now < time_b:
            return data[i-1][1]

    return data[-1][1]