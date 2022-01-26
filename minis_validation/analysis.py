"""Analysis of results from ``simulation`` package."""
import re
from pathlib import Path
import logging
from typing import Dict

from click import progressbar
import h5py
import yaml
import numpy as np
import pandas as pd
from scipy.signal import find_peaks
from scipy.optimize import curve_fit

from minis_validation.plotting import (scaled_log1p, scaled_log1p_inv, plot_traces_events,
                                       plot_fitted_results)
from minis_validation.util import TIME, CURRENT

L = logging.getLogger(__name__)


def _parse_job_config_filename(job_config_filename: str):
    match = re.match(r'config_(?P<cell_type>\w+)_(?P<syn_type>(Exc)|(Inh)).yaml',
                     job_config_filename)
    if match is None:
        return None, None
    else:
        return match.group('cell_type'), match.group('syn_type')


def _parse_trace_filename(trace_filename: str):
    match = re.match(r'traces_freq(?P<frequency>[\d.]+).h5', trace_filename)
    if match is None:
        return None
    else:
        return float(match.group('frequency'))


def _save_results(save_dir: Path, input_freqs, mean_freqs, std_freqs, amplitudes, calcium):
    """Save results (matrices to .npz for reuse eg. plots and to table for better readability)."""
    save_dir.mkdir(exist_ok=True, parents=True)
    calcium = np.full_like(input_freqs, calcium)
    np.savetxt(save_dir / 'frequencies.tsv',
               np.vstack((calcium, input_freqs, mean_freqs, std_freqs)).T,
               fmt='%.3f',
               delimiter='\t',
               header='calcium\tinput_freq\tmean_freq\tstd_freq')
    np.savez(save_dir / 'frequencies.npz', input_freqs=input_freqs, mean_freqs=mean_freqs,
             std_freqs=std_freqs, **amplitudes)


def _load_traces(trace_file: Path, t_start: int = 0):
    """Loads in traces (and events) from h5 dump."""
    with h5py.File(trace_file, 'r') as h5f:
        assert 'traces' in h5f, f'Unexpected HDF5 layout of a trace file {trace_file}'
        traces_per_gid = {}
        for trace_h5 in iter(h5f['traces'].values()):
            gid = trace_h5.attrs['gid']
            trace = np.array(trace_h5['trace'])  # time, voltage, current
            events = np.array(trace_h5['events'])  # time, id
            if t_start != 0:
                t_idx = np.where(t_start < trace[:, TIME])[0]
                e_idx = np.where(t_start < events[:, TIME])[0]
            else:
                t_idx = slice(None)  # type: ignore  # use all
                e_idx = slice(None)  # type: ignore  # use all
            traces_per_gid[gid] = {'trace': trace[t_idx, :], 'events': events[e_idx, :]}
    return traces_per_gid


def _process_trace(trace, syn_type, peak_min_height):
    _is = np.copy(trace['trace'][:, CURRENT])
    _is -= np.mean(_is)  # remove mean tendency
    if syn_type == 'Exc':  # find_peaks looks for positive peaks
        _is *= -1
    peaks, peak_props = find_peaks(_is, height=peak_min_height / 1000)  # /1000 pA to nA conversion

    t = trace['trace'][:, TIME]
    len_sim = (t[-1] - t[0]) / 1000.  # ms to s conversion
    f_peaks = len(peaks) / len_sim  # number of peaks / sim length
    ampl_peaks = peak_props['peak_heights']  # amplitude distribution

    return f_peaks, ampl_peaks, peaks


def _analyze_frequency(trace_file: Path,
                       syn_type: str,
                       peak_min_height: float = None,
                       plot_traces: bool = False):
    # pylint: disable=too-many-locals
    """Analyzes a single file that holds a simulation data of one frequency of one job config.

    Args:
        trace_file: file of simulation output data
        syn_type: type of synapses, either 'Inh' or 'Exc'
        peak_min_height: a min peak height to detect peaks of cell's current
        plot_traces: whether to produce a traces plot

    Returns:
        a tuple if minis data: mean, std and amplitude of minis frequencies
    """
    frequency = _parse_trace_filename(trace_file.name)
    traces_per_gid = _load_traces(trace_file, t_start=1000)  # t_start =1000 to skip the 1st second
    traces = traces_per_gid.values()

    res = [_process_trace(trace, syn_type, peak_min_height) for trace in traces]
    nbad = 0
    f_peaks = []
    ampl_peaks = []
    for (f, ampl, peaks), trace in zip(res, traces):
        # sanity check detected peaks (e.g. voltage-clamp artifacts)
        if len(peaks) <= len(trace['events'][:, TIME]):
            trace['peaks'] = peaks  # save them for plotting or whatever...
            f_peaks.append(f)  # append frequency
            ampl_peaks.extend(ampl)  # append amplitude distribution
        else:
            nbad += 1
            trace['peaks'] = []
    if nbad > 0:
        L.warning('%d/%d traces didn\'t pass sanity check', nbad, len(traces))

    if plot_traces:
        plot_dir = trace_file.parent / 'analysis' / 'debug_' / f'{frequency:.3f}freq'
        plot_traces_events(plot_dir, traces_per_gid, frequency <= 0.01, True)

    # ampl_peaks*1000 is for nA to pA conversion
    return np.mean(f_peaks), np.std(f_peaks), np.asarray(ampl_peaks) * 1000.


