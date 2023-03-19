import time
from datetime import datetime
from collections import defaultdict
import json


### Configuration block
MIN_ANGLE = 0
MAX_ANGLE = 360
ANGLE_STEP = 1
ANTENNAS_COUNT = 9
MEASUREMENTS_PER_ANGLE = 10
MEASUREMENTS_INTERVAL_SECONDS = 1
OUTPUT_FILE_PREFIX = 'training_measurements'

# if true then don't try to connect to the device
_DRY_RUN = False
### End of configuration block

if not _DRY_RUN:
    from pluto_beamformer import sdr, monopulse_angle


"""
This function is expected to return an array of N data arrays where N = ANTENNAS_COUNT
"""
def get_data_from_antennas():
    if _DRY_RUN:
        return [[] for _ in range(ANTENNAS_COUNT)]
    else:
        data = sdr.rx()

        return [
            data[i] for i in range(ANTENNAS_COUNT)
        ]


def calculate_angle_diff(antenna_i, antenna_j, raw_data):
    if _DRY_RUN:
        return 0
    else:
        data_i = raw_data[antenna_i]
        data_j = raw_data[antenna_j]
        return monopulse_angle(data_i, data_j)


def do_measurement_series():
    measurements = defaultdict(list)

    for n in range(MEASUREMENTS_PER_ANGLE):
        print('Measurement {}/{}...'.format(n+1, MEASUREMENTS_PER_ANGLE))

        # It is important to read the data from all the antennas simultaneously
        raw_data = get_data_from_antennas()

        for i in range(ANTENNAS_COUNT-1):
            for j in range(i+1, ANTENNAS_COUNT):
                angle_diff = calculate_angle_diff(i, j, raw_data)
                measurements[(i+1, j+1)].append(angle_diff)
                print('Angle diff between antennas {} and {} is measured as {}'.format(i+1, j+1, angle_diff))
        
        if n < MEASUREMENTS_PER_ANGLE-1:
            print('Waiting for {} second(s) for the next measurement...'.format(MEASUREMENTS_INTERVAL_SECONDS))
            time.sleep(MEASUREMENTS_INTERVAL_SECONDS)
            print('-----')

    return [
        {
            'antenna_i': key[0],
            'antenna_j': key[1],
            'angle_diffs': angle_diffs
        }

        for key, angle_diffs in measurements.items()
    ]


def save_data_to_file(data):
    now = datetime.now()

    file_name = '{}_{}.json'.format(
        OUTPUT_FILE_PREFIX,
        now.strftime('%Y%m%d_%H%M%S')
    )

    with open(file_name, 'w') as fp:
        json.dump(data, fp)
    
    print('=====')
    print('Measurement results are saved to {}'.format(file_name))


"""
The script runs measurement of phase difference for different angles
from <MIN_ANGLE> to <MAX_ANGLE> with step <ANGLE_STEP>.

For each input angle, measurements are performed <MEASUREMENTS_PER_ANGLE> times
with a time interval <MEASUREMENTS_INTERVAL_SECONDS>.

The measured data are saved to the file <OUTPUT_FILE_PREFIX>_<year><month><day>_<hour><minute><second>.json
in the following format:

[
    {
        "angle": 0,
        "measurements": [
            {"antenna_i": 1, "antenna_j": 2, "angle_diffs": [..., ..., ...]},
            {"antenna_i": 1, "antenna_j": 3, "angle_diffs": [..., ..., ...]},
            ...
        ]
    }
]
"""
if __name__ == '__main__':
    data = []

    for angle in range(MIN_ANGLE, MAX_ANGLE, ANGLE_STEP):
        if angle > MIN_ANGLE:
            print('\n')
        input('=== Please place the source at angle = {} degree(s) and press Enter when ready'.format(angle))

        measurements = do_measurement_series()
        data.append({
            'angle': angle,
            'measurements': measurements
        })

    save_data_to_file(data)