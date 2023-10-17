"""Plot functions for ``analysis`` package."""
from pathlib import Path
from typing import Dict

import matplotlib
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np

from minis_validation.util import CURRENT, TIME

matplotlib.use('Agg')


def scaled_log1p(x, a, b):
    """Logarithmic function used for fitting the data."""
    return a * np.log1p(b * x)


def scaled_log1p_inv(x, a, b):
    """Inverse of ``scaled_log1p`` to get the input value from the reference."""
    return np.expm1(x / a) / b


def plot_traces_events(plot_dir: Path,
                       population_name: str,
                       traces_per_gid: Dict,
                       mark_NetCon_events: bool,
                       mark_peaks: bool):
    """Plot simulated traces (and optionally events and detected peaks).

    Save one plot per each gid in ``plot_dir`` under a name 'a<GID>.png'.

    Args:
        plot_dir: folder where save plots
        population_name: name of the population
        traces_per_gid: traces data
        mark_NetCon_events: whether to plot NetCon events
        mark_peaks: whether to plot peaks
    """
    plot_dir.mkdir(exist_ok=True, parents=True)
    for gid, trace in traces_per_gid.items():
        t = trace['trace'][:, TIME]
        i = trace['trace'][:, CURRENT]

        fig = plt.figure(figsize=(20, 5))
        ax = fig.add_subplot(1, 1, 1)
        ax.plot(t, i, color='black')
        if mark_NetCon_events:
            events = trace['events'][:, TIME]
            for event in events:
                ax.axvline(event, color='gray', lw=0.5, ls='--')
        if mark_peaks:
            peaks = trace['peaks']
            ax.plot(t[peaks], i[peaks], 'x', color='red')
        ax.set_ylabel('I_m (nA)')
        ax.set_xlabel('Time (ms)')
        ax.set_xlim(t[0], t[-1])
        fig.savefig(plot_dir / f'{population_name}_{gid}.png', bbox_inches='tight', dpi=100)
        plt.close(fig)


def plot_fitted_results(plot_dir: Path,
                        title: str,
                        input_freqs: np.ndarray,
                        minis_freqs_mean: np.ndarray,
                        minis_freqs_std: np.ndarray,
                        popt: np.ndarray,
                        ref_freq: float,
                        ref_freq_inv: float):
    """Plots fitted results.

    Args:
        plot_dir: where to save the plot
        title: title of the plot
        input_freqs: input frequencies
        minis_freqs_mean: mean minis frequencies from the simulations
        minis_freqs_std: standard deviations of minis frequencies
        popt: fitted parameter values
        ref_freq: experimental minis frequency from the reference paper
        ref_freq_inv: inverse of ``ref_freq`` in the fitted curve
    """
    plot_dir.mkdir(exist_ok=True, parents=True)

    fig = plt.figure(figsize=(9, 6))
    ax = fig.add_subplot()
    ax.set_title(title)
    ax.errorbar(input_freqs, minis_freqs_mean, yerr=minis_freqs_std, fmt='o')
    X = np.linspace(input_freqs[0], input_freqs[-1], 1000)
    Y = scaled_log1p(X, *popt)
    ax.plot(X, Y)

    log_equation = mpatches.Patch(label=f'y = {popt[0]:.3f} * np.log1p({popt[1]:.3f} * x)',
                                  linewidth=0, fill=False)
    ax.legend(handles=[log_equation], frameon=False)

    # display reference values at the middle of their corresponding lines
    ax.axhline(ref_freq, color='gray', lw=0.5)
    ax.text(X[len(X) // 2], ref_freq, f'{ref_freq:.3f}')
    ax.axvline(ref_freq_inv, color='gray', lw=0.5)
    ax.text(ref_freq_inv, Y[len(Y) // 2], f'{ref_freq_inv:.3f}')

    ax.set_xlabel('Input freq. [Hz]')
    ax.set_ylabel('Minis freq. [Hz]')
    fig.savefig(plot_dir / 'frequencies.png', bbox_inches='tight', dpi=120)
    plt.close(fig)
