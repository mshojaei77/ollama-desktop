# AI and Machine Learning Fundamentals

## What is Machine Learning?

Machine learning is a subset of artificial intelligence that provides systems the ability to automatically learn and improve from experience without being explicitly programmed. Machine learning focuses on the development of computer programs that can access data and use it to learn for themselves.

## Types of Machine Learning

### Supervised Learning
Supervised learning is where you have input variables (x) and an output variable (y) and you use an algorithm to learn the mapping function from the input to the output. The goal is to approximate the mapping function so well that when you have new input data (x), you can predict the output variables (y) for that data.

### Unsupervised Learning
Unsupervised learning is where you only have input data (x) and no corresponding output variables. The goal in unsupervised learning is to model the underlying structure or distribution in the data in order to learn more about the data.

### Reinforcement Learning
Reinforcement learning is a type of machine learning where an agent learns to behave in an environment by performing actions and seeing the results. The agent receives rewards or penalties for the actions it performs and its goal is to maximize the total reward.

## Deep Learning

Deep learning is a subset of machine learning that uses neural networks with multiple layers (deep neural networks) to analyze various factors of data. Deep learning is what's behind many recent advancements in AI, including:

- Image and speech recognition
- Natural language processing
- Autonomous vehicles
- Medical discoveries

## Large Language Models (LLMs)

Large Language Models like GPT-4, LLaMA, and Claude are transformer-based neural networks trained on vast amounts of text data. These models can:

1. Generate human-like text
2. Translate between languages
3. Write different kinds of creative content
4. Answer questions in an informative way

The key innovations behind modern LLMs include:
- Transformer architecture
- Self-attention mechanisms
- Unsupervised pre-training followed by supervised fine-tuning
- Scaling laws showing performance improvements with model size

Signal Quality Checks (SQC)
Channels Connection
1.	Common algorithms: The most common approach is to measure electrode impedance to assess connection quality. High contact impedance (e.g., >5 kΩ) indicates a poor connection (The electrode-skin contact impedance of wet ... - ResearchGate). Many EEG systems inject a small AC current (often at 1 kHz) and measure the impedance of each electrode ( Increasing Robustness of Brain–Computer Interfaces Through Automatic Detection and Removal of Corrupted Input Signals - PMC ). Another simple check is detecting channels that are "flatlined" or saturated at the amplifier's rails, which often indicates a lead off or short.
2.	Explanation & Complexity: Impedance measurement uses Ohm's law: a known current yields a voltage proportional to impedance (constant time per channel). In software, detecting a disconnected channel can also be done by checking signal variance – a floating (disconnected) electrode often shows abnormally high noise or zero variance if shorted to reference. This computation is trivial (O*N samples per channel). For example, Dunlap et al. measure each channel's impedance and note that anomalies (very high or zero impedance) reflect broken or shorted leads ( Increasing Robustness of Brain–Computer Interfaces Through Automatic Detection and Removal of Corrupted Input Signals - PMC ). Similarly, a channel stuck at a constant value is clearly disconnected (A multimodal driver monitoring benchmark dataset for driver ... - Nature).
3.	Latest insights: Modern EEG amplifiers continuously monitor impedance and can warn of bad contacts in real time. Recent research suggests combining impedance with signal metrics (variance, line noise) for robust detection ( Increasing Robustness of Brain–Computer Interfaces Through Automatic Detection and Removal of Corrupted Input Signals - PMC ) ( Increasing Robustness of Brain–Computer Interfaces Through Automatic Detection and Removal of Corrupted Input Signals - PMC ). If impedance checks are not available, using multi-feature algorithms (e.g., variance + correlation with other channels) can improve detecting bad connections automatically.

