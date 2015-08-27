// Sensor Data Chart (amcharts.js)
var accel_chart;
var angr_chart;
var mag_chart;
var chartCursor;
const MAX_DATAPOINT_NUM = 200

// Attitude Display (three.js)
var scene, camera, renderer;
var cube;

function init_charts() {
    AmCharts.ready(function () {
        accel_chart = new AmCharts.AmSerialChart();
        accel_chart = make_xyz_chart();
        accel_chart.write("accel-chart");

        angr_chart = new AmCharts.AmSerialChart();
        angr_chart = make_xyz_chart();
        angr_chart.write("angr-chart");

        mag_chart = new AmCharts.AmSerialChart();
        mag_chart = make_xyz_chart();
        mag_chart.write("mag-chart");
    });
}

function make_xyz_chart() {
    var chart = new AmCharts.AmSerialChart();
    chart.dataProvider = [];
    chart.categoryField = "time";
    chart.balloon.bulletSize = 5;

    var valueAxis = new AmCharts.ValueAxis();
    chart.addValueAxis(valueAxis);

    for (var i = 0; i < 3; i++) {
        var graph = new AmCharts.AmGraph();
        graph.hideBulletsCount = 20;
        graph.bullet = "round";
        graph.bulletColor = "#FFFFFF";
        graph.useLineColorForBulletBorder = true
        graph.bulletBorderAlpha = 1;
        chart.addGraph(graph);
    }

    chart.graphs[0].valueField = "x";
    chart.graphs[0].lineColor = "red";
    chart.graphs[1].valueField = "y";
    chart.graphs[1].lineColor = "green";
    chart.graphs[2].valueField = "z";
    chart.graphs[2].lineColor = "blue";
    chart.addGraph(graph);
    /*
    var chart_scrollbar = new AmCharts.ChartScrollbar();
    chart.addChartScrollbar(chart_scrollbar);
    */
    return chart;
}

function init_threejs() {
    var target_obj = $("#attitude-data-area");
    var renderSize = target_obj.width()*0.8;
    scene = new THREE.Scene();

    camera = new THREE.PerspectiveCamera( 75, 1, 1, 10000 );
    camera.position.z = 1000;

    cube = new THREE.Mesh(
        new THREE.BoxGeometry( 600, 600, 300 ),
        new THREE.MeshBasicMaterial({
            color: 0xff0000,
            wireframe: true
        }));

    scene.add( cube );

    cube.quaternion =  new THREE.Quaternion(0,0,0,0);

    renderer = new THREE.WebGLRenderer();
    renderer.setSize( renderSize, renderSize );

    target_obj.append(renderer.domElement);
}

function update() {
    $.get('/alldata', function(data){
        var data = JSON.parse(data)
        if (data.result == "successed") {

            $("#time").text(data.time.toFixed(2) + " sec");
            $("#message").text("");

            accel_chart.dataProvider.push({
                'time': data.time,
                'x': data.acceleration[0],
                'y': data.acceleration[1],
                'z': data.acceleration[2]
            });
            if (accel_chart.dataProvider.length > MAX_DATAPOINT_NUM) {
                accel_chart.dataProvider.shift();
            }
            accel_chart.validateData();

            angr_chart.dataProvider.push({
                'time': data.time,
                'x': data.angular_rate[0],
                'y': data.angular_rate[1],
                'z': data.angular_rate[2]
            });
            if (angr_chart.dataProvider.length > MAX_DATAPOINT_NUM) {
                angr_chart.dataProvider.shift();
            }
            angr_chart.validateData();

            mag_chart.dataProvider.push({
                'time': data.time,
                'x': data.magnetic[0],
                'y': data.magnetic[1],
                'z': data.magnetic[2]
            });
            if (mag_chart.dataProvider.length > MAX_DATAPOINT_NUM) {
                mag_chart.dataProvider.shift();
            }
            mag_chart.validateData();

            var qtn = data.quaternion;
            cube.quaternion.set(qtn[0], qtn[1], qtn[2], qtn[3]);
            renderer.render(scene, camera);

            var vel = data.velocity;
            var pos = data.position;
            $("#position-data-area").empty()
            $("#position-data-area").append("<p>vx:"+vel[0]+"vy:"+vel[1]+"vz:"+vel[2]+"</p>");
            $("#position-data-area").append("<p>rx:"+pos[0]+"ry:"+pos[1]+"rz:"+pos[2]+"</p>");

        }else{
            $("#message").text(data.message);
        }
        setTimeout(update, 0);
    });
}

$(function(){
    init_threejs();
    init_charts();
    update();
});
