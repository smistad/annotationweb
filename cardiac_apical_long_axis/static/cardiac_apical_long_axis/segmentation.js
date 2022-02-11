var g_backgroundImageData;
var g_imageData;
var g_image;
var g_backgroundImage;
var g_frameNr;
var g_currentColor = null;
var g_controlPoints = {}; // control point dictionary [key_frame_nr] contains a dictionary/map of objects with a dictionary with label: label data, control_points: list
var g_currentObject = 0; // Which index in g_controlPoints[key_frame_nr] list we are in
var g_move = false;
var g_pointToMove = -1;
var g_labelToMove = -1;
var g_moveDistanceThreshold = 8;
var g_drawLine = false;
var g_currentSegmentationLabel = 0;
var g_motionModeData;
var g_motionModeImage;
var g_motionModeContext;
var g_createMotionModeImage = 0;
var g_motionModeLine = -1;
var g_moveMotionModeLIne = false;
var g_targetFrameTypes = {};
var g_currentLabel = -1;

function getLabelIdxWithId(id) {
    for(var i = 0; i < g_labelButtons.length; i++) {
        if(g_labelButtons[i].id == id) {
            return i;
        }
    }
}


function getMaxObjectID() {
    var max = -1;
    for(var key in g_controlPoints[g_currentFrameNr]) {
        key = parseInt(key); // dictionary keys are strings
        if(key > max)
            max = key;
    }
    return max;
}

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

        var scale =  g_canvasWidth / $('#canvas').width();
        var mouseX = (e.pageX - this.offsetLeft)*scale;
        var mouseY = (e.pageY - this.offsetTop)*scale;
        var point = getClosestPoint(mouseX, mouseY);
        if(point !== false) {
            // Activate object of this point
            $('.labelButton').removeClass('activeLabel');
            $('#labelButton' + point.label_idx).addClass('activeLabel');
            g_currentLabel = getLabelIdxWithId(point.label_idx);
            g_currentObject = g_currentLabel;
            // Move point
            g_move = true;
            g_pointToMove = point.index;
            g_labelToMove = point.label_idx;
        } else if(Math.abs(mouseX - g_motionModeLine) < g_moveDistanceThreshold && mouseY < g_canvasHeight/10) {
            g_moveMotionModeLIne = true;
        } else {
            var section = isPointOnSpline(mouseX, mouseY);
            if(section >= 0) {
                // Insert point
                insertControlPoint(mouseX, mouseY, g_labelButtons[g_currentLabel].id, section);
            } else {
                addControlPointsForNewFrame(g_currentFrameNr);
                // Add point at end
                addControlPoint(mouseX, mouseY, g_currentFrameNr, g_currentObject, g_labelButtons[g_currentLabel].id, g_shiftKeyPressed);
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
            setControlPoint(g_pointToMove, g_currentObject, mouseX, mouseY);
            redrawSequence();
        } else {
            if(!e.ctrlKey &&
                g_currentFrameNr in g_controlPoints &&
                g_currentObject in g_controlPoints[g_currentFrameNr] &&
                g_controlPoints[g_currentFrameNr][g_currentObject].control_points.length > 0 &&
                isPointOnSpline(mouseX, mouseY) < 0) {
                // If mouse is not close to spline, draw dotted drawing line
                var line = {
                    x0: getControlPoint(-1, g_currentObject).x,
                    y0: getControlPoint(-1, g_currentObject).y,
                    x1: mouseX,
                    y1: mouseY
                };
                g_drawLine = line;
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
            g_createMotionModeImage = 0;
            redrawSequence();
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
        if(point !== false) {
            g_controlPoints[g_currentFrameNr][g_currentObject].control_points.splice(point.index, 1);
        }
        redrawSequence();
    });


    $("#clearButton").click(function() {
        g_annotationHasChanged = true;
        // TODO fix
        redrawSequence();
    });


    $("#addNormalFrameButton").click(function() {
        setPlayButton(false);
        if(g_targetFrames.includes(g_currentFrameNr)) // Already exists
            return;
        addKeyFrame(g_currentFrameNr, '#555555');
        g_targetFrameTypes[g_currentFrameNr] = 'Normal';
        g_currentTargetFrameIndex = g_targetFrames.length-1;
    });

    $("#addEDFrameButton").click(function() {
        setPlayButton(false);
        if(g_targetFrames.includes(g_currentFrameNr)) // Already exists
            return;
        addKeyFrame(g_currentFrameNr, '#CC3434');
        g_targetFrameTypes[g_currentFrameNr] = 'ED';
        g_currentTargetFrameIndex = g_targetFrames.length-1;
    });

    $("#addESFrameButton").click(function() {
        setPlayButton(false);
        if(g_targetFrames.includes(g_currentFrameNr)) // Already exists
            return;
        addKeyFrame(g_currentFrameNr, '#0077b3');
        g_targetFrameTypes[g_currentFrameNr] = 'ES';
        g_currentTargetFrameIndex = g_targetFrames.length-1;
    });

    $('#copyAnnotation').click(function() {
        // Verify that we are on a target frame;
        if(g_targetFrames.indexOf(g_currentFrameNr) < 0 || g_targetFrames.length === 1)
            return;

        // Find previous frame
        var frame_index = g_targetFrames.findIndex(index => index === g_currentFrameNr);
        var copy_index = frame_index - 1;
        if(copy_index < 0)
            return;

        // Copy and potentially replace previous segmentation
        g_controlPoints[g_currentFrameNr] = JSON.parse(JSON.stringify(g_controlPoints[g_targetFrames[copy_index]])); // Hack for doing deep copy
        redrawSequence();
    });


    // Set first label active
    changeLabel(g_labelButtons[0].id);
    redraw();
}

