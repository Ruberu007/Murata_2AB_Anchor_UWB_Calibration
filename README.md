# Type 2AB Custom PCB UWB Calibration Tool

Offline Python desktop application for firmware diagnostic logs from a custom Murata LBUA5QJ2AB-828 PCB with two Taoglas UWC.20 antennas. It analyzes external PCB corrections for PDoA/AoA and DS-TWR ranging. It does not program firmware, registers or factory OTP.

## Double-click Windows application

Open the `dist` folder and double-click **UWB_Calibration.exe**. The executable bundles Python, Qt and all analysis dependencies; the receiving Windows 10/11 x64 computer does not need Python installed. You can copy this single executable to another folder or computer. It works offline and opens without a command window. The first launch can take several seconds while the bundled files extract to the Windows temporary folder.

Use **Load Demo Project** on the Project page to explore synthetic measurements, or create a real project and import your logs. Save projects to a writable folder such as Documents. Keep saved project JSON files separately from the executable.

The executable is unsigned. Windows may show a SmartScreen prompt for an unfamiliar downloaded program. An organization distributing this application can sign the executable with its own code-signing certificate.

To rebuild the executable from source on Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-build.txt
powershell -ExecutionPolicy Bypass -File .\build_exe.ps1
```

The repeatable PyInstaller configuration is `UWB_Calibration.spec`. Build output is `dist\UWB_Calibration.exe`. A packaged smoke check is `dist\UWB_Calibration.exe --demo --smoke-test`; it loads and analyzes the demo, then closes automatically. The source installation below remains available for development.

## Install and start (Windows 10/11)

Install Python 3.11 or newer, then open PowerShell in this directory:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

Activation is optional. Using the full interpreter path avoids PowerShell activation-policy issues. If `python` is a Windows Store alias, use `py -3` in the first command or the path to your installed Python.

```powershell
# Demo only: SYNTHETIC TEST DATA
.\.venv\Scripts\python.exe main.py --demo
# Open a saved project
.\.venv\Scripts\python.exe main.py --project examples\demo_project.json
# Automated tests
.\.venv\Scripts\python.exe -m pytest -q
# GUI launch/analysis smoke check
.\.venv\Scripts\python.exe main.py --demo --smoke-test
```

After dependencies are installed, no internet service, API key or OpenAI API is used. The project was verified on Python 3.14.6; its source requires Python 3.11 or later. Dependencies use lower version bounds so installers can select compatible wheels. For a reproducible installation of the verified environment, see `requirements-tested.txt`.

## Project and import workflow

The desktop interface uses a navy/teal RF workspace with numbered navigation on the left. Click **Working guide** in the header on any page for simple step-by-step instructions and explanations; the guide updates as you switch pages. Close it to give charts more room. Every chart includes a **How to read** caption, and its axis labels state the quantity and units. The guide explains all 14 plots and the meanings of phase, spread, timing, range error, power and first-path detection. Results appear in readable tables; complete structured values remain available in exports. Distance plots include ideal-reading and zero-error reference lines.

1. On **Project**, enter the project name, PCB revision, module, antenna, channel, calibration tag, operator and notes. Save to a local JSON file. Measurements are copied into the project, so loading does not require original logs.
2. On **Import Data**, choose `angle`, `distance` or `movement`, and select `EVB-EVB` or `EVB-CUSTOM`. For a fixed angle enter the known physical angle and distance (default 2.000 m). Import each log separately. Use a stationary sweep such as -60, -45, -30, -15, 0, +15, +30, +45 and +60 degrees.
3. Edit angle, distance, setup and enabled state in the dataset table. Click **Run Analysis / Refresh All Pages** after edits. Dataset names are unique on import. Removing a dataset changes the in-memory project; save when ready.
4. The parser recognizes timestamped firmware records, all requested raw diagnostic fields, diagnostic PDoA degrees and firmware-reported PDoA separately. Unknown fields are ignored. Missing fields produce warnings and empty values, rather than fabricated values.
5. `range=0x29` remains an opaque header token. The optional metres-per-code field only enables a linear conversion when you explicitly supply its scale. Leave it blank unless the firmware team confirms the encoding. Raw PDoA is also retained without guessing its conversion to degrees.
6. CSV input can include `timestamp`, `pdoa_deg`, `pdoa_raw`, `tdoa_raw`, `measured_distance_m` and any raw diagnostic fields. A `tdoa` column is accepted as an alias for `tdoa_raw`. Units for supplied distances must be metres.
7. **Raw Data** displays original fields and separate signed, unwrapped, corrected and validity columns. Click a column to sort. The text filter searches all columns. Rejected points remain in the table and full CSV export.

New Project, Load Project and Load Demo replace the current in-memory workspace. Save work before using them. Demo projects explicitly reject real-data imports to prevent mixing synthetic and measured data.

## Fixed angle calibration

### Save one RF file per angle and prepare final results

Open **Angle Capture Checklist (-180 to +180) / Prepare Final Results**. Set the sweep start/end and step (default 15 degrees; choose 1 for every integer angle). Click **Update angle checklist**, select the physical angle, and use **Import and save RF file for selected angle**. Import files such as `rf_angle_0Degree.txt` at their known physical angle; the app does not guess angles from filenames. The distance and EVB/custom setup use the Import Data controls. The checklist tracks custom-PCB captures; reference files are retained separately.

On the first capture choose a project JSON filename. Every capture is saved immediately, with the full original text embedded in the project and a copy in the adjacent `<project>_rf_captures` folder. Repeated captures at the same angle are retained rather than replaced. Load that JSON later to continue the sweep. Decimal values with parenthesized hexadecimal annotations are supported.

After collecting files, click **Prepare Final Results** and choose an output parent folder. A new result folder contains the saved project, original captures, all measurements, angle checklist, per-angle summary, calibration JSON and an HTML engineering report. A candidate LUT CSV/C header is included only when a LUT is available. Missing angles are listed; missing planned angles inside the selected LUT sector prevent readiness. Captures can be collected across multiple sessions. Existing captures survive changes to the planned step.

All -180 to +180 degree captures are analyzed as diagnostic data. Select a **LUT sector** (default -60 to +60 degrees) for AoA calibration. Two-antenna PDoA may have front/back ambiguity, and -180/+180 describe the same direction; a unique full-circle lookup cannot be assumed. A selected sector wider than 180 degrees emits no deployable LUT. A narrower sector still must pass monotonicity, stability and validation checks. Only a 0-degree file is enough to inspect zero-angle behavior, not to generate a final angle LUT.

Use **Fixed Angle Analysis** to select MAD (default), IQR or no filtering and linear or PCHIP interpolation. Run analysis to refresh all pages. The JSON settings editor lets you adjust thresholds, TDoA width and reference sign. Every threshold is a **PROJECT-SPECIFIC DEFAULT**, not a Murata specification.

The tab explains the selected filter and interpolation in plain English immediately below the controls. Select **Show explanations and current values for all settings** to view the meaning, units and effect of every numeric setting; scroll within that description. Click **Edit project-specific settings** to change values, then run analysis. The descriptions update when you change the filter or interpolation, load a project or edit settings.

Charts have their own **Plots** view; long numeric results are under **Statistics / details** so they cannot squeeze the plots. Use the short chart tabs (Raw PDoA, Corrected PDoA, etc.) and the plot toolbar to zoom, pan or save an image. An empty chart explains which measurements are needed. After saving captures in the angle checklist, click **Run Analysis / Refresh All Pages** or **Prepare Final Results** to display the latest captures.

MAD retains values within `threshold * 1.4826 * MAD` of the median. If MAD is zero, only values on the median plateau are retained. IQR keeps values in `[Q1 - threshold*IQR, Q3 + threshold*IQR]`. Filtering uses unwrapped phase for angle/movement datasets and measured range for distance datasets; missing calibration values are flagged separately. Motion diagnostics always examine the original full records, including rejected values. Filtering does not remove rows or change original values.

Per-dataset statistics include counts, phase/TDoA mean, median, sample SD, min, max, MAD and IQR; STS powers, first paths, F1/F2/F3, ratios/differences, timing differences and XTAL. A single sample has undefined sample SD. STS1 means the log's `sts` path and STS2 its `sts2` path; verify their correspondence to ANT1/ANT2 with your firmware team. Receive-time and FP-index differences are raw units, with no guessed timestamp rollover or physical-unit conversion. Raw power is **NOT dBm**.

Phase unwrapping operates in acquisition order, with missing samples splitting segments. It assumes adjacent phase changes are less than 180 degrees. Fixed-angle medians are also unwrapped across the sorted angle sweep, anchored to the zero-angle dataset. Sparse sweeps or long gaps can be ambiguous; inspect plots. The original phase, temporal unwrapped phase and angle-branch-corrected phase remain distinct.

At least one enabled **EVB-CUSTOM 0-degree** dataset is required. The robust filtered median gives the **CUSTOM PCB EXTERNAL PDOA OFFSET**. Equivalent phase branches across zero datasets are aligned before pooling. Correction is:

```
pdoa_corrected = unwrapped_pdoa - zero_offset
```

Spearman correlation and slope diagnose orientation against the configured reference sign (+1 by default). Reversed orientation suggests swapping logical ANT1/ANT2 or inverting PDoA in the coordinate transform. This is a recommendation, not proof of physical antenna reversal.

The angle median trajectory must be monotonic. Small local reversals warn; reversals larger than the configured tolerance fail. Equal phase points fail because the inverse lookup is ambiguous. Strongly non-monotonic data produces no LUT. PCHIP requires strictly monotonic data; piecewise-linear is the default.

The firmware lookup is **PDoA -> AoA**. Its input convention is:

```
lut_input = CUSTOM_PDOA_SIGN * (unwrapped_pdoa - CUSTOM_PDOA_ZERO_OFFSET_DEG)
```

The sign is -1 for reversed orientation and +1 otherwise. Keep the correct phase branch and stay inside the calibrated domain. Do not apply sign reversal twice. Leave-one-angle-out validation reports signed error for every held-out angle, MAE, RMSE and maximum absolute error. Held-out endpoints necessarily use extrapolation and are labeled. Production use should not extrapolate.

Default validation limits are MAE <= 5 degrees and maximum error <= 10 degrees. Minimum accepted samples, phase SD and TDoA SD also gate readiness. A small monotonicity warning can produce an engineering candidate LUT but cannot be marked ready. Data with missing zero calibration, too few angles, unstable fixed phase/TDoA or failed validation cannot be ready. A READY result is readiness against project criteria, not certification or proof that RF hardware is correct. Compare only captures at a consistent channel, geometry, distance and firmware configuration; create separate projects for different configurations.

## Distance / antenna-delay calibration

Import `distance` datasets at known distances, for example 1, 2, 3 and 5 m. Provide measured distances in the original log/CSV, attach a separate CSV with a `measured_distance_m` column, attach a plain ordered list, or manually assign one constant distance to a selected dataset. Lists must have one value per record in acquisition order. A manually assigned constant cannot establish noise/stability.

The page computes every record's range error, per-distance mean bias and SD, overall sample-weighted bias, and regression:

```
range_error_m = measured_distance_m - true_distance_m
measured_distance_m = slope * true_distance_m + intercept_m
equivalent_delay_seconds = mean_range_bias_m / 299792458
external_application_correction_m = -mean_range_bias_m
```

The range error is shown by the individual-point plot and can be calculated from the two distance columns in full CSV. A stable intercept is consistent with a fixed offset; a slope far from 1 suggests scaling effects worth investigating. Review regression and residuals rather than interpreting the mean bias alone. Bias is shown in metres/mm and equivalent one-way delay in ps/ns. A single distance cannot determine regression slope. This is **CUSTOM PCB EXTERNAL RANGE / ANTENNA-DELAY CORRECTION**. It is not a DS-TWR register value.

Final firmware calibration may need **Murata module-specific factory calibration + custom PCB external correction**. Do not overwrite factory OTP values. Confirm register units, correction sign, Tx/Rx allocation, timestamp scaling, DS-TWR factors and module factory-calibration handling with the firmware team/documentation. No register encoding is guessed.

## Movement and EVB comparison

Import a continuous moving-tag log as `movement`. The Movement page plots raw/unwrapped phase, signed TDoA, range, both STS powers and both first-path indices against elapsed timestamp seconds. If timestamps are unavailable, the horizontal coordinate is sample number (despite the elapsed_s column name). Datasets remain separate; discontinuities are not calculated across file boundaries. Events include phase wraps, phase/range jumps, TDoA spikes, first-path jumps and large power imbalance. Wraps alone do not establish RF instability. Smooth available raw fields suggest checking AoA conversion/coordinate transforms/visualization, but missing channels and undersampling can hide faults.

EVB vs Custom compares enabled accepted datasets matched by type, physical angle and physical distance. It reports mean, absolute difference and both sample SDs, plus ratios for positive power metrics. Multiple repetitions at a matching operating point are pooled. Phase values require the same firmware convention; wrapped branch differences can make direct phase comparisons ambiguous. Larger diagnostic values are not automatically better.

## Results and export

**Calibration Results** displays parser/sample/stability/orientation/monotonicity/balance/range checks, candidate LUT, validation and warnings. PASS means a stated project criterion was satisfied. WARNING means review is needed or data is unavailable. FAIL blocks the LUT. Readiness is conservative, but cannot detect impedance mismatch, antenna coupling or hardware faults from statistics alone.

The **Export** page refreshes analysis and writes:

- Full CSV: all enabled measurements, raw values, filter flags and derived values.
- Calibration CSV: ordered `pdoa_deg,aoa_deg` lookup pairs using the documented sign/offset convention.
- JSON: project, settings, physical corrections, LUT, statistics and warnings.
- C header: float LUT, phase offset/sign and available external range/delay constants, with a production-readiness flag and application comments. Missing range calibration emits no range constant.
- Self-contained HTML report: metadata, datasets, criteria, statistics, warnings, readiness, LUT, validation, range, movement evidence, comparison and all 14 plots. Open locally in a browser; use browser Print to PDF if needed.

JSON project Save/Load preserves copied original records, source paths, assignments, enabled state, metadata, settings, results and LUT. Analysis is recomputed after load and before export. Existing export paths follow the native save dialog's overwrite behavior.

## Firmware-specific confirmations still needed

- TDoA signed field width (41 bits is the default, not inferred from a sample), physical unit and timestamp wrap behavior.
- Raw PDoA conversion if diagnostic degrees are absent; whether logged phases already include firmware corrections.
- STS1/STS2 to ANT1/ANT2 mapping, sign convention, zero angle and coordinate reference.
- Physical header-range encoding if you intend to use it. The default treats it as opaque.
- Factory OTP handling, firmware delay unit, Tx/Rx split, DS-TWR correction factors and sign.
- Channel-dependent calibration, STS status-bit validity semantics, RF power conversion and FP-index units. Raw statuses are preserved and displayed; undocumented status bits are not used to reject records.

The current readiness checks do not certify STS authentication/status validity or absolute RF power. Establish firmware-specific acceptance rules before production. Software calibration cannot repair strong antenna coupling, impedance mismatch or unstable first-path detection.
