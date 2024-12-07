#!/usr/bin/python3.11
# File to Analyze results from lab 5 for Radio Frequency at Harvey Mudd College (E157)
# Written by Kaitlin Lucio
 
import skrf as rf
import pandas as pd
from math import pi
import matplotlib; matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import argparse
import numpy as np
import os


def calc_rx_gain_from_sparams(s21: float, w, tx_gain, r, c=3*10**8, linear_gain: bool=False):
    """Returns the gain of a receiver from the s parameter s21, frequency, gain of the transmitting antenna, and the distance between antennas"""
    if not linear_gain:
        tx_gain = np.power(10, (tx_gain/10)) # Power gain, so 10x is 10 dB increase
    return np.power((8*np.pow(pi, 2)*np.abs(s21)*w*r/c), 2) * (1/tx_gain)


def calc_impedance_from_reflection_coeff(gamma, z0 = 50):
    """Calculates the gain from a reflection coefficient. z0 is 50 ohms by default"""
    return z0 * (1 + gamma) / (1 - gamma)

def main():
    # Parameters settable as inputs #TODO: Change this to an argparse
    # data_folder = "./tl-link"
    # tx_gain = 13.24 # dB
    data_folder = "./patch" # This is assumed to be the antenna name too
    tx_gain = 4.25 # dB
    linear_gain = False
    antenna_distance = 1.4

    # Extract data by finding number in angle and using that as angle of antenna (assumed degrees) relative to transmitter.
    # Use angle and S parameters to create large pandas dataframe of frequency vs sXX(angle) [ex s11(30)]
    filenames = os.listdir(data_folder)
    datafiles = [os.path.join(data_folder, file) for file in filenames if "S2P" in os.path.splitext(file)[1]]
    print(datafiles)
    s_param_df = pd.DataFrame()
    gains = []
    for i, datafile in enumerate(datafiles):
        print(f"Analyzing {datafiles[i]}")
        angle = os.path.splitext(os.path.basename(datafile))[0]
        print(f"Statistics for Angle {angle}")
        # Open s2p using skrf
        antenna = rf.Network(datafile)

        if "Frequency" not in s_param_df.index:
            s_param_df["Frequency"] = antenna.frequency.f

        s_11 = [s[0][0] for s in antenna.s]
        s_12 = [s[0][1] for s in antenna.s]
        s_21 = [s[1][0] for s in antenna.s]
        s_22 = [s[1][1] for s in antenna.s]
        s_param_df[f"{angle}_s11"] = np.abs(s_11)
        s_param_df[f"{angle}_s21"] = np.abs(s_21)
        s_param_df[f"{angle}_s12"] = np.abs(s_12)
        s_param_df[f"{angle}_s22"] = np.abs(s_22)
        
        # Calculate angle gain for all bins
        gain_list = []
        for i, freq in enumerate(s_param_df["Frequency"]):
            # print(freq/(2*pi))
            # print(calc_rx_gain_from_sparams(s_21[i], freq/(2*pi), tx_gain, linear_gain=linear_gain))
            gain_list += [calc_rx_gain_from_sparams(s_21[i], freq/(2*pi), tx_gain, antenna_distance, linear_gain=linear_gain)]

        # convert gain list to db if asked
        if not linear_gain:
            gain_list = [10*np.log10(gain) for gain in gain_list]
            
        # Save gain list for angle
        s_param_df[f"{angle}_gain"] = gain_list
        max_gain = max(s_param_df[f"{angle}_gain"])
        max_index = np.argmax(s_param_df[f"{angle}_gain"])
        impedance = calc_impedance_from_reflection_coeff(s_param_df[f"{angle}_s22"][max_index])
        
        gains += [(float(angle)*pi/180, max_gain)]
        if not linear_gain:
            print(f"  Max Gain for Angle in dBi: {max_gain}")
        else:
            print(f"  Max Gain for Angle in Linear Units: {max_gain}")
        print(f"  Impedance: {impedance}")

        # Add line break between each analysis
        print()



    
    # Plot S parameter for 0 degree case (assumed to be broadside) and save to file based on folder name
    fig = plt.figure(0)
    plt.plot('Frequency', '0_s11', data=s_param_df)
    plt.plot('Frequency', '0_s12', data=s_param_df)
    plt.plot('Frequency', '0_s21', data=s_param_df)
    plt.plot('Frequency', '0_s22', data=s_param_df)
    plt.xlabel("Frequency")
    plt.ylabel("Magnitude of S Parameter")
    plt.title(f"S Parameters of Broadside of Antenna {os.path.basename(data_folder)}")
    plt.legend(["S11", "S12", "S21", "S22"])
    plt.savefig(f"./{os.path.basename(data_folder)}_broadside_sparams")
    plt.close()

    # Create new dataframe with just best case gain for each angle, plot polar and save to file based on folder name

    # Add first entry to complete circle
    gains.sort()
    gains.append(gains[0])
    fig, ax = plt.subplots(subplot_kw={'projection': 'polar'})
    angles = [angle[0] for angle in gains]
    gain = [angle[1] for angle in gains]
    ax.plot(angles, gain)
    ax.grid(True)
    ax.set_title(f"Emission gain of Antenna {os.path.basename(data_folder)} in dBi")
    plt.savefig(f"./{os.path.basename(data_folder)}_emissions")
    plt.close()



if __name__ == "__main__":
    main()

