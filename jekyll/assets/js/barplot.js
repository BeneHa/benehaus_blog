// automatically generated file, do not change here!
        var xValues = ['2022-01', '2022-02', '2022-03', '2022-04', '2022-05', '2022-06', '2022-07', '2022-08', '2022-09', '2022-10', '2022-11', '2022-12', '2023-01', '2023-02', '2023-03', '2023-04', '2023-05', '2023-06', '2023-07', '2023-08', '2023-09', '2023-10'];
        var yValues = [77.0, 247.0, 61.0, 97.0, 440.0, 401.0, 59.0, 687.0, 329.0, 161.0, 89.0, 0.0, 40.0, 104.0, 698.0, 130.0, 722.0, 601.0, 252.0, 342.0, 205.0, 67.0];
        var barColors ="blue";

        new Chart("barplot", {
        type: "bar",
        data: {
            labels: xValues,
            datasets: [{
            backgroundColor: barColors,
            data: yValues
            }]
        },
        options: {
            legend: {display: false},
            title: {
            display: false,
            }
        } });
    
