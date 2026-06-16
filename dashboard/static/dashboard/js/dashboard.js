/**
 * Dashboard JavaScript
 * Initializes Chart.js charts and handles real-time metric updates
 */

(function () {
    'use strict';

    const dashboard = {
        charts: {},
        refreshIntervals: [],

        // API endpoints
        endpoints: {
            stats: '/dashboard/api/stats/',
            timeline: '/dashboard/api/threat-timeline/',
            compliance: '/dashboard/api/compliance-breakdown/',
            heatmap: '/dashboard/api/risk-heatmap/',
            severity: '/dashboard/api/severity-distribution/',
        },

        // Chart colors
        colors: {
            primary: '#00b4d8',
            cyan: '#00d9ff',
            green: '#06d6a0',
            yellow: '#ffd60a',
            orange: '#f77f00',
            red: '#ef233c',
            text: '#e0e0e0',
            muted: '#a0a0a0',
            dark: '#1a2a3a',
        },

        init: function () {
            this.initThreatTimeline();
            this.initComplianceBreakdown();
            this.initSeverityDistribution();
            this.initRiskHeatmap();
            this.setupMetricsRefresh();
            this.setupActivityRefresh();
        },

        /**
         * Initialize threat activity timeline chart
         */
        initThreatTimeline: function () {
            const ctx = document.getElementById('threatTimelineChart');
            if (!ctx) return;

            fetch(this.endpoints.timeline + '?days=30')
                .then(response => response.json())
                .then(data => {
                    this.charts.threatTimeline = new Chart(ctx, {
                        type: 'line',
                        data: {
                            labels: data.labels,
                            datasets: [{
                                label: 'Threat Events',
                                data: data.data,
                                borderColor: this.colors.cyan,
                                backgroundColor: this.createGradient(ctx, this.colors.cyan),
                                borderWidth: 3,
                                fill: true,
                                tension: 0.4,
                                pointRadius: 4,
                                pointBackgroundColor: this.colors.cyan,
                                pointBorderColor: this.colors.dark,
                                pointBorderWidth: 2,
                                pointHoverRadius: 6,
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: true,
                            plugins: {
                                legend: {
                                    display: true,
                                    labels: { color: this.colors.text, font: { size: 12 } }
                                },
                                tooltip: {
                                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                                    titleColor: this.colors.cyan,
                                    bodyColor: this.colors.text,
                                    borderColor: this.colors.cyan,
                                    borderWidth: 1,
                                    padding: 10,
                                }
                            },
                            scales: {
                                y: {
                                    beginAtZero: true,
                                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                                    ticks: { color: this.colors.muted }
                                },
                                x: {
                                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                                    ticks: { color: this.colors.muted }
                                }
                            }
                        }
                    });
                })
                .catch(err => console.error('Error loading threat timeline:', err));
        },

        /**
         * Initialize compliance breakdown chart
         */
        initComplianceBreakdown: function () {
            const ctx = document.getElementById('complianceChart');
            if (!ctx) return;

            fetch(this.endpoints.compliance)
                .then(response => response.json())
                .then(data => {
                    this.charts.compliance = new Chart(ctx, {
                        type: 'bar',
                        data: {
                            labels: data.labels,
                            datasets: [
                                {
                                    label: 'Compliant',
                                    data: data.passed,
                                    backgroundColor: this.colors.green,
                                    borderColor: this.colors.green,
                                    borderWidth: 2,
                                },
                                {
                                    label: 'Non-Compliant',
                                    data: data.failed,
                                    backgroundColor: this.colors.red,
                                    borderColor: this.colors.red,
                                    borderWidth: 2,
                                }
                            ]
                        },
                        options: {
                            indexAxis: 'y',
                            responsive: true,
                            plugins: {
                                legend: {
                                    display: true,
                                    labels: { color: this.colors.text, font: { size: 11 } }
                                },
                                tooltip: {
                                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                                    titleColor: this.colors.cyan,
                                    bodyColor: this.colors.text,
                                    borderColor: this.colors.cyan,
                                    borderWidth: 1,
                                }
                            },
                            scales: {
                                x: {
                                    beginAtZero: true,
                                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                                    ticks: { color: this.colors.muted }
                                },
                                y: {
                                    grid: { display: false },
                                    ticks: { color: this.colors.muted }
                                }
                            }
                        }
                    });
                })
                .catch(err => console.error('Error loading compliance data:', err));
        },

        /**
         * Initialize alert severity distribution donut chart
         */
        initSeverityDistribution: function () {
            const ctx = document.getElementById('severityChart');
            if (!ctx) return;

            fetch(this.endpoints.severity)
                .then(response => response.json())
                .then(data => {
                    this.charts.severity = new Chart(ctx, {
                        type: 'doughnut',
                        data: {
                            labels: ['Low', 'Medium', 'High', 'Critical'],
                            datasets: [{
                                data: [data.LOW, data.MEDIUM, data.HIGH, data.CRITICAL],
                                backgroundColor: [
                                    this.colors.green,
                                    this.colors.yellow,
                                    this.colors.orange,
                                    this.colors.red
                                ],
                                borderColor: this.colors.dark,
                                borderWidth: 2,
                            }]
                        },
                        options: {
                            responsive: true,
                            plugins: {
                                legend: {
                                    position: 'bottom',
                                    labels: { color: this.colors.text, font: { size: 12 } }
                                },
                                tooltip: {
                                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                                    titleColor: this.colors.cyan,
                                    bodyColor: this.colors.text,
                                    borderColor: this.colors.cyan,
                                    borderWidth: 1,
                                    callbacks: {
                                        label: function (context) {
                                            return context.label + ': ' + context.parsed;
                                        }
                                    }
                                }
                            }
                        }
                    });
                })
                .catch(err => console.error('Error loading severity data:', err));
        },

        /**
         * Initialize risk heatmap
         */
        initRiskHeatmap: function () {
            const ctx = document.getElementById('heatmapChart');
            if (!ctx) return;

            fetch(this.endpoints.heatmap)
                .then(response => response.json())
                .then(data => {
                    this.renderHeatmap(ctx, data);
                })
                .catch(err => console.error('Error loading heatmap data:', err));
        },

        /**
         * Render heatmap using Chart.js bubble/scatter or custom canvas
         */
        renderHeatmap: function (canvas, data) {
            const ctx = canvas.getContext('2d');
            const cellSize = 30;
            const padding = 60;
            const width = 24 * cellSize + padding;
            const height = 7 * cellSize + padding;

            canvas.width = width;
            canvas.height = height;

            // Day labels
            const days = data.days;
            const hours = Array.from({ length: 24 }, (_, i) => i);
            const maxValue = Math.max(...data.heatmap.flat());

            // Draw labels
            ctx.fillStyle = this.colors.muted;
            ctx.font = '11px Arial';

            // Hour labels (top)
            hours.forEach((hour, i) => {
                ctx.fillText(hour + ':00', padding + i * cellSize + 5, 20);
            });

            // Day labels (left)
            days.forEach((day, i) => {
                ctx.fillText(day, 5, padding + i * cellSize + 18);
            });

            // Draw heatmap cells
            data.heatmap.forEach((dayData, dayIdx) => {
                dayData.forEach((value, hourIdx) => {
                    const intensity = value / maxValue;
                    const hue = (1 - intensity) * 240; // Red (0) to Green (240)
                    const color = `hsla(${hue}, 100%, ${30 + intensity * 40}%, 0.8)`;

                    ctx.fillStyle = color;
                    ctx.fillRect(
                        padding + hourIdx * cellSize,
                        padding + dayIdx * cellSize,
                        cellSize - 1,
                        cellSize - 1
                    );

                    // Draw value if > 0
                    if (value > 0) {
                        ctx.fillStyle = this.colors.text;
                        ctx.font = 'bold 10px Arial';
                        ctx.textAlign = 'center';
                        ctx.textBaseline = 'middle';
                        ctx.fillText(
                            value,
                            padding + hourIdx * cellSize + cellSize / 2,
                            padding + dayIdx * cellSize + cellSize / 2
                        );
                    }
                });
            });
        },

        /**
         * Set up auto-refresh of metrics every 60 seconds
         */
        setupMetricsRefresh: function () {
            this.refreshMetrics();
            const interval = setInterval(() => this.refreshMetrics(), 60000);
            this.refreshIntervals.push(interval);
        },

        /**
         * Fetch and update all metrics
         */
        refreshMetrics: function () {
            fetch(this.endpoints.stats)
                .then(response => response.json())
                .then(data => {
                    this.updateMetricCard('metricThreats', data.total_threats_today);
                    this.updateMetricCard('metricCritical', data.critical_alerts_open);
                    this.updateMetricCard('metricCompliance', data.compliance_score.toFixed(1) + '%');
                    this.updateMetricCard('metricSuspicious', data.suspicious_activities_today);
                    this.updateMetricCard('metricUsers', data.active_users_today);
                    this.updateMetricCard('metricIncidents', data.total_incidents_open);
                    this.updateMetricCard('metricVulns', data.vulnerabilities_open);

                    // Update "Last Updated" timestamp
                    const lastUpdated = new Date(data.timestamp);
                    const now = new Date();
                    const diff = Math.floor((now - lastUpdated) / 1000);

                    let timeStr = 'Just now';
                    if (diff >= 60) timeStr = Math.floor(diff / 60) + ' min ago';
                    if (diff >= 3600) timeStr = Math.floor(diff / 3600) + ' hrs ago';

                    document.getElementById('lastUpdated').textContent = timeStr;
                })
                .catch(err => console.error('Error refreshing metrics:', err));
        },

        /**
         * Update metric card with animation
         */
        updateMetricCard: function (elementId, newValue) {
            const element = document.getElementById(elementId);
            if (!element) return;

            const oldValue = element.textContent;
            if (oldValue === newValue) return; // No change

            element.style.animation = 'none';
            setTimeout(() => {
                element.style.animation = 'fadeInScale 0.4s ease-out';
                element.textContent = newValue;
            }, 10);
        },

        /**
         * Set up activity feed refresh
         */
        setupActivityRefresh: function () {
            // Optional: Implement activity feed refresh if needed
        },

        /**
         * Create gradient for line chart
         */
        createGradient: function (canvas, color) {
            const gradient = canvas.getContext('2d').createLinearGradient(0, 0, 0, 400);
            gradient.addColorStop(0, color + '40');
            gradient.addColorStop(1, color + '00');
            return gradient;
        },

        destroy: function () {
            Object.values(this.charts).forEach(chart => {
                if (chart) chart.destroy();
            });
            this.refreshIntervals.forEach(interval => clearInterval(interval));
        }
    };

    // Add CSS animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes fadeInScale {
            from {
                opacity: 0.5;
                transform: scale(0.95);
            }
            to {
                opacity: 1;
                transform: scale(1);
            }
        }
    `;
    document.head.appendChild(style);

    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => dashboard.init());
    } else {
        dashboard.init();
    }

    // Cleanup on page unload
    window.addEventListener('beforeunload', () => dashboard.destroy());
})();