def analyze_job(job_config_file: Path, job_traces_dir: Path) -> Dict:
    """Analyze results of a single job config.

    Analysis results are stored in 'analysis' folder within ``job_traces_dir``.

    Args:
        job_config_file: Path to a job YAML config file
        job_traces_dir: Path to a folder where stored simulations of a single job config

    Returns:
        Dictionary of analysis data
    """
    # pylint: disable=too-many-locals
    with job_config_file.open() as f:
        job_config = yaml.load(f, Loader=yaml.SafeLoader)
    cell_type, syn_type = _parse_job_config_filename(job_config_file.name)
    res = {}
    with progressbar(sorted(job_traces_dir.glob('*.h5')),
                     label=f'Analyzing {job_config_file}') as trace_files:
        for trace_file in trace_files:
            freq = _parse_trace_filename(trace_file.name)
            if freq is None:
                L.warning(('A trace file %s must be named as "traces_freq<some float number>.h5".' +
                           'Skipping'), trace_file)
            else:
                res[freq] = _analyze_frequency(trace_file, syn_type, **job_config['analysis'])
    if len(res.keys()) == 0:
        return {}

    input_freqs = np.fromiter(res.keys(), dtype=float)
    minis_freqs_mean = np.array([v[0] for v in res.values()])
    minis_freqs_std = np.array([v[1] for v in res.values()])
    minis_ampls = {f'ampl_{i}': v[2] for i, v in enumerate(res.values())}
    analysis_dir = job_traces_dir / 'analysis'

    # save results
    Ca = job_config['protocol']['calcium']
    _save_results(analysis_dir, input_freqs, minis_freqs_mean, minis_freqs_std, minis_ampls, Ca)

    # fit curve
    # pylint: disable=unbalanced-tuple-unpacking
    curve_fit_idx = 1 if input_freqs[0] == 0 else 0
    popt, _ = curve_fit(scaled_log1p,
                        xdata=input_freqs[curve_fit_idx:],
                        ydata=minis_freqs_mean[curve_fit_idx:],
                        p0=[10, 1],
                        sigma=minis_freqs_std[curve_fit_idx:])
    # find reference value
    ref_freq = job_config['results']['frequency']['mean']
    ref_freq_inv = scaled_log1p_inv(ref_freq, *popt)

    # plot results
    plot_fitted_results(analysis_dir,
                        job_traces_dir.name,
                        input_freqs,
                        minis_freqs_mean,
                        minis_freqs_std,
                        popt,
                        ref_freq,
                        ref_freq_inv)

    with (job_traces_dir / job_config_file.name).open('w') as f:
        job_config.update({'minis_frequency': float(ref_freq_inv)})
        yaml.dump(job_config, f, yaml.SafeDumper)

    return {
        'pathway': f'{cell_type}_{syn_type}',
        'ref_freq': ref_freq,
        'ref_std': job_config['results']['frequency']['std'],
        'Ca': Ca,
        'minis_freq': ref_freq_inv
    }


def analyze_jobs(jobs_configs_dir: Path, jobs_traces_dir: Path):
    """Analyze results of all job configs.

    Analysis results are stored in 'analysis' folder of the corresponding job's traces.

    Args:
        jobs_configs_dir: Path to a folder with YAML files describing experiment conditions.
        jobs_traces_dir: Path to a folder where stored results of all jobs simulations. This
            is ``output`` argument of ``simulation.run``.

    Returns:
        A dataframe of results
    """
    job_results = []
    for job_config_file in jobs_configs_dir.glob('*.yaml'):
        cell_type, syn_type = _parse_job_config_filename(job_config_file.name)
        if cell_type is None:
            L.warning(('%s must be named as "config_<CELL_TYPE>_<SYN_TYPE>.yaml where SYN_TYPE' +
                       ' must be either "Exc" or "Inh". Skipping.'), job_config_file.name)
        else:
            config_title = f'{cell_type}_{syn_type}'
            if (jobs_traces_dir / config_title).is_dir():
                job_results.append(analyze_job(job_config_file, jobs_traces_dir / config_title))
            else:
                L.warning('`job_config_file` %s must have a folder "%s" in `jobs_traces_dir` %s',
                          job_config_file, config_title, jobs_traces_dir)
    L.info('minis-validation analysis has been finished')
    job_results = pd.DataFrame(job_results)
    job_results.to_csv(jobs_traces_dir / 'job_results.csv', index=False)
    return job_results