Signal Uniqueness
1.	Common algorithms: Cross-correlation analysis is widely used to ensure each channel carries unique information. A very high correlation between two channels (e.g. >0.9) suggests they are redundant or one is a copy of another (possibly due to electrodes touching or a wiring short) ( Increasing Robustness of Brain–Computer Interfaces Through Automatic Detection and Removal of Corrupted Input Signals - PMC ). Researchers also use mutual information or coherence between channels as measures of uniqueness, but Pearson correlation is the simplest and most common metric.
2.	Explanation & Complexity: Computing pairwise correlation between 24 channels requires calculating a 24×24 correlation matrix (O(Nchan²·Ntime) which is easily manageable). If any pair's absolute correlation is abnormally high, one of the channels may be considered non-unique. For example, in a high-density array, abnormal near-unity correlation between two channels indicates one signal "is essentially being copied onto another" ( Increasing Robustness of Brain–Computer Interfaces Through Automatic Detection and Removal of Corrupted Input Signals - PMC ). Conversely, a channel that correlates too low with all others may be just noise (see Defective Channel).
3.	Latest insights: Beyond simple correlation, recent work suggests using RANSAC-based interpolation and checking the correlation of each channel with a reconstruction from neighbors (as in the PREP pipeline) (How To Reduce Noise In EEG Recordings [11 Solutions] | Mentalab). This can more robustly flag an electrode that is not contributing unique brain signals. In practice, ensuring a common reference and proper electrode placement helps maintain appropriate inter-channel correlations (too high or too low correlation can both signal issues (Automated Methods for EEG Artifact Removal) (Automated Methods for EEG Artifact Removal)).

Signal Scale
1.	Common algorithms: A basic quality check is verifying the amplitude scale of each channel is within expected ranges. This is often done by thresholding the signal's peak-to-peak or standard deviation. For scalp EEG, typical amplitudes are tens of µV; a channel with an amplitude of several hundred µV or virtually zero µV is suspect. Many artifact rejection methods use amplitude thresholds (e.g. ±75 µV for blinks) as a first pass (Automated Methods for EEG Artifact Removal) (Automated Methods for EEG Artifact Removal).
2.	Explanation & Complexity: Computing the signal's variance or peak-to-peak range for each channel (O*N) and comparing against normative values or against other channels is straightforward. Abnormally large variance usually means motion or drift, and abnormally low variance means a flat signal. Radüntz et al. note that large shifts in the EEG's mean (DC offset) or huge amplitude swings typically indicate amplifier drift or electrode artifact ( Quality Assessment of Single-Channel EEG for Wearable Devices - PMC ) ( Quality Assessment of Single-Channel EEG for Wearable Devices - PMC ). In practice, a simple algorithm might compute each channel's RMS and flag channels outside [median ±3×MAD] (median absolute deviation).
3.	Latest insights: Modern methods use robust statistics (median, kurtosis) rather than simple min/max to avoid false positives ( Quality Assessment of Single-Channel EEG for Wearable Devices - PMC ). For example, kurtosis can detect if a channel's distribution has extreme outliers (spikes) beyond normal EEG, complementing the scale check ( Quality Assessment of Single-Channel EEG for Wearable Devices - PMC ). Additionally, auto-rejection frameworks like FASTER combine normalized variance and median amplitude tests to automatically remove channels with outlying scale (How To Reduce Noise In EEG Recordings [11 Solutions] | Mentalab).

Tension Artifact (Muscle)
1.	Common algorithms: Muscle tension artifacts (EMG) are identified by their high-frequency content. A classic approach is to measure power in a high beta or gamma band (e.g. 25–50 Hz) and compare it to baseline. Brunner et al. introduced an algorithm that compares the 30 Hz-band power in short epochs to a local 3-min baseline; if an epoch's high-frequency power exceeds baseline by a factor (e.g. 4×), it is flagged as muscle artifact (Muscle artifacts in the sleep EEG: automated detection and effect on all-night EEG power spectra - PubMed) (Muscle artifacts in the sleep EEG: automated detection and effect on all-night EEG power spectra - PubMed). Another simple metric is the signal's kurtosis – muscle noise produces bursts that yield high kurtosis (heavy tails) compared to normal EEG ( Quality Assessment of Single-Channel EEG for Wearable Devices - PMC ).
2.	Explanation & Complexity: These algorithms typically filter or compute an FFT of the signal in the high-frequency band (O(N log N) for FFT or O(N) for filtering). The resulting power or RMS is then thresholded. Muscle artifacts are characterized by outlying high values of high-frequency activity relative to background (Muscle artifacts in the sleep EEG: automated detection and effect on all-night EEG power spectra - PubMed). By using a sliding window, one can detect transient EMG bursts in real time. For example, the 4-s epochs that exceed 4× the local 30 Hz power are marked as artifact in Brunner's method (Muscle artifacts in the sleep EEG: automated detection and effect on all-night EEG power spectra - PubMed) (Muscle artifacts in the sleep EEG: automated detection and effect on all-night EEG power spectra - PubMed).
3.	Latest insights: Recent research suggests using wavelet or spectral entropy methods to distinguish EMG from EEG more adaptively, but these remain signal-processing based. In practice, combining kurtosis and high-frequency RMS gives a reliable muscle artifact index (high kurtosis and high 30–100 Hz power = likely muscle) ( Quality Assessment of Single-Channel EEG for Wearable Devices - PMC ). Some systems also dedicate extra channels (e.g. EMG or accelerometers) to detect muscle or motion tension artifacts and then regress them out.

