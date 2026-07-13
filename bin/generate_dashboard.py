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
    
    # Sort samples alphanumerically
    all_data.sort(key=lambda x: x.get('Sample', ''))
    
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
            --classified: #3b75afff;
            --unclassified: #ef8636ff;
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
        
        .controls-section {{
            background-color: #f8fafc;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 25px;
            border-left: 4px solid var(--primary);
        }}
        
        .controls-grid {{
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            align-items: flex-end;
        }}
        
        .control-group {{
            flex: 1;
            min-width: 200px;
        }}
        
        .control-group label {{
            display: block;
            margin-bottom: 5px;
            font-weight: 500;
            color: var(--secondary);
            font-size: 0.9em;
        }}
        
        .control-group select,
        .control-group input {{
            width: 100%;
            padding: 8px 12px;
            border-radius: 4px;
            border: 1px solid #ddd;
            font-size: 14px;
        }}
        
        .button-group {{
            display: flex;
            gap: 10px;
            align-items: center;
        }}
        
        button {{
            padding: 8px 16px;
            background-color: var(--primary);
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            transition: background-color 0.2s;
            font-size: 14px;
            white-space: nowrap;
        }}
        
        button:hover {{
            background-color: #2980b9;
        }}
        
        .filter-note {{
            font-size: 0.85em;
            color: var(--gray);
            font-style: italic;
            margin-top: 10px;
        }}
        
        .metric-cards {{
            display: flex;
            gap: 15px;
            margin-bottom: 25px;
            flex-wrap: wrap;
        }}
        
        .metric-card {{
            flex: 1;
            min-width: 200px;
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
            flex-wrap: wrap;
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
            
            .controls-grid {{
                flex-direction: column;
                gap: 10px;
            }}
            
            .button-group {{
                width: 100%;
            }}
            
            button {{
                flex: 1;
            }}
            
            .tab-buttons {{
                overflow-x: auto;
                padding-bottom: 10px;
            }}
        }}
    </style>
