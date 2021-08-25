Job Config format
=================
Besides the file format, the filename of such file must follow the next pattern:
"config_<CELL_TYPE>_<SYN_MINIS>", where CELL_TYPE is for specifying cells like 'L23_PC'. SYN_MINIS
value must be either 'Inh' or 'Exc'. An example is `config_L23_PC_Exc.yaml`.
Description of the file content:

  ::

    reference: (str) The reference article from which the values are taken. Typically, main authors, year, journal and DOI.

    results: (yaml dict)
        frequency:
            mean: (float) Mean of minis frequency (in Hz) reported in the article.
            std: (sloat) Std of minis frequency (in Hz) reported in the article.
        amplitude: (yaml dict) If there is no such data in the article, the "amplitude" yaml dict
                    is omitted. Currently this is not used, but is kept here to enable comparison
                    with the minis amplitude distribution obtained from the sims.
            mean: (float) Mean of minis (mEPSC or mIPSC) amplitude (in pA) reported in the article.
            std: (float) Std of minis (mEPSC or mIPSC) amplitude (in pA) reported in the article.
        n: (int) Number of cells measured in the reference article.

    cells: (json dict) The type of cells where the measurements were performed in the reference
            article. Also the type of cells to be simulated.

    protocol: (yaml dict) Parameters of the experimental protocol used in the reference article,
              such as: holding voltage (hold_V, in mV), use of TTX (enable_ttx, always applied in
              experiments), and extracellular medium calcium concentration (calcium, in mM).
              Additionally here are presented purely simulation parameters like: duration of the
              simulation (t_stop, ms) and recording time interval (record_dt, ms). Ten seconds
              duration is typical so we get a good estimate of frequency (number of peaks/duration).
              Also, first second is discarded in analysis.
    analysis: (yaml dict) Analysis parameters taken from the reference paper. Currently, only the
              minimum peak height (detection threshold, in pA) based on SNR considerations in actual
              measurements. We use the same value when detecting peaks in the simulated signal,
              so it's comparable.

An example of such config:

  ::

    reference: "Brasier & Feldman 2008, J. Neurosci. (DOI: 10.1523/JNEUROSCI.3915-07.2008)"

    results:
        frequency:
            mean: 11.9
            std: 2.4
        amplitude:
            mean: 10.7
            std: 0.8
        n: 7

    cells: {"layer":4, "synapse_class":"EXC"}

    protocol:
        t_stop: 10000.0
        record_dt: 0.1
        hold_V: -90.0
        enable_ttx: true
        calcium: 2.5

    analysis:
        peak_min_height: 4.5