function loadSegmentationTask(image_sequence_id) {
    g_backgroundImage = new Image();
    g_frameNr = 0;
    g_backgroundImage.src = '/show_frame/' + image_sequence_id + '/' + 0 + '/' + g_taskID + '/';
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

    if(g_createMotionModeImage != g_framesLoaded) {
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
        g_createMotionModeImage = g_framesLoaded;
        console.log('Finished creating m-mode')
    }
    g_motionModeContext.putImageData(g_motionModeImage, 0, 0);

    // Draw line
    g_motionModeContext.lineWidth = 1;
    g_motionModeContext.beginPath();
    g_motionModeContext.strokeStyle = colorToHexString(0, 255, 0);
    g_motionModeContext.moveTo(g_currentFrameNr, 0);
    g_motionModeContext.lineTo(g_currentFrameNr, g_canvasHeight);
    g_motionModeContext.stroke();

    $('#m-mode-canvas').css('width', '100%');
    $('#m-mode-canvas').css('height', '200px');
}


function addControlPointsForNewFrame(frameNr) {
    if(!(g_targetFrames.includes(frameNr))) { // Target frame must be created first!
        alert('You can only add annotations to target frame. Select a target frame or create a new one.');
        return;
    }
    if(frameNr in g_controlPoints) // Already exists
        return;
    g_controlPoints[frameNr] = {};
}

function getClosestPoint(x, y) {
    var minDistance = g_canvasWidth*g_canvasHeight;
    var minPoint = -1;
    var minLabel = -1;
    var minObject = -1;

    for(var j in g_controlPoints[g_currentFrameNr]) {
        for(var i = 0; i < g_controlPoints[g_currentFrameNr][j].control_points.length; i++) {
            var point = getControlPoint(i, j);
            var distance = Math.sqrt((point.x - x) * (point.x - x) + (point.y - y) * (point.y - y));
            if(distance < minDistance) {
                minPoint = i;
                minDistance = distance;
                minLabel = g_controlPoints[g_currentFrameNr][j].label.id;
                minObject = j;
            }
        }
    }

    if(minDistance < g_moveDistanceThreshold) {
        return {index: minPoint, label_idx: minLabel, object: minObject};
    } else {
        return false;
    }
}