Defective Channel
1.	Common algorithms: A "defective" channel (one that isn't recording brain signals properly) is often caught by a combination of the above metrics: near-zero variance or flat signal, abnormally low correlation with all other channels, or consistently extreme noise. Automated methods like FASTER label a channel as bad if it deviates on any of several criteria (variance, correlation, Hurst exponent, etc.) beyond 3 SD (How To Reduce Noise In EEG Recordings [11 Solutions] | Mentalab). In practice, a completely flatlined channel or one dominated by noise (no recognizable EEG) is removed.
2.	Explanation & Complexity: Checking for a constant signal is trivial (e.g. standard deviation ~0). Low correlation with other channels is also a strong indicator: since true EEG signals have some spatial correlation, a channel that is uncorrelated with the rest is likely "off" (Automated Methods for EEG Artifact Removal) (Automated Methods for EEG Artifact Removal). For example, Schaefer et al. use the minimum average correlation of each channel as a metric – if a channel's mean correlation with all others is extremely low, it's deemed defective ( Increasing Robustness of Brain–Computer Interfaces Through Automatic Detection and Removal of Corrupted Input Signals - PMC ) ( Increasing Robustness of Brain–Computer Interfaces Through Automatic Detection and Removal of Corrupted Input Signals - PMC ). These computations (variance and correlation) are O(N) and O(N²) respectively and easily done in real-time for 24 channels.
3.	Latest insights: Modern EEG pipelines perform automatic bad-channel detection by combining metrics. For instance, the PREP pipeline uses a robust correlation method (RANSAC) to find outlier channels (How To Reduce Noise In EEG Recordings [11 Solutions] | Mentalab), and FASTER combines variance, correlation and other features in a z-score framework (How To Reduce Noise In EEG Recordings [11 Solutions] | Mentalab). The latest research also highlights using the Hurst exponent – a channel with signal characteristics far from the typical 0.7 Hurst of EEG is likely picking up non-EEG noise (Automated Methods for EEG Artifact Removal) (Automated Methods for EEG Artifact Removal) (e.g. a drifting or erratic channel). Thus, incorporating long-range dependence and other statistics can improve defective channel identification.

Power Scale
1.	Common algorithms: "Power scale" refers to the frequency-domain amplitude of the signal. A common check is to compute each channel's power spectral density (PSD) (using Welch's method or FFT) and ensure the overall power in each band is within expected limits. If one channel has drastically higher total power (or specific band power) than others, it may be problematic (Autoreject: Automated artifact rejection for MEG and EEG data - PMC). This is essentially a frequency-domain analog of the signal scale check.
2.	Explanation & Complexity: Computing PSD for each channel is O(N log N) per channel. Algorithms then compare metrics like total power 1–50 Hz, or bandwise power (delta, theta, etc.), across channels. Under normal operation, channels of a 24-channel EEG should have comparable broadband power (allowing for some region differences). A channel with an order-of-magnitude higher power (especially at all frequencies) likely has added noise. Nolan et al. explicitly included variance (total power) as one criterion for bad channels (Automated Methods for EEG Artifact Removal), and also assume neighboring channels should show highly correlated power distributions (Detection of Movement and Lead-Popping Artifacts in Polysomnography EEG Data).
3.	Latest insights: Newer methods suggest normalizing power by median across channels or using reference channels to detect outliers. If a certain frequency band is inflated on one channel (for example, excessive high-frequency power), it could be flagged. Ensuring the device's gain is properly calibrated for all channels is also crucial – modern EEG amplifiers rarely drift in gain, so large power scale inconsistencies often trace back to electrode issues or external noise.


