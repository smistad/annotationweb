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
var g_currentSegmentationLabel = 0;


function setupSegmentation() {
    g_controlPoints.push([]); // Endo
    g_controlPoints.push([]); // Epi
    g_controlPoints.push([]); // Atrium

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
                insertControlPoint(mouseX, mouseY, g_currentSegmentationLabel, section);
            } else {
                // Add point at end
                addControlPoint(mouseX, mouseY, g_currentSegmentationLabel);
            }
        }
        redraw();
    });

    $('#canvas').mousemove(function(e) {
        var scale =  g_canvasWidth / $('#canvas').width();
        var mouseX = (e.pageX - this.offsetLeft)*scale;
        var mouseY = (e.pageY - this.offsetTop)*scale;
        if(g_move) {
            setControlPoint(g_pointToMove, g_currentSegmentationLabel, mouseX, mouseY);
            redraw();
        } else {
            if(g_controlPoints[g_currentSegmentationLabel].length > 0 && isPointOnSpline(mouseX, mouseY) < 0) {
                var line = {
                    x0: getControlPoint(-1, g_currentSegmentationLabel).x,
                    y0: getControlPoint(-1, g_currentSegmentationLabel).y,
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

    $('#canvas').mouseleave(function(e) {
        g_drawLine = false;
        redraw();
    });

    $('#canvas').dblclick(function(e) {
        if(g_move)
            return;
        var scale =  g_canvasWidth / $('#canvas').width();
        var mouseX = (e.pageX - this.offsetLeft)*scale;
        var mouseY = (e.pageY - this.offsetTop)*scale;
        var point = getClosestPoint(mouseX, mouseY);
        if(point >= 0) {
            g_controlPoints[g_currentSegmentationLabel].splice(point, 1);
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
    changeLabel(0);
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

    for(var i = 0; i < g_controlPoints[g_currentSegmentationLabel].length; i++) {
        var point = getControlPoint(i, g_currentSegmentationLabel);
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
    g_controlPoints[g_currentSegmentationLabel].splice(index+1, 0, controlPoint);
}

function snapToAVLine(x, y) {
    // See https://en.wikipedia.org/wiki/Distance_from_a_point_to_a_line
    var y1 = getControlPoint(0, 0).y;
    var y2 = getControlPoint(-1, 0).y;
    var x1 = getControlPoint(0, 0).x;
    var x2 = getControlPoint(-1, 0).x;
    var a = (y2 - y1);
    var b = -(x2 - x1);
    var c = x2*y1 - y2*x1;
    var distance = Math.abs(a*x + b*y + c) / Math.sqrt(a*a + b*b);
    // Calculate new position
    x = (b*(b*x - a*y) - a*c) / (a*a + b*b);
    y = (a*(-b*x + a*y) - b*c) / (a*a + b*b);

    return {
        distance: distance,
        x: x,
        y: y
    };
}

function addControlPoint(x, y, label) {
    var controlPoint = createControlPoint(x, y, label);
    g_controlPoints[g_currentSegmentationLabel].push(controlPoint);
}

function getControlPoint(index, label) {
    if(index === -1) {
        index = g_controlPoints[label].length-1;
    }
    return g_controlPoints[label][index];
}

function setControlPoint(index, label, x, y) {
    g_controlPoints[label][index].x = x;
    g_controlPoints[label][index].y = y;

}

function isPointOnSpline(pointX, pointY) {
    for(var i = 0; i < g_controlPoints[g_currentSegmentationLabel].length; ++i) {
        var a = getControlPoint(max(0, i - 1), g_currentSegmentationLabel);
        var b = getControlPoint(i, g_currentSegmentationLabel);
        var c = getControlPoint(min(g_controlPoints[g_currentSegmentationLabel].length - 1, i + 1), g_currentSegmentationLabel);
        var d = getControlPoint(min(g_controlPoints[g_currentSegmentationLabel].length - 1, i + 2), g_currentSegmentationLabel);

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

    // For left atrium, insert endo endpoints
    if(g_controlPoints[0].length > 1 && g_controlPoints[2].length > 0) {
        g_controlPoints[2].splice(0, 0, getControlPoint(-1, 0));
        g_controlPoints[2].push(getControlPoint(0, 0));
    }

    if(g_controlPoints[0].length > 1 && g_controlPoints[1].length > 0) {
        var startPoint = getControlPoint(0, 1);
        var endPoint = getControlPoint(-1, 1);
        var snap1 = snapToAVLine(startPoint.x, startPoint.y);
        var snap2 = snapToAVLine(endPoint.x, endPoint.y);
        g_controlPoints[1].splice(0, 0, createControlPoint(snap1.x, snap1.y, 1));
        if(g_controlPoints[1].length > 5)
            g_controlPoints[1].push(createControlPoint(snap2.x, snap2.y, 1));
    }

    // Draw controlPoint
    for(var labelIndex = 0; labelIndex < 3; labelIndex++) {
        for (var i = 0; i < g_controlPoints[labelIndex].length; ++i) {
            g_context.beginPath();
            var a = getControlPoint(max(0, i - 1), labelIndex);
            var b = getControlPoint(i, labelIndex);
            var c = getControlPoint(min(g_controlPoints[labelIndex].length - 1, i + 1), labelIndex);
            var d = getControlPoint(min(g_controlPoints[labelIndex].length - 1, i + 2), labelIndex);

            var label = getLabelWithId(labelIndex);

            // Draw line as spline
            g_context.strokeStyle = colorToHexString(label.red, label.green, label.blue);
            var step = 0.1;
            var prev_x = -1;
            var prev_y = -1;
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

                // Draw line
                if (prev_x >= 0) {
                    g_context.moveTo(prev_x, prev_y);
                    g_context.lineTo(x, y);
                    g_context.stroke();
                }
                prev_x = x;
                prev_y = y;
            }

            // Draw control point
            g_context.fillStyle = colorToHexString(255, 255, 0);
            g_context.fillRect(b.x - controlPointSize / 2, b.y - controlPointSize / 2, controlPointSize, controlPointSize);
        }
    }

    // Remove inserted LA endpoints
    if(g_controlPoints[0].length > 1 && g_controlPoints[2].length > 0) {
        g_controlPoints[2].splice(0, 1);
        g_controlPoints[2].splice(g_controlPoints[2].length - 1, 1);
    }
    if(g_controlPoints[0].length > 1 && g_controlPoints[1].length > 0) {
        g_controlPoints[1].splice(0, 1);
        if(g_controlPoints[1].length > 5)
            g_controlPoints[1].splice(g_controlPoints[1].length - 1, 1);
    }

    // Draw AV plane line
    if(g_controlPoints[0].length > 4) {
        var y0 = getControlPoint(0, 0).y;
        var y1 = getControlPoint(-1, 0).y;
        var x0 = getControlPoint(0, 0).x;
        var x1 = getControlPoint(-1, 0).x;
        var a = (y1 - y0) / (x1 - x0);
        if(Math.abs(a) < 1) {
            g_context.beginPath();
            g_context.setLineDash([5, 5]); // dashes are 5px and spaces are 5px
            g_context.strokeStyle = colorToHexString(255, 255, 0);
            g_context.moveTo(0, -a * x1 + y1);
            g_context.lineTo(g_canvasWidth - 1, a * (g_canvasWidth - 1) - a * x1 + y1);
            g_context.stroke();
            g_context.setLineDash([]); // Clear
        }
    }

    if(g_drawLine !== false) {
        g_context.beginPath();
        g_context.setLineDash([5, 5]); // dashes are 5px and spaces are 5px
        var label = getLabelWithId(g_currentSegmentationLabel);
        g_context.strokeStyle = colorToHexString(label.red, label.green, label.blue);
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

// Override of annotationweb.js
function changeLabel(label_id) {
    console.log('changing label to: ', label_id)
    g_currentSegmentationLabel = label_id;
}