function createControlPoint(x, y, label, uncertain) {
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
        label: labelIndex, // index: only used for color
        uncertain: uncertain    // whether the user is uncertain about this point or not
    };
    return controlPoint;
}

function insertControlPoint(x, y, label, index) {
    var controlPoint = createControlPoint(x, y, label, g_shiftKeyPressed);
    g_controlPoints[g_currentFrameNr][g_currentObject].control_points.splice(index+1, 0, controlPoint);
}

function addControlPoint(x, y, target_frame, object, label, uncertain) {
    console.log('Adding control point for ' + target_frame + ' object ' + object)
    var controlPoint = createControlPoint(x, y, label, uncertain);
    if(!(object in g_controlPoints[target_frame])) // add object if it doesn't exist
        g_controlPoints[target_frame][object] = {label: g_labelButtons[getLabelIdxWithId(label)], control_points: []};
    g_controlPoints[target_frame][object].control_points.push(controlPoint);
}

function getControlPoint(index, object) {
    if(index < 0) {
        index = g_controlPoints[g_currentFrameNr][object].control_points.length+index;
    }
    return g_controlPoints[g_currentFrameNr][object].control_points[index];
}

function setControlPoint(index, object, x, y) {
    g_controlPoints[g_currentFrameNr][object].control_points[index].x = x;
    g_controlPoints[g_currentFrameNr][object].control_points[index].y = y;
}

function isPointOnSpline(pointX, pointY) {
    for(var object in g_controlPoints[g_currentFrameNr]) {
        for (var i = 0; i < g_controlPoints[g_currentFrameNr][object].control_points.length; ++i) {
            var a = getControlPoint(max(0, i - 1), object);
            var b = getControlPoint(i, object);
            var c = getControlPoint(min(g_controlPoints[g_currentFrameNr][object].control_points.length - 1, i + 1), object);
            var d = getControlPoint(min(g_controlPoints[g_currentFrameNr][object].control_points.length - 1, i + 2), object);

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
                if (Math.sqrt((pointX - x) * (pointX - x) + (pointY - y) * (pointY - y)) < g_moveDistanceThreshold) {
                    return i;
                }
            }
        }
    }
    return -1;
}


