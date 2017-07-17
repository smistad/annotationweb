var g_backgroundImageData;
var g_imageData;
var g_image;
var g_backgroundImage;
var g_frameNr;
var g_currentColor = null;
var g_controlPoints = [];
var g_move = false;
var g_pointToMove = -1;
var g_moveDistanceThreshold = 8;
var g_drawLine = false;


function setupSegmentation() {

    // Initialize canvas with background image
    g_context.clearRect(0, 0, g_context.canvas.width, g_context.canvas.height); // Clears the canvas
    g_context.drawImage(g_backgroundImage, 0, 0, g_canvasWidth, g_canvasHeight); // Draw background image
    g_backgroundImageData = g_context.getImageData(0,0,g_canvasWidth, g_canvasHeight).data; // Get pixel data
    // Create the image which will be put on canvas
    g_image = g_context.getImageData(0, 0, g_canvasWidth, g_canvasHeight);
    g_imageData = g_image.data;

    // Define event callbacks
    $('#canvas').mousedown(function(e) {
        // If current frame is not the frame to segment
        if(g_currentFrameNr != g_frameNr) {
            // Move slider to frame to segment
            $('#slider').slider("value", g_frameNr);
            g_currentFrameNr = g_frameNr;
            redraw();
            return;
        }

        var scale =  g_canvasWidth / $('#canvas').width();
        var mouseX = (e.pageX - this.offsetLeft)*scale;
        var mouseY = (e.pageY - this.offsetTop)*scale;
        var point = getClosestPoint(mouseX, mouseY);
        if(point >= 0) {
            // Move point
            g_move = true;
            g_pointToMove = point;
        } else {
            var section = isPointOnSpline(mouseX, mouseY);
            if(section >= 0) {
                // Insert point
                insertControlPoint(mouseX, mouseY, g_currentLabel, section);
            } else {
                // Add point at end
                addControlPoint(mouseX, mouseY, g_currentLabel);
            }
        }
        redraw();
    });

    $('#canvas').mousemove(function(e) {
        var scale =  g_canvasWidth / $('#canvas').width();
        var mouseX = (e.pageX - this.offsetLeft)*scale;
        var mouseY = (e.pageY - this.offsetTop)*scale;
        if(g_move) {
            g_controlPoints[g_pointToMove].x = mouseX;
            g_controlPoints[g_pointToMove].y = mouseY;
            redraw();
        } else {
            if(g_controlPoints.length > 0 && isPointOnSpline(mouseX, mouseY) < 0) {
                var line = {
                    x0: g_controlPoints[g_controlPoints.length - 1].x,
                    y0: g_controlPoints[g_controlPoints.length - 1].y,
                    x1: mouseX,
                    y1: mouseY
                };
                g_drawLine = line;
            } else {
                g_drawLine = false;
            }
            redraw();
        }
        e.preventDefault();
    });

    $('#canvas').mouseup(function(e) {
        g_move = false;
    });

    $('#canvas').dblclick(function(e) {
        if(g_move)
            return;
        var scale =  g_canvasWidth / $('#canvas').width();
        var mouseX = (e.pageX - this.offsetLeft)*scale;
        var mouseY = (e.pageY - this.offsetTop)*scale;
        var point = getClosestPoint(mouseX, mouseY);
        if(point >= 0) {
            g_controlPoints.splice(point, 1);
        }
        redraw();
    });


    $("#clearButton").click(function() {
        g_annotationHasChanged = true;
        g_controlPoints = [];
        $('#slider').slider('value', g_frameNr); // Update slider
        redraw();
    });

    // Set first label active
    changeLabel(g_labelButtons[0].id);
    redraw();
}

function loadSegmentationTask(image_sequence_id, frame_nr) {
    console.log('In seg task load')

    g_backgroundImage = new Image();
    g_frameNr = frame_nr;
    g_backgroundImage.src = '/show_frame/' + image_sequence_id + '/' + frame_nr + '/';
    g_backgroundImage.onload = function() {
        g_canvasWidth = this.width;
        g_canvasHeight = this.height;
        setupSegmentation();
    };

}

function getClosestPoint(x, y) {
    var minDistance = g_canvasWidth*g_canvasHeight;
    var minPoint = -1;

    for(var i = 0; i < g_controlPoints.length; i++) {
        var point = g_controlPoints[i];
        var distance = Math.sqrt((point.x-x)*(point.x-x) + (point.y-y)*(point.y-y));
        if(distance < minDistance) {
            minPoint = i;
            minDistance = distance;
        }
    }

    if(minDistance < g_moveDistanceThreshold) {
        return minPoint;
    } else {
        return -1;
    }
}

function createControlPoint(x, y, label) {
    // Find label index
    var labelIndex = 0;
    for(var i = 0; i < g_labelButtons.length; i++) {
        if(g_labelButtons[i].id == label) {
            labelIndex = i;
            break;
        }
    }

    var controlPoint = {
        x: x,
        y: y,
        label_id: label, // actual DB id
        label: labelIndex // index: only used for color
    };
    return controlPoint;
}

function insertControlPoint(x, y, label, index) {
    var controlPoint = createControlPoint(x, y, label);
    g_controlPoints.splice(index+1, 0, controlPoint);
}

