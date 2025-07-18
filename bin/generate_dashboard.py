#!/usr/bin/env python3
"""
Enhanced Kraken Dashboard with automatic sample switching
"""

import json
import argparse
from pathlib import Path
import sys
from datetime import datetime

def generate_dashboard(json_files, output_file="dashboard.html", title="Kraken Dashboard"):
    """
    Generate an enhanced HTML dashboard with responsive sample switching
    """
    # Load and combine all JSON data
    all_data = []
    for json_file in json_files:
        with open(json_file, 'r') as f:
            data = json.load(f)
            if isinstance(data, list):
                all_data.extend(data)
            else:
                all_data.append(data)
    
    # Get current date for the footer
    generation_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Generate the HTML with embedded data
    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="https://cdn.datatables.net/1.11.5/css/jquery.dataTables.min.css">
    <link rel="stylesheet" href="https://cdn.datatables.net/buttons/2.2.2/css/buttons.dataTables.min.css">
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="https://cdn.datatables.net/1.11.5/js/jquery.dataTables.min.js"></script>
    <script src="https://cdn.datatables.net/buttons/2.2.2/js/dataTables.buttons.min.js"></script>
    <script src="https://cdn.datatables.net/buttons/2.2.2/js/buttons.html5.min.js"></script>
    <script src="https://cdn.datatables.net/buttons/2.2.2/js/buttons.print.min.js"></script>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        :root {{
            --primary: #3498db;
            --secondary: #2c3e50;
            --light: #f8f9fa;
            --dark: #343a40;
            --gray: #6c757d;
            --success: #28a745;
            --danger: #e74c3c;
        }}
        
        body {{
            font-family: 'Segoe UI', Roboto, -apple-system, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f8fafc;
            line-height: 1.6;
            color: #212529;
        }}
        
        .dashboard-container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 0 20px rgba(0,0,0,0.05);
        }}
        
        h1 {{
            color: var(--secondary);
            text-align: center;
            margin-bottom: 30px;
            font-weight: 600;
            border-bottom: 1px solid #eee;
            padding-bottom: 15px;
        }}
        
        .metric-cards {{
            display: flex;
            gap: 15px;
            margin-bottom: 25px;
        }}
        
        .metric-card {{
            flex: 1;
            padding: 20px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            border-left: 4px solid var(--primary);
        }}
        
        .metric-value {{
            font-size: 24px;
            font-weight: bold;
            color: var(--secondary);
            margin-bottom: 5px;
        }}
        
        .metric-label {{
            color: var(--gray);
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .filter-section {{
            background-color: #f8fafc;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 25px;
            border-left: 4px solid var(--primary);
        }}
        
        .filter-note {{
            font-size: 0.85em;
            color: var(--gray);
            margin-left: 10px;
            font-style: italic;
        }}
        
        .chart-container {{
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 25px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            border: 1px solid #eee;
        }}
        
        .data-table {{
            margin-top: 20px;
        }}
        
        .dataTables_wrapper {{
            margin-top: 20px;
        }}
        
        .dataTables_length select, 
        .dataTables_filter input {{
            padding: 5px 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }}
        
        .tab-container {{
            margin-top: 20px;
        }}
        
        .tab-buttons {{
            display: flex;
            margin-bottom: -1px;
        }}
        
        .tab-button {{
            padding: 12px 20px;
            background: none;
            border: none;
            border-bottom: 3px solid transparent;
            cursor: pointer;
            margin-right: 5px;
            font-weight: 500;
            color: var(--gray);
            transition: all 0.2s;
        }}
        
        .tab-button:hover {{
            color: var(--primary);
        }}
        
        .tab-button.active {{
            color: var(--primary);
            font-weight: 600;
            border-bottom-color: var(--primary);
        }}
        
        .tab-content {{
            display: none;
            padding: 20px;
            background-color: white;
            border-radius: 0 8px 8px 8px;
            border: 1px solid #eee;
        }}
        
        .tab-content.active {{
            display: block;
        }}
        
        select, input {{
            padding: 8px 12px;
            margin-right: 10px;
            border-radius: 4px;
            border: 1px solid #ddd;
        }}
        
        label {{
            margin-right: 5px;
            font-weight: 500;
            color: var(--secondary);
        }}
        
        button {{
            padding: 8px 16px;
            background-color: var(--primary);
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            transition: background-color 0.2s;
        }}
        
        button:hover {{
            background-color: #2980b9;
        }}
        
        .footer {{
            margin-top: 30px;
            padding-top: 15px;
            border-top: 1px solid #eee;
            color: #7f8c8d;
            font-size: 0.85em;
            text-align: center;
        }}
        
        .footer a {{
            color: var(--primary);
            text-decoration: none;
        }}
        
        .footer a:hover {{
            text-decoration: underline;
        }}
        
        @media (max-width: 768px) {{
            .metric-cards {{
                flex-direction: column;
            }}
            
            .tab-buttons {{
                overflow-x: auto;
                padding-bottom: 10px;
            }}
            
            .filter-section {{
                padding: 15px 10px;
            }}
        }}
    </style>
</head>
<body>
    <div class="dashboard-container">
        <h1>{title}</h1>
        
        <div class="metric-cards">
            <!-- Will be populated by JavaScript -->
        </div>
        
        <div class="filter-section">
            <label for="sample-select">Sample:</label>
            <select id="sample-select">
                <!-- Options will be added by JavaScript -->
            </select>
            
            <label for="min-pct">Chart Min %:</label>
            <input type="number" id="min-pct" min="0" max="100" value="0" step="0.1"
                   title="Minimum percentage for taxa in the chart">
            
            <button id="apply-filters">Update Chart</button>
            <span class="filter-note">(Table shows all taxa - use search/filters below)</span>
        </div>
        
        <div class="tab-container">
            <div class="tab-buttons">
                <button class="tab-button active" data-tab="summary">Summary</button>
                <button class="tab-button" data-tab="taxa">Taxonomic Breakdown</button>
                <button class="tab-button" data-tab="comparison">Sample Comparison</button>
            </div>
            
            <div id="summary" class="tab-content active">
                <div class="chart-container">
                    <div id="classification-chart" style="width:100%; height:400px;"></div>
                </div>
                <div class="chart-container">
                    <div id="reads-chart" style="width:100%; height:400px;"></div>
                </div>
                <div class="data-table">
                    <h3>Detailed Metrics</h3>
                    <table id="summary-table" class="display" style="width:100%"></table>
                </div>
            </div>
            
            <div id="taxa" class="tab-content">
                <div class="chart-container">
                    <div id="taxa-chart" style="width:100%; height:500px;"></div>
                </div>
                <div class="data-table">
                    <h3>All Taxonomic Classifications</h3>
                    <table id="taxa-table" class="display" style="width:100%"></table>
                </div>
            </div>
            
            <div id="comparison" class="tab-content">
                <div class="chart-container">
                    <div id="comparison-chart" style="width:100%; height:500px;"></div>
                </div>
                <div class="data-table">
                    <h3>All Samples Data</h3>
                    <table id="all-data-table" class="display" style="width:100%"></table>
                </div>
            </div>
        </div>
        
        <div class="footer">
            Generated by <strong><a href="https://github.com/kwtrp-peo/viralphyl" target="_blank" rel="noopener noreferrer">kwtrp-peo/viraphyl</a> v0.9.4</strong> on {generation_date} | 
            DOI: <a href="https://doi.org/234123442358x" target="_blank" rel="noopener noreferrer" style="font-family: monospace;">234123442358x</a>
        </div>
    </div>

    <script>
        // Embedded data from JSON files
        const sampleData = {json.dumps(all_data, indent=4)};
        
        // Version information
        const versionInfo = {{
            generator: "kwtrp-peo/viraphyl",
            version: "0.7.0",
            doi: "234123442358x",
            url: "https://github.com/kwtrp-peo/viraphyl",
            generated: new Date().toISOString()
        }};
        
        // Initialize the dashboard with debounced updates
        $(document).ready(function() {{
            // Populate sample dropdown
            const sampleSelect = $('#sample-select');
            sampleData.forEach(sample => {{
                sampleSelect.append(`<option value="${{sample.Sample}}">${{sample.Sample}}</option>`);
            }});

            // Initialize tabs
            $('.tab-button').click(function() {{
                const tabId = $(this).data('tab');
                $('.tab-button').removeClass('active');
                $(this).addClass('active');
                $('.tab-content').removeClass('active');
                $(`#${{tabId}}`).addClass('active');
                updateCharts();
            }});

            // Automatic updates for sample selection only (300ms debounce)
            let updateTimeout;
            $('#sample-select').on('change', function() {{
                clearTimeout(updateTimeout);
                updateTimeout = setTimeout(updateCharts, 300);
            }});

            // Manual update for Min% and force refresh
            $('#apply-filters').click(function() {{
                clearTimeout(updateTimeout); // Cancel any pending sample-change updates
                updateCharts();
            }});

            // Optional: Add Enter key support for Min% input
            $('#min-pct').keypress(function(e) {{
                if (e.which === 13) {{ // 13 = Enter key
                    $('#apply-filters').click();
                }}
            }});

            // Initial render
            updateCharts();
            renderAllDataTable();
        }});

        function updateMetricCards(sample) {{
            const classifiedReads = sample.Classified_Reads || 
                                 (sample.Total_Reads * (sample.Classified_Pct / 100));
            const unclassifiedReads = sample.Unclassified_Reads || 
                                    (sample.Total_Reads - classifiedReads);
            const classifiedPct = sample.Classified_Pct || 
                                 ((classifiedReads / sample.Total_Reads) * 100);
            const unclassifiedPct = sample.Unclassified_Pct || 
                                  ((unclassifiedReads / sample.Total_Reads) * 100);
            
            const cardsHtml = `
                <div class="metric-card">
                    <div class="metric-value">${{sample.Total_Reads.toLocaleString()}}</div>
                    <div class="metric-label">Total Reads</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${{unclassifiedReads.toLocaleString()}}</div>
                    <div class="metric-label">Unclassified (${{unclassifiedPct.toFixed(2)}}%)</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${{classifiedReads.toLocaleString()}}</div>
                    <div class="metric-label">Classified (${{classifiedPct.toFixed(2)}}%)</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${{sample.Taxa.length.toLocaleString()}}</div>
                    <div class="metric-label">Taxa Identified</div>
                </div>
            `;
            
            $('.metric-cards').html(cardsHtml);
        }}

        function updateCharts() {{
            const selectedSample = $('#sample-select').val();
            const minPct = parseFloat($('#min-pct').val());
            
            const sample = sampleData.find(s => s.Sample === selectedSample);
            if (!sample) return;
            
            // Update metric cards
            updateMetricCards(sample);
            
            // Show ALL taxa in the table (filtering handled client-side)
            updateTaxaTable(sample.Taxa);
            
            // Apply percentage filter only to the visual chart
            const filteredTaxa = sample.Taxa.filter(t => t.Total_Percentage >= minPct);
            updateTaxaChart(filteredTaxa);
            
            updateClassificationChart(sample);
            updateReadsChart(sample);
            updateSummaryTable(sample);
        }}

        function updateClassificationChart(sample) {{
            const classifiedPct = sample.Classified_Pct || (100 - sample.Unclassified_Pct);
            const unclassifiedPct = sample.Unclassified_Pct || (100 - classifiedPct);

            const labels = ['Classified', 'Unclassified'];
            const values = [classifiedPct, unclassifiedPct];

            const classificationColorMap = {{
                "Classified": "#3b75afff",
                "Unclassified": "#ef8636ff"
            }};

            const data = [{{
                values: values,
                labels: labels,
                type: 'pie',
                marker: {{
                    colors: labels.map(label => classificationColorMap[label])
                }},
                textinfo: 'percent',
                hoverinfo: 'label+percent+value',
                hole: 0.4,
                textfont: {{
                    size: 14
                }},
                sort: false
            }}];

            const layout = {{
                title: 'Read Classification',
                height: 400,
                showlegend: true,
                font: {{
                    family: 'Segoe UI, sans-serif'
                }}
            }};

            Plotly.newPlot('classification-chart', data, layout);
        }}

        function updateReadsChart(sample) {{
            const classifiedReads = sample.Classified_Reads || 
                                (sample.Total_Reads * (sample.Classified_Pct / 100));
            const unclassifiedReads = sample.Unclassified_Reads || 
                                    (sample.Total_Reads - classifiedReads);

            const data = [
                {{
                    name: 'Classified Reads',
                    value: classifiedReads
                }},
                {{
                    name: 'Unclassified Reads',
                    value: unclassifiedReads
                }},
                {{
                    name: 'Total Reads',
                    value: sample.Total_Reads
                }}
            ];

            const readColorMap = {{
                "Total Reads": "#2c3e50",
                "Classified Reads": "#3b75afff",
                "Unclassified Reads": "#ef8636ff"
            }};

            const chartData = [{{
                x: data.map(item => item.name),
                y: data.map(item => item.value),
                type: 'bar',
                marker: {{
                    color: data.map(item => readColorMap[item.name])
                }}
            }}];

            const layout = {{
                title: 'Read Counts',
                yaxis: {{
                    title: 'Number of Reads'
                }},
                font: {{
                    family: 'Segoe UI, sans-serif'
                }}
            }};

            Plotly.newPlot('reads-chart', chartData, layout);
        }}


        function updateTaxaChart(taxa) {{
            // Sort by percentage (descending)
            taxa.sort((a, b) => b.Total_Percentage - a.Total_Percentage);
            
            // Limit to top 50 for the chart (for better visualization)
            const topTaxa = taxa.slice(0, 50);
            
            const data = [{{
                x: topTaxa.map(t => t.Name),
                y: topTaxa.map(t => t.Total_Percentage),
                type: 'bar',
                marker: {{
                    color: 'var(--success)'
                }}
            }}];
            
            const layout = {{
                title: 'Top Taxa by Percentage (≥ min %)',
                xaxis: {{
                    title: 'Taxa',
                    tickangle: -45
                }},
                yaxis: {{
                    title: 'Percentage (%)'
                }},
                margin: {{
                    b: 150
                }},
                font: {{
                    family: 'Segoe UI, sans-serif'
                }}
            }};
            
            Plotly.newPlot('taxa-chart', data, layout);
        }}

        function updateSummaryTable(sample) {{
            const classifiedReads = sample.Classified_Reads || 
                                 (sample.Total_Reads * (sample.Classified_Pct / 100));
            const unclassifiedReads = sample.Unclassified_Reads || 
                                    (sample.Total_Reads - classifiedReads);
            const classifiedPct = sample.Classified_Pct || 
                                 ((classifiedReads / sample.Total_Reads) * 100);
            const unclassifiedPct = sample.Unclassified_Pct || 
                                  ((unclassifiedReads / sample.Total_Reads) * 100);
            
            // Ordered summary data
            const summaryData = [
                {{
                    "Metric": "Total Reads",
                    "Value": sample.Total_Reads.toLocaleString()
                }},
                {{
                    "Metric": "Unclassified Reads",
                    "Value": `${{unclassifiedReads.toLocaleString()}} (${{unclassifiedPct.toFixed(2)}}%)`
                }},
                {{
                    "Metric": "Classified Reads",
                    "Value": `${{classifiedReads.toLocaleString()}} (${{classifiedPct.toFixed(2)}}%)`
                }},
                {{
                    "Metric": "Number of Taxa",
                    "Value": sample.Taxa.length.toLocaleString()
                }}
            ];
            
            $('#summary-table').DataTable({{
                data: summaryData,
                columns: [
                    {{ title: "Metric", data: "Metric" }},
                    {{ title: "Value", data: "Value" }}
                ],
                destroy: true,
                searching: false,
                paging: false,
                info: false,
                ordering: false
            }});
        }}

        function updateTaxaTable(taxa) {{
            $('#taxa-table').DataTable({{
                data: taxa,
                columns: [
                    {{ title: "TaxID", data: "TaxID" }},
                    {{ title: "Name", data: "Name" }},
                    {{ title: "Read Count", data: "Count", render: $.fn.dataTable.render.number(',', '.', 0, '') }},
                    {{ title: "Classified %", data: "Classified_Percentage", render: function(data) {{ return data ? data.toFixed(2) + '%' : 'N/A'; }} }},
                    {{ title: "Total %", data: "Total_Percentage", render: function(data) {{ return data.toFixed(2) + '%'; }} }}
                ],
                destroy: true,
                order: [[4, 'desc']], // Sort by total percentage descending
                pageLength: 5,
                lengthMenu: [5, 10, 25, 50, 100, -1], // -1 means "All"
                dom: 'Blfrtip',
                buttons: [
                    'copy', 'csv', 'excel', 'pdf', 'print'
                ],
                language: {{
                    search: "_INPUT_",
                    searchPlaceholder: "Search taxa..."
                }}
            }});
        }}

        function renderAllDataTable() {{
            // Prepare data for the comparison table
            const tableData = sampleData.map(sample => {{
                const classifiedReads = sample.Classified_Reads || 
                                     (sample.Total_Reads * (sample.Classified_Pct / 100));
                const classifiedPct = sample.Classified_Pct || 
                                     ((classifiedReads / sample.Total_Reads) * 100);
                const unclassifiedPct = sample.Unclassified_Pct || 
                                      (100 - classifiedPct);
                
                return {{
                    "Sample": sample.Sample,
                    "Total Reads": sample.Total_Reads.toLocaleString(),
                    "Unclassified (%)": unclassifiedPct.toFixed(2),
                    "Classified (%)": classifiedPct.toFixed(2),
                    "Number of Taxa": sample.Taxa.length,
                    "Top Taxa": sample.Taxa[0]?.Name || "N/A",
                    "Top Taxa %": sample.Taxa[0]?.Total_Percentage?.toFixed(2) || "N/A"
                }};
            }});
            
            $('#all-data-table').DataTable({{
                data: tableData,
                columns: [
                    {{ title: "Sample", data: "Sample" }},
                    {{ title: "Total Reads", data: "Total Reads" }},
                    {{ title: "Unclassified (%)", data: "Unclassified (%)" }},
                    {{ title: "Classified (%)", data: "Classified (%)" }},
                    {{ title: "Number of Taxa", data: "Number of Taxa" }},
                    {{ title: "Top Taxa", data: "Top Taxa" }},
                    {{ title: "Top Taxa %", data: "Top Taxa %" }}
                ],
                order: [[1, 'desc']], // Sort by total reads descending
                pageLength: 5,
                lengthMenu: [5, 10, 25, 50],
                dom: 'Blfrtip',
                buttons: [
                    'copy', 'csv', 'excel', 'pdf', 'print'
                ]
            }});
            
            // Create comparison chart
            createComparisonChart();
        }}

        function createComparisonChart() {{
            const samples = sampleData.map(s => s.Sample);
            const classified = sampleData.map(s => {{
                if (s.Classified_Pct) return s.Classified_Pct;
                const classifiedReads = s.Classified_Reads || 
                                    (s.Total_Reads * (s.Classified_Pct / 100));
                return (classifiedReads / s.Total_Reads) * 100;
            }});
            const unclassified = sampleData.map((s, i) => {{
                if (s.Unclassified_Pct) return s.Unclassified_Pct;
                return 100 - classified[i];
            }});

            const data = [
                {{
                    x: samples,
                    y: classified,
                    name: 'Classified',
                    type: 'bar',
                    marker: {{
                        color: '#3b75afff'
                    }}
                }},
                {{
                    x: samples,
                    y: unclassified,
                    name: 'Unclassified',
                    type: 'bar',
                    marker: {{
                        color: '#ef8636ff'
                    }}
                }}
            ];

            const layout = {{
                title: 'Classification Across Samples',
                barmode: 'stack',
                yaxis: {{
                    title: 'Percentage (%)',
                    range: [0, 100]
                }},
                font: {{
                    family: 'Segoe UI, sans-serif'
                }},
                legend: {{
                    traceorder: 'normal'
                }}
            }};

            Plotly.newPlot('comparison-chart', data, layout);
        }}
    </script>
</body>
</html>
    """
    
    # Save the HTML file
    with open(output_file, 'w') as f:
        f.write(html_template)
    
    print(f"Enhanced dashboard generated successfully: {output_file}")

def main():
    parser = argparse.ArgumentParser(
        description="Generate enhanced Kraken dashboard with version info",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        '-j', '--json',
        nargs='+',
        required=True,
        help='Input JSON file(s) from Kraken processing',
        metavar='FILE',
        dest='json_files'
    )
    
    parser.add_argument(
        '-o', '--output',
        default='kraken_dashboard.html',
        help='Output HTML file path'
    )
    
    parser.add_argument(
        '-t', '--title',
        default='Kraken Results Dashboard',
        help='Dashboard title'
    )
    
    args = parser.parse_args()
    
    # Verify files exist
    missing = [f for f in args.json_files if not Path(f).exists()]
    if missing:
        print(f"Error: Missing files: {', '.join(missing)}")
        sys.exit(1)
    
    generate_dashboard(
        json_files=args.json_files,
        output_file=args.output,
        title=args.title
    )

if __name__ == "__main__":
    main()