</head>
<body>
    <div class="dashboard-container">
        <h1>{title}</h1>
        
        <!-- Metric Cards - Will be populated by JavaScript -->
        <div class="metric-cards"></div>
        
        <!-- Controls Section -->
        <div class="controls-section">
            <div class="controls-grid">
                <div class="control-group">
                    <label for="sample-search"> Search Sample:</label>
                    <input type="text" id="sample-search" placeholder="Type to filter samples...">
                </div>
                
                <div class="control-group">
                    <label for="sample-select"> Select Sample:</label>
                    <select id="sample-select"></select>
                </div>
                
                <div class="control-group">
                    <label for="sort-order"> Sort Samples:</label>
                    <select id="sort-order">
                        <option value="alpha">Alphabetical (A-Z)</option>
                        <option value="alpha-desc">Alphabetical (Z-A)</option>
                        <option value="reads">By Total Reads</option>
                        <option value="taxa">By Taxa Count</option>
                        <option value="classified">By Classified %</option>
                    </select>
                </div>
                
                <div class="control-group">
                    <label for="min-pct"> Chart Min %:</label>
                    <input type="number" id="min-pct" min="0" max="100" value="0" step="0.1">
                </div>
                
                <div class="button-group">
                    <button id="apply-filters">Update Chart</button>
                </div>
            </div>
            <div class="filter-note">
                 Table shows all taxa - use table search/filters below. Charts respect minimum percentage.
            </div>
        </div>
        
        <!-- Tabs -->
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
        
        // ==================== UTILITY FUNCTIONS ====================
        
        // Natural alphanumeric sorting using Intl.Collator
        const naturalCompare = new Intl.Collator(undefined, {{
            numeric: true,
            sensitivity: 'base'
        }}).compare;
        
        // ==================== SAMPLE HELPER ====================
        // Single source of truth for sample metrics with caching
        
        const SampleHelper = {{
            cache: new Map(),
            
            getMetrics(sample) {{
                if (this.cache.has(sample.Sample)) {{
                    return this.cache.get(sample.Sample);
                }}
                
                const totalReads = sample.Total_Reads || 0;
                
                // Calculate reads
                const classifiedReads = sample.Classified_Reads || 
                                       (totalReads * (sample.Classified_Pct / 100)) ||
                                       (totalReads - (sample.Unclassified_Reads || 0));
                const unclassifiedReads = sample.Unclassified_Reads || 
                                         (totalReads - classifiedReads);
                
                // Calculate percentages
                const classifiedPct = sample.Classified_Pct || 
                                     ((classifiedReads / totalReads) * 100) ||
                                     (100 - (sample.Unclassified_Pct || 0));
                const unclassifiedPct = sample.Unclassified_Pct || 
                                       ((unclassifiedReads / totalReads) * 100) ||
                                       (100 - classifiedPct);
                
                const metrics = {{
                    totalReads,
                    classifiedReads,
                    unclassifiedReads,
                    classifiedPct,
                    unclassifiedPct,
                    taxaCount: sample.Taxa?.length || 0,
                    topTaxa: sample.Taxa?.[0] || null
                }};
                
                this.cache.set(sample.Sample, metrics);
                return metrics;
            }},
            
            clearCache() {{
                this.cache.clear();
            }}
        }};
        
        // ==================== SORTERS ====================
        
        const Sorters = {{
            alpha: (a, b) => naturalCompare(a.Sample, b.Sample),
            'alpha-desc': (a, b) => naturalCompare(b.Sample, a.Sample),
            reads: (a, b) => (b.Total_Reads || 0) - (a.Total_Reads || 0),
            taxa: (a, b) => (b.Taxa?.length || 0) - (a.Taxa?.length || 0),
            classified: (a, b) => {{
                const getPct = (s) => SampleHelper.getMetrics(s).classifiedPct;
                return getPct(b) - getPct(a);
            }}
        }};
        
        // ==================== RENDERERS ====================
        
        const MetricCards = {{
            render(sample) {{
                if (!sample) return '';
                
                const metrics = SampleHelper.getMetrics(sample);
                
                const cards = [
                    {{ label: 'Total Reads', value: metrics.totalReads, format: 'number' }},
                    {{ label: 'Classified', value: metrics.classifiedReads, 
                       percentage: metrics.classifiedPct, format: 'number' }},
                    {{ label: 'Unclassified', value: metrics.unclassifiedReads, 
                       percentage: metrics.unclassifiedPct, format: 'number' }},
                    {{ label: 'Taxa Identified', value: metrics.taxaCount, format: 'number' }}
                ];
                
                return cards.map(card => `
                    <div class="metric-card">
                        <div class="metric-value">${{this.formatValue(card)}}</div>
                        <div class="metric-label">${{card.label}}</div>
                    </div>
                `).join('');
            }},
            
            formatValue(card) {{
                if (card.format === 'number') {{
                    const formatted = card.value.toLocaleString();
                    return card.percentage !== undefined ? 
                        `${{formatted}} (${{card.percentage.toFixed(2)}}%)` : 
                        formatted;
                }}
                return card.value;
            }}
        }};
        
        const TableDataFactory = {{
            summaryRows(sample) {{
                const metrics = SampleHelper.getMetrics(sample);
                
                return [
                    {{ Metric: "Total Reads", Value: metrics.totalReads.toLocaleString() }},
                    {{ Metric: "Unclassified Reads", 
                       Value: `${{metrics.unclassifiedReads.toLocaleString()}} (${{metrics.unclassifiedPct.toFixed(2)}}%)` }},
                    {{ Metric: "Classified Reads", 
                       Value: `${{metrics.classifiedReads.toLocaleString()}} (${{metrics.classifiedPct.toFixed(2)}}%)` }},
                    {{ Metric: "Number of Taxa", Value: metrics.taxaCount.toLocaleString() }}
                ];
            }},
            
            comparisonRow(sample) {{
                const metrics = SampleHelper.getMetrics(sample);
                
                return {{
                    "Sample": sample.Sample,
                    "Total Reads": metrics.totalReads.toLocaleString(),
                    "Unclassified (%)": metrics.unclassifiedPct.toFixed(2),
                    "Classified (%)": metrics.classifiedPct.toFixed(2),
                    "Number of Taxa": metrics.taxaCount,
                    "Top Taxa": metrics.topTaxa?.Name || "N/A",
                    "Top Taxa %": metrics.topTaxa?.Total_Percentage?.toFixed(2) || "N/A"
                }};
            }}
        }};
        
        const ChartStyles = {{
            colors: {{
                classified: '#3b75afff',
                unclassified: '#ef8636ff',
                total: '#2c3e50',
                success: '#28a745'
            }},
            
            layout: {{
                font: {{ family: 'Segoe UI, sans-serif' }},
                margin: {{ b: 150 }},
                height: 400
            }},
            
            getClassificationData(sample) {{
                const metrics = SampleHelper.getMetrics(sample);
                return {{
                    labels: ['Classified', 'Unclassified'],
                    values: [metrics.classifiedPct, metrics.unclassifiedPct],
                    colors: [this.colors.classified, this.colors.unclassified]
                }};
            }},
            
            getReadsData(sample) {{
                const metrics = SampleHelper.getMetrics(sample);
                return [
                    {{ name: 'Total Reads', value: metrics.totalReads, color: this.colors.total }},
                    {{ name: 'Classified Reads', value: metrics.classifiedReads, color: this.colors.classified }},
                    {{ name: 'Unclassified Reads', value: metrics.unclassifiedReads, color: this.colors.unclassified }}
                ];
            }}
        }};
        
        // ==================== DASHBOARD STATE ====================
        
        const DashboardState = {{
            currentSample: null,
            minPercentage: 0,
            filteredTaxa: [],
            samples: [],
            
            init() {{
                this.samples = [...sampleData];
                this.setSample(this.samples[0]?.Sample);
            }},
            
            setSample(sampleName) {{
                this.currentSample = this.samples.find(s => s.Sample === sampleName);
                this.updateFilteredTaxa();
                this.notifyListeners();
            }},
            
            setMinPercentage(value) {{
                this.minPercentage = value;
                this.updateFilteredTaxa();
                this.notifyListeners();
            }},
            
            updateFilteredTaxa() {{
                if (!this.currentSample?.Taxa) {{
                    this.filteredTaxa = [];
                    return;
                }}
                this.filteredTaxa = this.currentSample.Taxa
                    .filter(t => t.Total_Percentage >= this.minPercentage);
            }},
            
            sortSamples(method) {{
                if (Sorters[method]) {{
                    this.samples.sort(Sorters[method]);
                }}
            }},
            
            listeners: [],
            
            subscribe(callback) {{
                this.listeners.push(callback);
                return () => {{
                    this.listeners = this.listeners.filter(l => l !== callback);
                }};
            }},
            
            notifyListeners() {{
                this.listeners.forEach(cb => cb(this));
            }}
        }};
        
        // ==================== DASHBOARD UPDATE FUNCTIONS ====================
        
        function updateAll(state) {{
            if (!state.currentSample) return;
            
            // Update metric cards
            $('.metric-cards').html(MetricCards.render(state.currentSample));
            
            // Update charts
            updateClassificationChart(state.currentSample);
            updateReadsChart(state.currentSample);
            updateTaxaChart(state.filteredTaxa);
            
            // Update tables
            updateSummaryTable(state.currentSample);
            updateTaxaTable(state.filteredTaxa);
        }}
        
        function updateClassificationChart(sample) {{
            const data = ChartStyles.getClassificationData(sample);
            Plotly.react('classification-chart', [{{
                values: data.values,
                labels: data.labels,
                type: 'pie',
                marker: {{ colors: data.colors }},
                hole: 0.4,
                textinfo: 'percent',
                hoverinfo: 'label+percent+value',
                sort: false
            }}], {{
                title: 'Read Classification',
                showlegend: true,
                ...ChartStyles.layout
            }});
        }}
        
        function updateReadsChart(sample) {{
            const data = ChartStyles.getReadsData(sample);
            Plotly.react('reads-chart', [{{
                x: data.map(d => d.name),
                y: data.map(d => d.value),
                type: 'bar',
                marker: {{ color: data.map(d => d.color) }}
            }}], {{
                title: 'Read Counts',
                yaxis: {{ title: 'Number of Reads' }},
                ...ChartStyles.layout
            }});
        }}
        
        function updateTaxaChart(taxa) {{
            const topTaxa = taxa
                .sort((a, b) => b.Total_Percentage - a.Total_Percentage)
                .slice(0, 50);
            
            Plotly.react('taxa-chart', [{{
                x: topTaxa.map(t => t.Name),
                y: topTaxa.map(t => t.Total_Percentage),
                type: 'bar',
                marker: {{ color: ChartStyles.colors.success }}
            }}], {{
                title: 'Top Taxa by Percentage (≥ min %)',
                xaxis: {{ title: 'Taxa', tickangle: -45 }},
                yaxis: {{ title: 'Percentage (%)' }},
                margin: {{ b: 150 }},
                ...ChartStyles.layout
            }});
        }}
        
        function updateSummaryTable(sample) {{
            if ($('#summary-table').DataTable().destroy) {{
                $('#summary-table').DataTable().destroy();
            }}
            
            $('#summary-table').DataTable({{
                data: TableDataFactory.summaryRows(sample),
                columns: [
                    {{ title: "Metric", data: "Metric" }},
                    {{ title: "Value", data: "Value" }}
                ],
                searching: false,
                paging: false,
                info: false,
                ordering: false
            }});
        }}
        
        function updateTaxaTable(taxa) {{
            if ($('#taxa-table').DataTable().destroy) {{
                $('#taxa-table').DataTable().destroy();
            }}
            
            $('#taxa-table').DataTable({{
                data: taxa,
                columns: [
                    {{ title: "TaxID", data: "TaxID" }},
                    {{ title: "Name", data: "Name" }},
                    {{ title: "Read Count", data: "Count", render: $.fn.dataTable.render.number(',', '.', 0, '') }},
                    {{ title: "% of Classified Reads", data: "Classified_Percentage", 
                       render: data => data ? data.toFixed(2) + '%' : 'N/A' }},
                    {{ title: "% of All Reads", data: "Total_Percentage", 
                       render: data => data.toFixed(2) + '%' }}
                ],
                order: [[4, 'desc']],
                pageLength: 5,
                lengthMenu: [5, 10, 25, 50, 100, -1],
                dom: 'Blfrtip',
                buttons: ['copy', 'csv', 'excel', 'pdf', 'print'],
                language: {{
                    search: "_INPUT_",
                    searchPlaceholder: "Search taxa..."
                }}
            }});
        }}
        
        function renderAllDataTable() {{
            const tableData = sampleData.map(sample => TableDataFactory.comparisonRow(sample));
            
            $('#all-data-table').DataTable({{
                data: tableData,
                columns: [
                    {{ title: "Sample", data: "Sample" }},
                    {{ title: "Total Reads", data: "Total Reads" }},
                    {{ title: "Unclassified (%)", data: "Unclassified (%)" }},
                    {{ title: "Classified (%)", data: "Classified (%)" }},
                    {{ title: "# Taxa", data: "Number of Taxa" }},
                    {{ title: "Top Taxa", data: "Top Taxa" }},
                    {{ title: "Top Taxa %", data: "Top Taxa %" }}
                ],
                order: [[1, 'desc']],
                pageLength: 5,
                lengthMenu: [5, 10, 25, 50],
                dom: 'Blfrtip',
                buttons: ['copy', 'csv', 'excel', 'pdf', 'print']
            }});
            
            createComparisonChart();
        }}
        
        function createComparisonChart() {{
            const samples = sampleData.map(s => s.Sample);
            const classified = sampleData.map(s => SampleHelper.getMetrics(s).classifiedPct);
            const unclassified = sampleData.map(s => SampleHelper.getMetrics(s).unclassifiedPct);
            
            Plotly.newPlot('comparison-chart', [
                {{
                    x: samples,
                    y: classified,
                    name: 'Classified',
                    type: 'bar',
                    marker: {{ color: ChartStyles.colors.classified }}
                }},
                {{
                    x: samples,
                    y: unclassified,
                    name: 'Unclassified',
                    type: 'bar',
                    marker: {{ color: ChartStyles.colors.unclassified }}
                }}
            ], {{
                title: 'Classification Across Samples',
                barmode: 'stack',
                yaxis: {{ title: 'Percentage (%)', range: [0, 100] }},
                ...ChartStyles.layout
            }});
        }}
        
        // ==================== DROPDOWN MANAGEMENT ====================
        
        function populateSampleDropdown(sortMethod = 'alpha') {{
            const sampleSelect = $('#sample-select');
            const currentValue = sampleSelect.val();
            
            // Sort samples
            DashboardState.sortSamples(sortMethod);
            
            // Clear and repopulate
            sampleSelect.empty();
            DashboardState.samples.forEach(sample => {{
                sampleSelect.append(`<option value="${{sample.Sample}}">${{sample.Sample}}</option>`);
            }});
            
            // Restore selection or select first
            if (currentValue && DashboardState.samples.some(s => s.Sample === currentValue)) {{
                sampleSelect.val(currentValue);
            }} else {{
                sampleSelect.val(DashboardState.samples[0]?.Sample);
            }}
            
            // Trigger change
            sampleSelect.trigger('change');
        }}
        
        // ==================== INITIALIZATION ====================
        
        $(document).ready(function() {{
            // Initialize state
            DashboardState.init();
            DashboardState.subscribe(updateAll);
            
            // Populate sample dropdown
            populateSampleDropdown('alpha');
            
            // Set up sample search
            $('#sample-search').on('input', function() {{
                const searchTerm = $(this).val().toLowerCase();
                const sortMethod = $('#sort-order').val();
                
                const filteredSamples = sampleData
                    .filter(s => s.Sample.toLowerCase().includes(searchTerm))
                    .sort(Sorters[sortMethod]);
                
                const sampleSelect = $('#sample-select');
                sampleSelect.empty();
                
                if (filteredSamples.length === 0) {{
                    sampleSelect.append('<option value="">No matching samples</option>');
                }} else {{
                    filteredSamples.forEach(sample => {{
                        sampleSelect.append(`<option value="${{sample.Sample}}">${{sample.Sample}}</option>`);
                    }});
                    sampleSelect.val(filteredSamples[0].Sample);
                    sampleSelect.trigger('change');
                }}
            }});
            
            // Handle sort order changes
            $('#sort-order').change(function() {{
                const sortMethod = $(this).val();
                const searchTerm = $('#sample-search').val().toLowerCase();
                
                if (searchTerm) {{
                    $('#sample-search').trigger('input');
                }} else {{
                    populateSampleDropdown(sortMethod);
                }}
            }});
            
            // Handle sample selection
            $('#sample-select').change(function() {{
                DashboardState.setSample($(this).val());
            }});
            
            // Handle min percentage changes
            $('#apply-filters').click(function() {{
                DashboardState.setMinPercentage(parseFloat($('#min-pct').val()) || 0);
            }});
            
            $('#min-pct').keypress(function(e) {{
                if (e.which === 13) {{
                    $('#apply-filters').click();
                }}
            }});
            
            // Tab switching
            $('.tab-button').click(function() {{
                const tabId = $(this).data('tab');
                $('.tab-button').removeClass('active');
                $(this).addClass('active');
                $('.tab-content').removeClass('active');
                $(`#${{tabId}}`).addClass('active');
                
                // Force chart resize for better display
                setTimeout(() => {{
                    window.dispatchEvent(new Event('resize'));
                }}, 100);
            }});
            
            // Initialize comparison tab
            renderAllDataTable();
        }});
    </script>
</body>
</html>
    """
    
    # Save the HTML file
    # Save the HTML file
    with open(output_file, 'w') as f:
        f.write(html_template)

    print(f"Enhanced dashboard generated successfully: {output_file}")
    print("  - Samples sorted alphanumerically")
    print(f"  - Loaded {len(all_data)} sample(s)")

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