function addControlPoint(x, y, label) {
    var controlPoint = createControlPoint(x, y, label);
    g_controlPoints.push(controlPoint);
}

function isPointOnSpline(pointX, pointY) {
    for(var i = 0; i < g_controlPoints.length; ++i) {
        var a = g_controlPoints[max(0, i - 1)];
        var b = g_controlPoints[i];
        var c = g_controlPoints[min(g_controlPoints.length - 1, i + 1)];
        var d = g_controlPoints[min(g_controlPoints.length - 1, i + 2)];

        var step = 0.1;
        var tension = 0.5;
        for (var t = 0.0; t < 1; t += step) {
            var x =
                (2 * t * t * t - 3 * t * t + 1) * b.x +
                (1 - tension) * (t * t * t - 2.0 * t * t + t) * (c.x - a.x) +
                (-2 * t * t * t + 3 * t * t) * c.x +
                (1 - tension) * (t * t * t - t * t) * (d.x - b.x);
            var y =
                (2 * t * t * t - 3 * t * t + 1) * b.y +
                (1 - tension) * (t * t * t - 2.0 * t * t + t) * (c.y - a.y) +
                (-2 * t * t * t + 3 * t * t) * c.y +
                (1 - tension) * (t * t * t - t * t) * (d.y - b.y);
            if(Math.sqrt((pointX-x)*(pointX-x) + (pointY-y)*(pointY-y)) < g_moveDistanceThreshold) {
                return i;
            }
        }
    }
    return -1;
}


function redraw(){
    g_context.putImageData(g_image, 0, 0);
    var controlPointSize = 6;
    g_context.lineWidth = 2;
    // Draw controlPoint
    for(var i = 0; i < g_controlPoints.length; ++i) {
        g_context.beginPath();
        var controlPoint = g_controlPoints[i];
        var label = g_labelButtons[controlPoint.label];

        var a = g_controlPoints[max(0, i-1)];
        var b = g_controlPoints[i];
        var c = g_controlPoints[min(g_controlPoints.length-1, i+1)];
        var d = g_controlPoints[min(g_controlPoints.length-1, i+2)];


        // Draw line as spline
        g_context.strokeStyle = colorToHexString(label.red, label.green, label.blue);
        var step = 0.1;
        var prev_x = -1;
        var prev_y = -1;
        var tension = 0.5;
        for(var t = 0.0; t < 1; t += step) {
            var x =
                (2*t*t*t - 3*t*t + 1)*b.x +
                (1-tension)*(t*t*t - 2.0*t*t + t)*(c.x - a.x) +
                (-2*t*t*t + 3*t*t)*c.x +
                (1-tension)*(t*t*t - t*t)*(d.x - b.x) ;
            var y =
                (2*t*t*t - 3*t*t + 1)*b.y +
                (1-tension)*(t*t*t - 2.0*t*t + t)*(c.y - a.y) +
                (-2*t*t*t + 3*t*t)*c.y +
                (1-tension)*(t*t*t - t*t)*(d.y - b.y);

            // Draw line
            if(prev_x >= 0) {
                g_context.moveTo(prev_x, prev_y);
                g_context.lineTo(x, y);
                g_context.stroke();
            }
            prev_x = x;
            prev_y = y;
        }

        // Draw control point
        g_context.fillStyle = colorToHexString(255, 255, 0);
        g_context.fillRect(b.x - controlPointSize/2, b.y - controlPointSize/2, controlPointSize, controlPointSize);
    }

    // Draw AV plane line
    if(g_controlPoints.length > 4) {
        var y0 = g_controlPoints[0].y;
        var y1 = g_controlPoints[g_controlPoints.length - 1].y;
        var x0 = g_controlPoints[0].x;
        var x1 = g_controlPoints[g_controlPoints.length - 1].x;
        var a = (y1 - y0) / (x1 - x0);
        console.log(a);
        if (Math.abs(a) < 1) {
            g_context.setLineDash([5, 5]); // dashes are 5px and spaces are 5px
            g_context.strokeStyle = colorToHexString(255, 255, 0);
            g_context.moveTo(0, -a * x1 + y1);
            g_context.lineTo(g_canvasWidth - 1, a * (g_canvasWidth - 1) - a * x1 + y1);
            g_context.stroke();
            g_context.setLineDash([]); // Clear
        }
    }


    if(g_drawLine !== false) {
        g_context.setLineDash([5, 5]); // dashes are 5px and spaces are 5px
        g_context.strokeStyle = colorToHexString(255, 255, 0);
        g_context.moveTo(g_drawLine.x0, g_drawLine.y0);
        g_context.lineTo(g_drawLine.x1, g_drawLine.y1);
        g_context.stroke();
        g_context.setLineDash([]); // Clear
    }

}

// Override redraw sequence in sequence.js
function redrawSequence() {
    if(g_currentFrameNr == g_frameNr) {
        redraw();
    } else {
        var index = g_currentFrameNr - g_startFrame;
        g_context.drawImage(g_sequence[index], 0, 0, g_canvasWidth, g_canvasHeight);
    }
}
