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
var g_frameED = -1;
var g_frameES = -1;
var g_currentPhase = 0; // 0 == ED, 1 == ES
var g_motionModeData;
var g_motionModeImage;
var g_motionModeContext;
var g_createMotionModeImage = true;
var g_motionModeLine = -1;
var g_moveMotionModeLIne = false;


function setupSegmentation() {
    g_controlPoints.push([]); // ED
    g_controlPoints.push([]); // ES
    g_controlPoints[0].push([]); // Endo
    g_controlPoints[0].push([]); // Epi
    g_controlPoints[0].push([]); // Atrium
    g_controlPoints[1].push([]); // Endo
    g_controlPoints[1].push([]); // Epi
    g_controlPoints[1].push([]); // Atrium

    // Initialize canvas with background image
    g_context.clearRect(0, 0, g_context.canvas.width, g_context.canvas.height); // Clears the canvas
    g_context.drawImage(g_backgroundImage, 0, 0, g_canvasWidth, g_canvasHeight); // Draw background image
    g_backgroundImageData = g_context.getImageData(0,0,g_canvasWidth, g_canvasHeight).data; // Get pixel data
    // Create the image which will be put on canvas
    g_image = g_context.getImageData(0, 0, g_canvasWidth, g_canvasHeight);
    g_imageData = g_image.data;

    // Remove any previous event handlers
    $('#canvas').off();

    // Define event callbacks
    $('#canvas').mousedown(function(e) {
        /*
        // If current frame is not the frame to segment
        if(g_currentFrameNr != g_frameNr) {
            // Move slider to frame to segment
            $('#slider').slider("value", g_frameNr);
            g_currentFrameNr = g_frameNr;
            redraw();
            return;
        }
        */

        var scale =  g_canvasWidth / $('#canvas').width();
        var mouseX = (e.pageX - this.offsetLeft)*scale;
        var mouseY = (e.pageY - this.offsetTop)*scale;
        var point = getClosestPoint(mouseX, mouseY);
        if(point >= 0) {
            // Move point
            g_move = true;
            g_pointToMove = point;
        } else if(Math.abs(mouseX - g_motionModeLine) < g_moveDistanceThreshold && mouseY < g_canvasHeight/10) {
            g_moveMotionModeLIne = true;
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
        redrawSequence();
    });

    $('#canvas').mousemove(function(e) {
        var scale =  g_canvasWidth / $('#canvas').width();
        var mouseX = (e.pageX - this.offsetLeft)*scale;
        var mouseY = (e.pageY - this.offsetTop)*scale;
        var cursor = 'default';
        if(g_move) {
            cursor = 'move';
            setControlPoint(g_pointToMove, g_currentSegmentationLabel, mouseX, mouseY);
            redrawSequence();
        } else if(g_moveMotionModeLIne) {
            cursor = 'move';
            g_motionModeLine = mouseX;
            redrawSequence();
        } else {
            if(g_controlPoints[g_currentPhase][g_currentSegmentationLabel].length > 0 && isPointOnSpline(mouseX, mouseY) < 0) {
                // If mouse is not close to spline, draw dotted drawing line
                var line = {
                    x0: getControlPoint(-1, g_currentSegmentationLabel).x,
                    y0: getControlPoint(-1, g_currentSegmentationLabel).y,
                    x1: mouseX,
                    y1: mouseY
                };
                g_drawLine = line;
            } else if(Math.abs(mouseX - g_motionModeLine) < g_moveDistanceThreshold && mouseY < g_canvasHeight/10) {
                cursor = 'pointer';
            } else {
                cursor = 'pointer';
                g_drawLine = false;
            }
            redrawSequence();
        }
        $('#canvas').css({'cursor' : cursor});
        e.preventDefault();
    });

    $('#canvas').mouseup(function(e) {
        g_move = false;
        if(g_moveMotionModeLIne) {
            g_moveMotionModeLIne = false;
            g_createMotionModeImage = true;
        }
    });

    $('#canvas').mouseleave(function(e) {
        g_drawLine = false;
        redrawSequence();
    });

    $('#canvas').dblclick(function(e) {
        if(g_move)
            return;
        var scale =  g_canvasWidth / $('#canvas').width();
        var mouseX = (e.pageX - this.offsetLeft)*scale;
        var mouseY = (e.pageY - this.offsetTop)*scale;
        var point = getClosestPoint(mouseX, mouseY);
        if(point >= 0) {
            g_controlPoints[g_currentPhase][g_currentSegmentationLabel].splice(point, 1);
        }
        redrawSequence();
    });


    $("#clearButton").click(function() {
        g_annotationHasChanged = true;
        g_controlPoints = [];
        $('#slider').slider('value', g_frameNr); // Update slider
        redrawSequence();
    });

    $('#markAsED').click(function() {
        g_frameED = g_currentFrameNr;
        $('#sliderEDmark').css('background-color', 'red');
        $('#sliderEDmark').css('width', $('.ui-slider-handle').css('width'));
        $('#sliderEDmark').css('margin-left', $('.ui-slider-handle').css('margin-left'));
        $('#sliderEDmark').css('height', '100%');
        $('#sliderEDmark').css('z-index', '99');
        $('#sliderEDmark').css('left', $('.ui-slider-handle').css('left'));
        $('#sliderEDmark').css('position', 'absolute');
        $('#EDFrame').text(g_frameED);
        console.log('Frame ED set to ' + g_frameED);
    });

    $('#markAsES').click(function() {
        g_frameES = g_currentFrameNr;
        $('#sliderESmark').css('background-color', 'blue');
        $('#sliderESmark').css('width', $('.ui-slider-handle').css('width'));
        $('#sliderESmark').css('margin-left', $('.ui-slider-handle').css('margin-left'));
        $('#sliderESmark').css('height', '100%');
        $('#sliderESmark').css('z-index', '99');
        $('#sliderESmark').css('left', $('.ui-slider-handle').css('left'));
        $('#sliderESmark').css('position', 'absolute');
        $('#ESFrame').text(g_frameES);
        console.log('Frame ES set to ' + g_frameES);
    });

    $('#slider').resize(function() {
        // TODO Move slider ED/ES mark
    });

    $('#segmentED').click(function() {
        g_currentPhase = 0;
        goToFrame(g_frameED);
    });

    $('#segmentES').click(function() {
        g_currentPhase = 1;
        goToFrame(g_frameES);
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

function createMotionModeCanvas() {
    if(g_motionModeLine == -1) {
        g_motionModeLine = g_canvasWidth / 2;
    }
    // Create canvas
    var canvas = document.getElementById('m-mode-canvas');
    canvas.setAttribute('width', g_framesLoaded);
    canvas.setAttribute('height', g_canvasHeight);
    // IE stuff
    if(typeof G_vmlCanvasManager != 'undefined') {
        canvas = G_vmlCanvasManager.initElement(canvas);
    }
    g_motionModeContext = canvas.getContext("2d");
    var width = g_framesLoaded;
    g_motionModeContext.clearRect(0, 0, g_motionModeContext.canvas.width, g_motionModeContext.canvas.height); // Clears the canvas

    if(g_createMotionModeImage) {
        g_motionModeImage = g_motionModeContext.getImageData(0, 0, width, g_canvasHeight);
        g_motionModeData = g_motionModeImage.data;
        console.log('Frames: ' + g_framesLoaded)
        console.log('Width: ' + g_canvasWidth)
        console.log('Height: ' + g_canvasHeight)
        // Go through entire sequence
        for (var t = 0; t < g_framesLoaded; t++) {
            var frame = g_sequence[t];
            var dummyCanvas = document.createElement('canvas');
            dummyCanvas.setAttribute('width', g_canvasWidth);
            dummyCanvas.setAttribute('height', g_canvasHeight);
            var dummyContext = dummyCanvas.getContext('2d');
            dummyContext.drawImage(frame, 0, 0);
            var pixels = dummyContext.getImageData(g_motionModeLine, 0, 1, g_canvasHeight).data;
            for (var y = 0; y < g_canvasHeight; y++) {
                var value = pixels[y*4]
                //console.log(value)
                g_motionModeData[(t + y * width) * 4 + 0] = value;
                g_motionModeData[(t + y * width) * 4 + 1] = value;
                g_motionModeData[(t + y * width) * 4 + 2] = value;
                g_motionModeData[(t + y * width) * 4 + 3] = 255;
            }
        }
        g_createMotionModeImage = false;
    }
    g_motionModeContext.putImageData(g_motionModeImage, 0, 0);

    // Draw line
    g_motionModeContext.beginPath();
    //g_motionModeContext.setLineDash([5, 5]); // dashes are 5px and spaces are 5px
    g_motionModeContext.strokeStyle = colorToHexString(0, 255, 0);
    g_motionModeContext.moveTo(g_currentFrameNr, 0);
    g_motionModeContext.lineTo(g_currentFrameNr, g_canvasHeight);
    g_motionModeContext.stroke();
    g_motionModeContext.setLineDash([]); // Clear

    $('#m-mode-canvas').css('width', '100%');
    $('#m-mode-canvas').css('height', g_canvasHeight+'px');
}

function getClosestPoint(x, y) {
    var minDistance = g_canvasWidth*g_canvasHeight;
    var minPoint = -1;

    for(var i = 0; i < g_controlPoints[g_currentPhase][g_currentSegmentationLabel].length; i++) {
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
    g_controlPoints[g_currentPhase][g_currentSegmentationLabel].splice(index+1, 0, controlPoint);
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
    g_controlPoints[g_currentPhase][g_currentSegmentationLabel].push(controlPoint);
}

function getControlPoint(index, label) {
    if(index === -1) {
        index = g_controlPoints[g_currentPhase][label].length-1;
    }
    return g_controlPoints[g_currentPhase][label][index];
}

function setControlPoint(index, label, x, y) {
    g_controlPoints[g_currentPhase][label][index].x = x;
    g_controlPoints[g_currentPhase][label][index].y = y;

}

function isPointOnSpline(pointX, pointY) {
    for(var i = 0; i < g_controlPoints[g_currentPhase][g_currentSegmentationLabel].length; ++i) {
        var a = getControlPoint(max(0, i - 1), g_currentSegmentationLabel);
        var b = getControlPoint(i, g_currentSegmentationLabel);
        var c = getControlPoint(min(g_controlPoints[g_currentPhase][g_currentSegmentationLabel].length - 1, i + 1), g_currentSegmentationLabel);
        var d = getControlPoint(min(g_controlPoints[g_currentPhase][g_currentSegmentationLabel].length - 1, i + 2), g_currentSegmentationLabel);

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
    //g_context.putImageData(g_image, 0, 0);
    var index = g_currentFrameNr - g_startFrame;
    g_context.drawImage(g_sequence[index], 0, 0, g_canvasWidth, g_canvasHeight);
    var controlPointSize = 6;
    g_context.lineWidth = 2;

    // For left atrium, insert endo endpoints
    if(g_controlPoints[g_currentPhase][0].length > 1 && g_controlPoints[g_currentPhase][2].length > 0) {
        g_controlPoints[g_currentPhase][2].splice(0, 0, getControlPoint(-1, 0));
        g_controlPoints[g_currentPhase][2].push(getControlPoint(0, 0));
    }

    if(g_controlPoints[g_currentPhase][0].length > 1 && g_controlPoints[g_currentPhase][1].length > 0) {
        var startPoint = getControlPoint(0, 1);
        var endPoint = getControlPoint(-1, 1);
        var snap1 = snapToAVLine(startPoint.x, startPoint.y);
        var snap2 = snapToAVLine(endPoint.x, endPoint.y);
        g_controlPoints[g_currentPhase][1].splice(0, 0, createControlPoint(snap1.x, snap1.y, 1));
        if(g_controlPoints[g_currentPhase][1].length > 5)
            g_controlPoints[g_currentPhase][1].push(createControlPoint(snap2.x, snap2.y, 1));
    }

    // Draw controlPoint
    for(var labelIndex = 0; labelIndex < 3; labelIndex++) {
        for (var i = 0; i < g_controlPoints[g_currentPhase][labelIndex].length; ++i) {
            g_context.beginPath();
            var a = getControlPoint(max(0, i - 1), labelIndex);
            var b = getControlPoint(i, labelIndex);
            var c = getControlPoint(min(g_controlPoints[g_currentPhase][labelIndex].length - 1, i + 1), labelIndex);
            var d = getControlPoint(min(g_controlPoints[g_currentPhase][labelIndex].length - 1, i + 2), labelIndex);

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
    if(g_controlPoints[g_currentPhase][0].length > 1 && g_controlPoints[g_currentPhase][2].length > 0) {
        g_controlPoints[g_currentPhase][2].splice(0, 1);
        g_controlPoints[g_currentPhase][2].splice(g_controlPoints[g_currentPhase][2].length - 1, 1);
    }
    if(g_controlPoints[g_currentPhase][0].length > 1 && g_controlPoints[g_currentPhase][1].length > 0) {
        g_controlPoints[g_currentPhase][1].splice(0, 1);
        if(g_controlPoints[g_currentPhase][1].length > 5)
            g_controlPoints[g_currentPhase][1].splice(g_controlPoints[g_currentPhase][1].length - 1, 1);
    }

    // Draw AV plane line
    if(g_controlPoints[g_currentPhase][0].length > 4) {
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
    createMotionModeCanvas();
    if((g_currentPhase == 0 && g_currentFrameNr == g_frameED) || (g_currentPhase == 1 && g_currentFrameNr == g_frameES)) {
        redraw();
    } else {
        var index = g_currentFrameNr - g_startFrame;
        g_context.drawImage(g_sequence[index], 0, 0, g_canvasWidth, g_canvasHeight);
    }

    // Draw motion mode line
    g_context.beginPath();
    g_context.strokeStyle = colorToHexString(0, 255, 255);
    // Draw solid line where it can be moved
    g_context.moveTo(g_motionModeLine, 0);
    g_context.lineTo(g_motionModeLine, g_canvasHeight/10);
    g_context.stroke();
    // Draw dashed line for the rest
    g_context.setLineDash([5, 5]); // dashes are 5px and spaces are 5px
    g_context.moveTo(g_motionModeLine, g_canvasHeight/10);
    g_context.lineTo(g_motionModeLine, g_canvasHeight);
    g_context.stroke();
    g_context.setLineDash([]); // Clear
}

// Override of annotationweb.js
function changeLabel(label_id) {
    console.log('changing label to: ', label_id)
    g_currentSegmentationLabel = label_id;
}