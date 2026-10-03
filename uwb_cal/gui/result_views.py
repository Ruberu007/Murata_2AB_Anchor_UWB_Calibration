"""Readable summaries for engineers; structured exports retain the full results."""
from html import escape


def value(item):
    if item is None:
        return 'Not available'
    if isinstance(item, float):
        return f'{item:.4g}'
    return escape(str(item))


def table(headers, rows):
    html = '<table width="100%" cellspacing="0" cellpadding="6" border="0"><tr bgcolor="#e6eff5">'
    html += ''.join('<th align="left">' + escape(h) + '</th>' for h in headers) + '</tr>'
    for i, row in enumerate(rows):
        html += '<tr bgcolor="' + ('#f4f8fb' if i % 2 == 0 else '#ffffff') + '">' + ''.join('<td>' + value(v) + '</td>' for v in row) + '</tr>'
    return html + '</table>'


def bullets(items):
    return '<ul>' + ''.join('<li>' + escape(str(item)) + '</li>' for item in items) + '</ul>'


def calibration_summary(result):
    ready = result.get('production_ready', False)
    html = '<h2>' + ('Ready against project criteria' if ready else 'Review needed before using the lookup') + '</h2>'
    html += '<p>These checks use your project limits. They do not certify the hardware or change firmware.</p>'
    html += table(['Check', 'Outcome'], result.get('readiness', {}).items())
    html += '<h3>External PCB phase correction</h3>' + table(['Quantity', 'Value'], [('Measured zero-angle offset (°)', result.get('zero_pdoa_offset_deg')), ('Suggested additive correction (°)', result.get('suggested_pdoa_correction_deg')), ('Antenna / phase orientation', result.get('orientation')), ('Selected angle sector (°)', result.get('calibration_sector_deg'))])
    validation = result.get('validation')
    if validation:
        html += '<h3>Angle prediction accuracy</h3><p>One known angle is left out at a time and estimated from the remaining points.</p>'
        html += table(['Average absolute error (°)', 'RMSE (°)', 'Worst absolute error (°)'], [[validation['mae'], validation['rmse'], validation['max_error']]])
        html += '<p>' + escape(validation['note']) + '</p>'
        html += table(['True angle (°)', 'Estimated angle (°)', 'Error (°)', 'Outside remaining points?'], [[r['angle_deg'], r['predicted_deg'], r['error_deg'], 'Yes' if r['extrapolated'] else 'No'] for r in validation['errors']])
    if result.get('lut'):
        html += '<h3>Candidate phase-to-angle lookup</h3><p>Input = sign × (unwrapped phase − zero offset). Check readiness before firmware integration.</p>'
        html += table(['Lookup phase (°)', 'Physical angle (°)'], [[r['pdoa_deg'], r['aoa_deg']] for r in result['lut']])
    html += '<h3>Warnings and next checks</h3>' + bullets(result.get('warnings', []))
    html += '<h3>Engineering notes</h3>' + bullets(result.get('engineering_notes', []))
    return html


def distance_summary(result):
    if not result:
        return '<h2>Measured range is needed</h2><p>Import a distance test with known true distance and measured metres. Then run analysis.</p>'
    html = '<h2>External PCB range correction</h2><p>Positive bias means measured distances are too long. Subtract the bias to correct the application distance.</p>'
    html += table(['Quantity', 'Value'], [('Mean bias (mm)', result['bias_mm']), ('Application correction (m)', result['correction_m']), ('Equivalent one-way delay (ps)', result['delay_ps']), ('Equivalent delay (ns)', result['delay_ns']), ('Regression slope (ideal 1)', result['slope']), ('Regression intercept (m)', result['intercept_m'])])
    html += '<h3>At each known distance</h3>' + table(['True distance (m)', 'Average reading (m)', 'Average error (m)', 'Error spread / SD (m)', 'Readings'], [[r['true_distance_m'], r['measured_mean'], r['bias_m'], r['sd_m'], r['count']] for r in result['by_distance']])
    return html + '<p>' + escape(result['note']) + '</p>'


def movement_summary(movements):
    if not movements:
        return '<h2>No moving-tag capture loaded</h2><p>Import a file as movement, then run analysis. The guide explains what to look for.</p>'
    html = '<h2>Movement diagnostic evidence</h2>'
    for name, result in movements.items():
        html += '<h3>' + escape(name) + '</h3><p>' + escape(result['conclusion']) + '</p>'
        html += table(['Sample number (starts at 0)', 'Event'], [[e['sample'], e['event']] for e in result['events']])
    return html


def comparison_summary(rows):
    html = '<h2>Reference board vs custom PCB</h2><p>Only matching test types, angles and distances are compared. Larger values are not automatically better. SD means spread around the average.</p>'
    if not rows:
        return html + '<p>Load both EVB-EVB and EVB-CUSTOM captures at matching operating points, then run analysis.</p>'
    return html + table(['Angle (°)', 'Distance (m)', 'Parameter', 'EVB average', 'Custom average', 'Difference', 'Ratio', 'EVB SD', 'Custom SD'], [[r['angle_deg'], r['distance_m'], r['parameter'], r['evb_mean'], r['custom_mean'], r['absolute_difference'], r['ratio'], r['evb_sd'], r['custom_sd']] for r in rows])


def angle_summary(result):
    html = '<h2>Stationary angle measurements</h2>'
    html += table(['Quantity', 'Value'], [('External zero-angle offset (°)', result.get('zero_pdoa_offset_deg')), ('Suggested additive correction (°)', result.get('suggested_pdoa_correction_deg')), ('Phase orientation', result.get('orientation')), ('Phase trend consistency', result.get('monotonicity')), ('Phase / physical-angle slope', result.get('slope')), ('Direction consistency / Spearman correlation', result.get('spearman'))])
    html += '<p>Accepted readings are used for filtered statistics. Rejected readings remain in the original data. Power is not dBm; timing and index values are raw units.</p>'
    for record in result['statistics']:
        html += '<h3>' + escape(record['dataset']) + '</h3><p>Total: ' + str(record['total']) + ' | Accepted: ' + str(record['valid']) + ' | Rejected/missing: ' + str(record['rejected']) + '</p>'
        html += '<p>RF path balance: ' + escape(record['rf_balance']['status']) + '</p>'
        html += table(['Field', 'Average', 'Middle reading', 'Spread / SD', 'Minimum', 'Maximum', 'MAD', 'IQR'], [[metric, stats['mean'], stats['median'], stats['sd'], stats['minimum'], stats['maximum'], stats['mad'], stats['iqr']] for metric, stats in record['metrics'].items()])
        html += '<p>MAD = typical distance from the middle reading; IQR = spread of the middle half of readings.</p>'
        html += '<h4>Original readings before filtering</h4>' + table(['Field', 'Average', 'Spread / SD'], [[metric, stats['mean'], stats['sd']] for metric, stats in record['raw_metrics'].items()])
    return html