function redraw(){
    var index = g_currentFrameNr - g_startFrame;
    g_context.drawImage(g_sequence[index], 0, 0, g_canvasWidth, g_canvasHeight);

    if(!(g_currentFrameNr in g_controlPoints))
        return;

    var controlPointSize = 6;
    g_context.lineWidth = 2;

    for(var i = 0; i < 4; ++i) {
        if(!(i in g_controlPoints[g_currentFrameNr])) {
            g_controlPoints[g_currentFrameNr][i] = {label: g_labelButtons[i], control_points: []};
        }
    }

    // For left atrium, insert endo endpoints
    if (g_controlPoints[g_currentFrameNr][0].control_points.length > 1 && g_controlPoints[g_currentFrameNr][2].control_points.length > 0) {
        g_controlPoints[g_currentFrameNr][2].control_points.splice(0, 0, getControlPoint(-1, 0));
        g_controlPoints[g_currentFrameNr][2].control_points.push(getControlPoint(0, 0));
    }
    // For aorta, insert endo endpoints
    if (g_controlPoints[g_currentFrameNr][0].control_points.length > 1 && g_controlPoints[g_currentFrameNr][3].control_points.length > 0) {
        g_controlPoints[g_currentFrameNr][3].control_points.splice(0, 0, getControlPoint(-2, 0));
        g_controlPoints[g_currentFrameNr][3].control_points.push(getControlPoint(-1, 0));
    }

    // Draw straight line from epicard endpoints to LV endoendpoints
    if (g_controlPoints[g_currentFrameNr][0].control_points.length > 1 && g_controlPoints[g_currentFrameNr][1].control_points.length > 0) {
        var startPointEpi = getControlPoint(0, 1);
        var endPointEpi = getControlPoint(-1, 1);
        var startPointEndo = getControlPoint(0, 0);
        var endPointEndo = getControlPoint(-2, 0);
        g_context.beginPath();
        g_context.setLineDash([5, 5]); // dashes are 5px and spaces are 5px
        g_context.strokeStyle = colorToHexString(0, 0, 255);
        g_context.moveTo(startPointEpi.x, startPointEpi.y);
        g_context.lineTo(startPointEndo.x, startPointEndo.y);
        g_context.stroke();
        g_context.moveTo(endPointEpi.x, endPointEpi.y);
        g_context.lineTo(endPointEndo.x, endPointEndo.y);
        g_context.stroke();
        g_context.setLineDash([]); // Clear
    }

    // Draw controlPoint
    for(var labelIndex = 0; labelIndex < 4; labelIndex++) {
        if(!(labelIndex in g_controlPoints[g_currentFrameNr]))
            continue;
        var label = g_controlPoints[g_currentFrameNr][labelIndex].label;
        for(var i = 0; i < g_controlPoints[g_currentFrameNr][labelIndex].control_points.length; ++i) {
            g_context.beginPath();
            var a = getControlPoint(max(0, i - 1), labelIndex);
            var b = getControlPoint(i, labelIndex);
            var c = getControlPoint(min(g_controlPoints[g_currentFrameNr][labelIndex].control_points.length - 1, i + 1), labelIndex);
            var d = getControlPoint(min(g_controlPoints[g_currentFrameNr][labelIndex].control_points.length - 1, i + 2), labelIndex);
            if(labelIndex === 0 && i === g_controlPoints[g_currentFrameNr][labelIndex].control_points.length - 3) { // Special treatment of endocard, where last point connect to aorta annulus should not be rounded but straighted
                d = getControlPoint(min(g_controlPoints[g_currentFrameNr][labelIndex].control_points.length - 1, i + 1), labelIndex);
            }

            // Draw line as spline
            g_context.strokeStyle = colorToHexString(label.red, label.green, label.blue);
            var step = 0.1;
            var prev_x = -1;
            var prev_y = -1;
            var tension = 0.5;
            if(b.uncertain || c.uncertain) {
                // Draw uncertain segments with dashed line
                g_context.setLineDash([1, 5]); // dashes are 5px and spaces are 5px
            } else {
                g_context.setLineDash([]); // reset
            }
            for(var t = 0.0; t < 1; t += step) {
                if(labelIndex < 4 && i === g_controlPoints[g_currentFrameNr][labelIndex].control_points.length-1) // Do not draw after last control point, except for RV
                    break;
                if(labelIndex === 5 && i >= g_controlPoints[g_currentFrameNr][labelIndex].control_points.length - 3) // Do not draw last two lines for LVOT
                    break
                if(
                    labelIndex === 0 &&
                    i === g_controlPoints[g_currentFrameNr][0].control_points.length-2 &&
                    g_controlPoints[g_currentFrameNr][0].control_points.length > 4
                        ) // Skip drawing last of endo (LVout)
                    break;
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
            g_context.fillRect(b.x - controlPointSize / 2, b.y - controlPointSize / 2, controlPointSize, controlPointSize);
        }
    }

    // Remove inserted LA and aorta endpoints
    if (g_controlPoints[g_currentFrameNr][0].control_points.length > 1 && g_controlPoints[g_currentFrameNr][2].control_points.length > 0) {
        g_controlPoints[g_currentFrameNr][2].control_points.splice(0, 1);
        g_controlPoints[g_currentFrameNr][2].control_points.splice(g_controlPoints[g_currentFrameNr][2].control_points.length - 1, 1);
    }
    if (g_controlPoints[g_currentFrameNr][0].control_points.length > 1 && g_controlPoints[g_currentFrameNr][3].control_points.length > 0) {
        g_controlPoints[g_currentFrameNr][3].control_points.splice(0, 1);
        g_controlPoints[g_currentFrameNr][3].control_points.splice(g_controlPoints[g_currentFrameNr][3].control_points.length - 1, 1);
    }

     // Draw aorta annulus plane line
     if(0 in g_controlPoints[g_currentFrameNr] && g_controlPoints[g_currentFrameNr][0].control_points.length > 4) {
        let y0 = getControlPoint(-2, 0).y;
        let y1 = getControlPoint(-1, 0).y;
        let x0 = getControlPoint(-2, 0).x;
        let x1 = getControlPoint(-1, 0).x;
        g_context.beginPath();
        g_context.setLineDash([5, 5]); // dashes are 5px and spaces are 5px
        g_context.strokeStyle = colorToHexString(255, 255, 255);
        g_context.moveTo(x0, y0);
        g_context.lineTo(x1, y1);
        g_context.stroke();
        g_context.setLineDash([]); // Clear
    }

    // Draw LA annulus plane line
    if(0 in g_controlPoints[g_currentFrameNr] && g_controlPoints[g_currentFrameNr][0].control_points.length > 4) {
        let y0 = getControlPoint(0, 0).y;
        let y1 = getControlPoint(-1, 0).y;
        let x0 = getControlPoint(0, 0).x;
        let x1 = getControlPoint(-1, 0).x;
        g_context.beginPath();
        g_context.setLineDash([5, 5]); // dashes are 5px and spaces are 5px
        g_context.strokeStyle = colorToHexString(255, 255, 0);
        g_context.moveTo(x0, y0);
        g_context.lineTo(x1, y1);
        g_context.stroke();
        g_context.setLineDash([]); // Clear
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
    var index = g_currentFrameNr - g_startFrame;
    g_context.drawImage(g_sequence[index], 0, 0, g_canvasWidth, g_canvasHeight);
    redraw();

    // Draw motion mode line
    g_context.beginPath();
    g_context.setLineDash([]); // Clear
    g_context.lineWidth = 8;
    g_context.strokeStyle = colorToHexString(0, 255, 255);
    // Draw solid line where it can be moved
    g_context.moveTo(g_motionModeLine, 0);
    g_context.lineTo(g_motionModeLine, g_canvasHeight/10);
    g_context.stroke();
    g_context.lineWidth = 2;
    // Draw dashed line for the rest
    g_context.setLineDash([5, 5]); // dashes are 5px and spaces are 5px
    g_context.moveTo(g_motionModeLine, g_canvasHeight/10);
    g_context.lineTo(g_motionModeLine, g_canvasHeight);
    g_context.stroke();
    g_context.setLineDash([]); // Clear
}

// Override of annotationweb.js
function changeLabel(label_id) {
    g_currentSegmentationLabel = label_id;
    console.log('changing label to: ', label_id);
    $('.labelButton').removeClass('activeLabel');
    $('#labelButton' + label_id).addClass('activeLabel');
    g_currentLabel = getLabelIdxWithId(label_id);
    g_currentObject = g_currentLabel;
}

function sendDataForSave() {
    return $.ajax({
        type: "POST",
        url: "/cardiac-alax/segmentation/save/",
        data: {
            control_points: JSON.stringify(g_controlPoints),
            target_frames: JSON.stringify(g_targetFrames),
            target_frame_types: JSON.stringify(g_targetFrameTypes),
            motion_mode_line: g_motionModeLine,
            width: g_canvasWidth,
            height: g_canvasHeight,
            image_id: g_imageID,
            task_id: g_taskID,
            rejected: g_rejected ? 'true':'false',
            comments: $('#comments').val(),
            quality: $('input[name=quality]:checked').val(),
        },
        dataType: "json" // Need this do get result back as JSON
    });
}
