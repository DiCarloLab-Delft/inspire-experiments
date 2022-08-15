from __future__ import annotations
from dataclasses import dataclass


import os
import time
import json

import numpy as np
from pathlib import Path
from datetime import datetime, date
from qiskit import Job

DEFAULT_DATA_DIR = './data/'
DEFAULT_PLOT_DIR = './plots/'

@dataclass
class ExperimentData():

    def __init__(self):
        self._data_dir = Path(DEFAULT_DATA_DIR)
        self._plot_dir = Path(DEFAULT_PLOT_DIR)
        self._data = None
        self._timestamp = date.today()

    @property
    def data_dir(self):
        return self._data_dir

    @data_dir.setter
    def data_dir(self, d: str | Path):
        self._data_dir = Path(d)

    @property
    def plot_dir(self):
        return self._plot_dir

    @plot_dir.setter
    def plot_dir(self, d: str | Path):
        self._plot_dir = Path(d)

    @property
    def timestamp(self):
        return self._timestamp

    @timestamp.setter
    def timestamp(self, t: str | datetime):
        if isinstance(t, str):
            self._timestamp = date.fromtimestamp(t)
        elif isinstance(t, datetime):
            self._timestamp = t
        else:
            raise ValueError("Wrong format for timestamp!")

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, d: np.ndarray):
        self._data = np.asarray(d)

    @property
    def counts(self):
        return self._counts

    @counts.setter
    def counts(self, d: dict):
        self._counts = d

    @classmethod
    def save_job_result(
            cls,
            job,
            exp_name: str,
            header: str=None,
            directory: str | Path=data_dir()
    ):
        np.savetxt(
            fname=directory / Path(exp_name + '_RAW.csv'),
            X=np.array(job.result().data()['memory_multiple_measurement']),
            delimiter=',',
            fmt='%s',
            header=header
        )

        with open(directory / Path(exp_name + '_PROB.json'), 'w') as f:
            f.write(header + '\n')
            f.write(json.dumps(job.result().get_probabilities_multiple_measurement()))

        with open(directory / Path(exp_name + '_COUNTS.json'), 'w') as f:
            f.write(header + '\n')
            f.write(json.dumps(job.result().data()['counts_multiple_measurement']))

        return job

    @classmethod
    def get_json_data(
            cls,
            filename: str | Path,
            comment: str='#',
            directory: str=data_dir()
    ):
        with open(directory / Path(filename), 'r') as f:
            data_str = [line for line in f.read().split('\n') if line[0] != comment]
            data_dict = json.loads(data_str[0])

        cls.counts(data_dict)
        cls.timestamp(time.ctime(os.path.getmtime(directory / Path(filename))))
        return data_dict

    @classmethod
    def get_csv_data(
            cls,
            filename: str,
            comment: str='#',
            single_qubit: bool=False,
            use_string_repr: bool=True,
            directory: str=data_dir()
    ):
        data_hex = np.loadtxt(directory + filename, comments=comment, dtype='<U3', delimiter=',')
        # create binary strings of length 5
        data_bin = np.array(list(map(lambda h: str(bin(int(h, 16)))[2:].zfill(5), data_hex.flatten()))).reshape(data_hex.shape)

        if not use_string_repr:
            # convert strings to arrays of binary integers, which creates an extra dimension in the data_bin array
            data_bin = np.array(map(lambda s: np.fromiter(s, dtype=int), data_bin.flatten())).reshape(data_hex.shape)

        if single_qubit:
            # if only one qubit is measured, just create integer 0s/1s
            # this will disregard any specific qubits in the 1-state and just return 1 if any one qubit was in 1-state
            # the lambda function produces a decimal representation of the binary (hex) string
            data_bin = np.array(list(map(lambda d: int(d, 16), data_hex.flatten()))).reshape(data_hex.shape)
            data_bin = (data_bin > 0).astype(int)

        cls.data(data_bin)
        cls.timestamp(time.ctime(os.path.getmtime(directory / Path(filename))))
        return data_bin