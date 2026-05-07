import panda as pd
import numpy as np
df = pd.read_csv('gait_trial.csv')
print(df.head())
#x-axis
sampling_rate = 250
df['time'] = df.index / sampling_rate #calculating how long has passed
#y-axis
df['res_acc']=np.sqrt(df['ax']**2+df['ay']**2+df['az']**2)

from scipy.signal import find_peaks
peaks, properties = find_peaks(df['res_acc'],
                               height=100
                               distance=50)

ms_indices = []
for i in range(len(peaks)-1):
    start_search = peaks[i]
    end_search = peaks[i]+75
    window = df['res_acc'].iloc[start_search:end_search]
    ms_index=window.idxmin()
    ms_indices.append(ms_index)

to_indices = []
look_back_window = 88
for i in range(len(peaks)):
    ic_index = peaks[i]
    start_search = ic_index - look_back_window
    end-search = ic_index
    if start_search > 0:
    window = df['res_acc'].iloc[start_search:end_search]
    to_index = window.idmax()
    to_indices.append(to_index)


#visualization
import matplotlib.pyplot as plt
plt.figure(figsize=(10, 4))
plt.plot(df['time'],df['res_acc'], label='Resultant acceleration', color='black')

plt.plot(df['time'].iloc[peaks], df['res_acc'].iloc[peaks], "r^", label='Initial contact (IC)')
plt.plot(df['time'].iloc[ms_indices], df['res_acc'].iloc[ms_indices], "bo" , label='Mid stance (MS)')
plt.plot(df['time']iloc['to_indices'], df[res_acc]iloc['to_indices'], "gs" , label='Toes off (TO)')
plt.xlabel('Time(s)')
plt.ylabel('Acceleration(m/s^2)')
plt.title('Calibrated Gait data')
plt.legend
plt.tight_layout()
plt.show()
