// automatically generated file, do not change here!
        var xValues = ['2022-01', '2022-02', '2022-03', '2022-04', '2022-05', '2022-06', '2022-07', '2022-08', '2022-09', '2022-10', '2022-11', '2022-12', '2023-01', '2023-02', '2023-03', '2023-04', '2023-05', '2023-06', '2023-07', '2023-08', '2023-09', '2023-10', '2023-11', '2023-12', '2024-01', '2024-02', '2024-03', '2024-04', '2024-05'];
        var yValues = [77.0, 247.0, 61.0, 97.0, 440.0, 401.0, 59.0, 687.0, 329.0, 161.0, 89.0, 0.0, 40.0, 104.0, 698.0, 130.0, 722.0, 601.0, 252.0, 342.0, 205.0, 348.0, 74.0, 51.0, 89.0, 148.0, 405.0, 492.0, 780.0];
        var altValues= [191.0, 1317.0, 246.0, 325.0, 2208.0, 1372.0, 132.0, 3531.0, 2251.0, 609.0, 223.0, 0.0, 98.0, 232.0, 6963.0, 660.0, 3450.0, 4739.0, 1774.0, 3045.0, 911.0, 1662.0, 382.0, 93.0, 209.0, 450.0, 2038.0, 3102.0, 8899.0];
        var barColorDist ="blue";
        var barColorAlt ="grey";

        new Chart("barplot", {
        type: "bar",
        data: {
            labels: xValues,
            datasets: [{
                label: 'Distance',
                backgroundColor: barColorDist,
                data: yValues,
                yAxisID: 'y-axis-distance'
            },
            {
                label: 'Altitude',
                backgroundColor: barColorAlt,
                data: altValues.map(value => value / 10),
                yAxisID: 'y-axis-altitude'
            }]
        },
        options: {
            legend: {display: true},
            title: {
            display: false,
            },
            tooltips: {
                callbacks: {
                    label: function(tooltipItem, data) {
                        var datasetLabel = data.datasets[tooltipItem.datasetIndex].label || '';
                        var value = tooltipItem.yLabel;
                        if (tooltipItem.datasetIndex === 1) {
                            value = value * 10; // Convert scaled value back to real value
                            return datasetLabel + ': ' + value + ' m';
                        } else {
                            return datasetLabel + ': ' + value + ' km';
                        }
                    }
                }
            },
            scales: {
                yAxes: [{
                    id: 'y-axis-distance',
                    type: 'linear',
                    position: 'left',
                    ticks: {
                        beginAtZero: true,
                        callback: function(value, index, values) {
                            return value + ' km';
                        }
                    },
                    scaleLabel: {
                        display: true,
                        labelString: 'Distance (km)'
                    }
                }, {
                    id: 'y-axis-altitude',
                    type: 'linear',
                    position: 'right',
                    ticks: {
                        beginAtZero: true,
                        callback: function(value, index, values) {
                            return value * 10 + ' m';
                        }
                    },
                    scaleLabel: {
                        display: true,
                        labelString: 'Altitude (m)'
                    }
                }],
                xAxes: [{
                    barPercentage: 1.0,
                categoryPercentage: 0.5
                }]
            }
        } });
    
